"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import logging
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page
import asyncio

from models import BrowserAction

logger = logging.getLogger(__name__)

class ChromeClient:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def connect(self):
        """Initialize browser and create a new page."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # Set to False for debugging
            )
        self.page = await self.browser.new_page()
        
    async def disconnect(self):
        """Close browser and cleanup resources."""
        if self.page:
            await self.page.close()
            self.page = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            
    async def navigate(self, url: str) -> bool:
        """Navigate to a URL."""
        try:
            if not self.page:
                raise ValueError("Browser not initialized")
            await self.page.goto(url)
            return True
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            return False
            
    async def execute_action(self, action: BrowserAction) -> Dict[str, Any]:
        """Execute a browser action."""
        if not self.page:
            return {"success": False, "error": "Browser not initialized"}
            
        try:
            result = {"success": True}
            
            if action.type == "click":
                element = await self._find_element(action.selector)
                await element.click()
                
            elif action.type == "type":
                element = await self._find_element(action.selector)
                await element.fill(action.value)
                
            elif action.type == "select":
                element = await self._find_element(action.selector)
                await element.select_option(value=action.value)
                
            elif action.type == "wait":
                await asyncio.sleep(float(action.value))
                
            elif action.type == "screenshot":
                screenshot = await self.page.screenshot()
                result["data"] = {"screenshot": screenshot}
                
            elif action.type == "extract":
                element = await self._find_element(action.selector)
                text = await element.text_content()
                result["data"] = {"text": text}
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action.type}"
                }
                
            return result
            
        except Exception as e:
            logger.error(f"Action execution error: {str(e)}")
            return {"success": False, "error": str(e)}
            
    async def _find_element(self, selector: str):
        """Find an element using various selector strategies."""
        try:
            # Try CSS selector first
            element = await self.page.wait_for_selector(selector)
            if element:
                return element
                
            # Try XPath if CSS selector fails
            element = await self.page.wait_for_selector(f"xpath={selector}")
            if element:
                return element
                
            raise ValueError(f"Element not found: {selector}")
            
        except Exception as e:
            raise ValueError(f"Error finding element: {str(e)}")
            
    async def get_tab_info(self) -> Dict[str, str]:
        """Get information about the current tab."""
        if not self.page:
            return {
                "url": "",
                "title": "",
                "status": "disconnected"
            }
            
        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "status": "connected"
        }
