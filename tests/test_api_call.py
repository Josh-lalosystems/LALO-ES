"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import asyncio
from core.tools.api_call import api_call_tool

# Use a known public HTTP test service

def test_get_example():
    res = asyncio.run(api_call_tool.execute_with_validation(method="GET", url="https://httpbin.org/get", params={"q":"lalo"}))
    assert res.success
    assert res.output["status"] == 200
    assert res.output["json"]["args"]["q"] == "lalo"
