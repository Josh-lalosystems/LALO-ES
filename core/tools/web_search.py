"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Web Search Tool

Provides web search capabilities using multiple providers:
- Tavily (recommended for AI applications)
- SerpAPI (Google Search)
- DuckDuckGo (fallback, no API key required)
"""

import os
import httpx
from typing import Dict, List, Optional
from datetime import datetime

from .base import BaseTool, ToolDefinition, ToolParameter, ToolExecutionResult


class WebSearchTool(BaseTool):
    """Web search tool with multiple provider support"""

    def __init__(self):
        self._provider = os.getenv("SEARCH_PROVIDER", "duckduckgo").lower()
        self._tavily_key = os.getenv("TAVILY_API_KEY")
        self._serpapi_key = os.getenv("SERPAPI_API_KEY")

        # Auto-detect best provider based on available keys
        if not self._provider or self._provider == "auto":
            if self._tavily_key:
                self._provider = "tavily"
            elif self._serpapi_key:
                self._provider = "serpapi"
            else:
                self._provider = "duckduckgo"

    @property
    def tool_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="web_search",
            description="Search the web for information on any topic. Returns a list of relevant results with titles, URLs, and snippets.",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="The search query to execute",
                    required=True
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="Maximum number of results to return (default: 5, max: 20)",
                    required=False
                ),
                ToolParameter(
                    name="search_depth",
                    type="string",
                    description="Search depth: 'basic' for quick results or 'advanced' for comprehensive search (Tavily only)",
                    required=False,
                    enum=["basic", "advanced"]
                ),
                ToolParameter(
                    name="include_domains",
                    type="array",
                    description="List of domains to include in search (optional filter)",
                    required=False
                ),
                ToolParameter(
                    name="exclude_domains",
                    type="array",
                    description="List of domains to exclude from search (optional filter)",
                    required=False
                )
            ],
            returns={
                "type": "object",
                "description": "Search results with query, provider, and list of results"
            }
        )

    async def execute(self, **kwargs) -> ToolExecutionResult:
        """Execute web search using configured provider"""
        query = kwargs.get("query")
        max_results = min(kwargs.get("max_results", 5), 20)
        search_depth = kwargs.get("search_depth", "basic")
        include_domains = kwargs.get("include_domains", [])
        exclude_domains = kwargs.get("exclude_domains", [])

        try:
            if self._provider == "tavily":
                results = await self._search_tavily(
                    query, max_results, search_depth, include_domains, exclude_domains
                )
            elif self._provider == "serpapi":
                results = await self._search_serpapi(
                    query, max_results, include_domains, exclude_domains
                )
            else:  # duckduckgo
                results = await self._search_duckduckgo(
                    query, max_results, include_domains, exclude_domains
                )

            return ToolExecutionResult(
                success=True,
                output={
                    "query": query,
                    "provider": self._provider,
                    "results": results,
                    "count": len(results),
                    "timestamp": datetime.utcnow().isoformat()
                },
                metadata={
                    "provider": self._provider,
                    "max_results": max_results
                }
            )

        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f"Search failed: {str(e)}",
                output={
                    "query": query,
                    "provider": self._provider,
                    "results": [],
                    "count": 0
                }
            )

    async def _search_tavily(
        self,
        query: str,
        max_results: int,
        search_depth: str,
        include_domains: List[str],
        exclude_domains: List[str]
    ) -> List[Dict]:
        """Search using Tavily API (best for AI applications)"""
        if not self._tavily_key:
            raise ValueError("TAVILY_API_KEY not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self._tavily_key,
                    "query": query,
                    "search_depth": search_depth,
                    "max_results": max_results,
                    "include_domains": include_domains if include_domains else None,
                    "exclude_domains": exclude_domains if exclude_domains else None,
                    "include_answer": True,
                    "include_raw_content": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        # Transform Tavily results to standard format
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
                "score": item.get("score", 0.0),
                "published_date": item.get("published_date")
            })

        return results

    async def _search_serpapi(
        self,
        query: str,
        max_results: int,
        include_domains: List[str],
        exclude_domains: List[str]
    ) -> List[Dict]:
        """Search using SerpAPI (Google Search)"""
        if not self._serpapi_key:
            raise ValueError("SERPAPI_API_KEY not configured")

        # Build domain filters for Google
        domain_query = query
        if include_domains:
            domain_filters = " OR ".join([f"site:{domain}" for domain in include_domains])
            domain_query = f"{query} ({domain_filters})"
        if exclude_domains:
            for domain in exclude_domains:
                domain_query += f" -site:{domain}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://serpapi.com/search",
                params={
                    "api_key": self._serpapi_key,
                    "q": domain_query,
                    "num": max_results,
                    "engine": "google"
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        # Transform SerpAPI results to standard format
        results = []
        for item in data.get("organic_results", [])[:max_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "score": item.get("position", 999) * -1.0,  # Convert position to score
                "published_date": item.get("date")
            })

        return results

    async def _search_duckduckgo(
        self,
        query: str,
        max_results: int,
        include_domains: List[str],
        exclude_domains: List[str]
    ) -> List[Dict]:
        """Search using DuckDuckGo (free, no API key required)"""
        try:
            from duckduckgo_search import AsyncDDGS
        except ImportError:
            raise ValueError(
                "duckduckgo-search package not installed. "
                "Run: pip install duckduckgo-search"
            )

        # Apply domain filters to query
        domain_query = query
        if include_domains:
            domain_filters = " OR ".join([f"site:{domain}" for domain in include_domains])
            domain_query = f"{query} ({domain_filters})"
        if exclude_domains:
            for domain in exclude_domains:
                domain_query += f" -site:{domain}"

        # Search with DuckDuckGo
        async with AsyncDDGS() as ddgs:
            search_results = []
            async for result in ddgs.text(domain_query, max_results=max_results):
                search_results.append(result)

        # Transform DuckDuckGo results to standard format
        results = []
        for i, item in enumerate(search_results):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", ""),
                "score": (max_results - i) / max_results,  # Descending score based on position
                "published_date": None
            })

        return results

    def is_enabled(self) -> bool:
        """Tool is enabled if any provider is configured"""
        # DuckDuckGo is always available (no API key needed)
        return True


# Create singleton instance
web_search_tool = WebSearchTool()
