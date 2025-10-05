#!/usr/bin/env python3
"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
Verification script for LALO AI Tools
Tests that all tools are properly registered and accessible
"""

import sys
import logging
from core.tools import tool_registry


def main():
    logger = logging.getLogger('verify_tools')
    logger.info('LALO AI Tools Verification')

    # List all registered tools
    all_tools = tool_registry.get_all_tools()
    tool_names = list(all_tools.keys())
    logger.info('Registered Tools (%s)', len(tool_names))

    for tool_name in tool_names:
        logger.info('✓ %s', tool_name)

        # Get tool instance
        tool = tool_registry.get_tool(tool_name)
        if tool:
            definition = tool.tool_definition
            logger.info('  Description: %s', definition.description[:100])
            logger.info('  Parameters: %s', len(definition.parameters))
            logger.info('  Enabled: %s', tool.is_enabled())
        else:
            logger.warning('  ✗ ERROR: Tool not found in registry')

    # Get tool schemas (for LLM integration)
    logger.info('Tool Schemas (for LLM function calling):')

    for tool_name in tool_names:
        schema = tool_registry.get_tool_schema(tool_name)
        if schema:
            logger.info('✓ %s', tool_name)
            logger.info('  Schema type: %s', schema.get('type', 'N/A'))
            logger.info('  Required params: %s', schema.get('required', []))
        else:
            logger.warning('✗ %s - No schema available', tool_name)

    logger.info('Verification Complete!')

    # Summary
    expected_tools = ["web_search", "rag_query", "image_generator", "code_executor"]
    missing = [t for t in expected_tools if t not in tool_names]

    if missing:
        logger.warning('Missing tools: %s', missing)
        return 1
    else:
        logger.info('All expected tools are registered and ready!')
        return 0


if __name__ == "__main__":
    sys.exit(main())
