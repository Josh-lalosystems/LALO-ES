import asyncio
from core.tools.api_call import api_call_tool

# Use a known public HTTP test service

def test_get_example():
    res = asyncio.run(api_call_tool.execute_with_validation(method="GET", url="https://httpbin.org/get", params={"q":"lalo"}))
    assert res.success
    assert res.output["status"] == 200
    assert res.output["json"]["args"]["q"] == "lalo"
