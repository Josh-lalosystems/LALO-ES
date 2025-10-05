"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""Async Playwright helper for simple frontend checks used by MCP.

Contract:
 - Input: url (str), wait_selector (str), timeout (int seconds), screenshot (bool)
 - Output: dict { ok: bool, status: str, title?: str, screenshot?: bytes, details?: str }
"""
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeout


async def check_frontend(url: str, wait_selector: str = "body", timeout: int = 10, screenshot: bool = False):
    """Navigate to the `url`, wait for `wait_selector` and optionally return a screenshot.

    Returns a dict with keys: ok (bool), status (str), title (opt), screenshot (bytes opt), details (opt)
    """
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=timeout * 1000)
            title = await page.title()
            shot = None
            if screenshot:
                shot = await page.screenshot(type="png")
            await browser.close()
            return {"ok": True, "status": "loaded", "title": title, "screenshot": shot}
    except PWTimeout as e:
        return {"ok": False, "status": "timeout", "details": str(e)}
    except Exception as e:
        return {"ok": False, "status": "error", "details": str(e)}
