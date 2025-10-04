import asyncio
from core.tools.database_query import database_query_tool

# basic smoke test against default sqlite file lalo.db which should exist

def test_select_smoke():
    res = asyncio.run(database_query_tool.execute_with_validation(sql="SELECT 1 as x"))
    assert res.success
    assert res.output["rows"][0]["x"] == 1

# reject non-select

def test_reject_update():
    res = asyncio.run(database_query_tool.execute_with_validation(sql="UPDATE users SET x=1"))
    assert not res.success
    assert "Only SELECT" in res.error
