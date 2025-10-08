# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
Database Query Tool (read-only)

Supports safe SQL SELECT queries against configured databases.
- Prevents write/DDL by rejecting non-SELECT statements
- Enforces timeout and row limits
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel
import sqlalchemy as sa
import os

from core.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolExecutionResult

DEFAULT_URL = os.getenv("DB_TOOL_URL", "sqlite:///./lalo.db")
ROW_LIMIT = int(os.getenv("DB_TOOL_ROW_LIMIT", "500"))
TIMEOUT = int(os.getenv("DB_TOOL_TIMEOUT", "10"))

engine = sa.create_engine(DEFAULT_URL, pool_pre_ping=True)


def _is_select(sql: str) -> bool:
    s = sql.strip().lower()
    # basic: allow only statements starting with select or with 'with' CTE then select
    return s.startswith("select ") or s.startswith("with ")


class DatabaseQueryTool(BaseTool):
    def __init__(self):
        super().__init__()

    @property
    def tool_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="database_query",
            description="Execute safe, read-only SQL queries against configured database",
            category="database",
            parameters=[
                ToolParameter(name="sql", type="string", description="SELECT query to execute", required=True),
            ],
            returns={"rows": "List of rows (dicts)", "row_count": "Number of returned rows (capped)"},
            requires_approval=False,
        )

    async def execute(self, **kwargs) -> ToolExecutionResult:
        sql = kwargs.get("sql", "")
        if not _is_select(sql):
            return ToolExecutionResult(success=False, error="Only SELECT queries are allowed")

        try:
            with engine.connect() as conn:
                result = conn.execution_options(stream_results=True, timeout=TIMEOUT).execute(sa.text(sql))
                columns = result.keys()
                rows = []
                for i, row in enumerate(result):
                    if i >= ROW_LIMIT:
                        break
                    rows.append(dict(zip(columns, row)))
                return ToolExecutionResult(success=True, output={"rows": rows, "row_count": len(rows)})
        except Exception as e:
            return ToolExecutionResult(success=False, error=str(e))


# Singleton instance for registry
database_query_tool = DatabaseQueryTool()
