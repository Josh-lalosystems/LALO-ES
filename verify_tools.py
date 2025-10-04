#!/usr/bin/env python3
"""
Verification script for LALO AI Tools
Tests that all tools are properly registered and accessible
"""

import sys
from core.tools import tool_registry

def main():
    print("=" * 60)
    print("LALO AI Tools Verification")
    print("=" * 60)

    # List all registered tools
    all_tools = tool_registry.get_all_tools()
    tool_names = list(all_tools.keys())
    print(f"\nRegistered Tools ({len(tool_names)}):")
    print("-" * 60)

    for tool_name in tool_names:
        print(f"\n✓ {tool_name}")

        # Get tool instance
        tool = tool_registry.get_tool(tool_name)
        if tool:
            definition = tool.tool_definition
            print(f"  Description: {definition.description[:100]}...")
            print(f"  Parameters: {len(definition.parameters)}")
            print(f"  Enabled: {tool.is_enabled()}")
        else:
            print(f"  ✗ ERROR: Tool not found in registry")

    print("\n" + "=" * 60)

    # Get tool schemas (for LLM integration)
    print("\nTool Schemas (for LLM function calling):")
    print("-" * 60)

    for tool_name in tool_names:
        schema = tool_registry.get_tool_schema(tool_name)
        if schema:
            print(f"\n✓ {tool_name}")
            print(f"  Schema type: {schema.get('type', 'N/A')}")
            print(f"  Required params: {schema.get('required', [])}")
        else:
            print(f"\n✗ {tool_name} - No schema available")

    print("\n" + "=" * 60)
    print("Verification Complete!")
    print("=" * 60)

    # Summary
    expected_tools = ["web_search", "rag_query", "image_generator", "code_executor"]
    missing = [t for t in expected_tools if t not in tool_names]

    if missing:
        print(f"\n⚠ WARNING: Missing tools: {missing}")
        return 1
    else:
        print(f"\n✓ All expected tools are registered and ready!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
