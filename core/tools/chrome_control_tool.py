"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
Chrome Browser Control Tool for LALO

Allows LALO to control the user's Chrome browser via MCP (Model Context Protocol).
Can navigate pages, click elements, fill forms, extract data, etc.
"""

from typing import Dict, Any, List, Optional
import asyncio
import json

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    import logging
    logger = logging.getLogger('core.tools.chrome_control_tool')
    logger.warning("selenium not installed. Install with: pip install selenium")

from .base_tool import BaseTool, ToolParameter

class ChromeControlTool(BaseTool):
    """Tool for controlling Chrome browser"""

    def __init__(self):
        super().__init__(
            name="chrome_browser_control",
            description="Control Chrome browser: navigate pages, click elements, fill forms, extract data, take screenshots",
            category="automation",
            required_permissions=["automation:browser", "web:access"]
        )

        self.driver: Optional[Any] = None
        self.parameters = [
            ToolParameter(
                name="action",
                type="string",
                description="Browser action to perform",
                required=True,
                enum=[
                    "navigate", "click", "type", "extract_text", "extract_links",
                    "fill_form", "submit_form", "screenshot", "execute_script",
                    "get_title", "get_url", "go_back", "go_forward", "refresh",
                    "close", "switch_tab", "new_tab"
                ]
            ),
            ToolParameter(
                name="url",
                type="string",
                description="URL to navigate to (for 'navigate' action)",
                required=False
            ),
            ToolParameter(
                name="selector",
                type="string",
                description="CSS selector for element (for 'click', 'type', 'extract_text' actions)",
                required=False
            ),
            ToolParameter(
                name="text",
                type="string",
                description="Text to type (for 'type' action)",
                required=False
            ),
            ToolParameter(
                name="script",
                type="string",
                description="JavaScript to execute (for 'execute_script' action)",
                required=False
            ),
            ToolParameter(
                name="form_data",
                type="object",
                description="Form data as key-value pairs (for 'fill_form' action)",
                required=False
            ),
            ToolParameter(
                name="wait_seconds",
                type="number",
                description="Seconds to wait for element",
                required=False,
                default=10
            ),
        ]

    def _ensure_driver(self):
        """Ensure Chrome driver is initialized"""
        if self.driver is None and SELENIUM_AVAILABLE:
            options = Options()
            # Connect to existing Chrome instance if possible
            # Otherwise start new instance
            try:
                # Try to connect to existing Chrome with remote debugging
                options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
                self.driver = webdriver.Chrome(options=options)
            except:
                # Start new Chrome instance
                options.add_argument("--start-maximized")
                self.driver = webdriver.Chrome(options=options)

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute browser control action"""
        if not SELENIUM_AVAILABLE:
            return {
                "success": False,
                "error": "Selenium library not installed. Install with: pip install selenium"
            }

        action = parameters.get("action")

        try:
            self._ensure_driver()

            if action == "navigate":
                url = parameters.get("url")
                if not url:
                    return {"success": False, "error": "url parameter required"}

                self.driver.get(url)
                return {
                    "success": True,
                    "action": "navigate",
                    "url": url,
                    "title": self.driver.title
                }

            elif action == "click":
                selector = parameters.get("selector")
                if not selector:
                    return {"success": False, "error": "selector parameter required"}

                wait_seconds = parameters.get("wait_seconds", 10)
                element = WebDriverWait(self.driver, wait_seconds).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                element.click()

                return {
                    "success": True,
                    "action": "click",
                    "selector": selector
                }

            elif action == "type":
                selector = parameters.get("selector")
                text = parameters.get("text", "")

                if not selector:
                    return {"success": False, "error": "selector parameter required"}

                wait_seconds = parameters.get("wait_seconds", 10)
                element = WebDriverWait(self.driver, wait_seconds).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                element.clear()
                element.send_keys(text)

                return {
                    "success": True,
                    "action": "type",
                    "selector": selector,
                    "text_length": len(text)
                }

            elif action == "extract_text":
                selector = parameters.get("selector", "body")
                wait_seconds = parameters.get("wait_seconds", 10)

                element = WebDriverWait(self.driver, wait_seconds).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                text = element.text

                return {
                    "success": True,
                    "action": "extract_text",
                    "selector": selector,
                    "text": text
                }

            elif action == "extract_links":
                links = self.driver.find_elements(By.TAG_NAME, "a")
                link_data = [
                    {"text": link.text, "href": link.get_attribute("href")}
                    for link in links if link.get_attribute("href")
                ]

                return {
                    "success": True,
                    "action": "extract_links",
                    "count": len(link_data),
                    "links": link_data[:50]  # Limit to 50
                }

            elif action == "fill_form":
                form_data = parameters.get("form_data", {})

                for selector, value in form_data.items():
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    element.clear()
                    element.send_keys(value)

                return {
                    "success": True,
                    "action": "fill_form",
                    "fields_filled": len(form_data)
                }

            elif action == "submit_form":
                selector = parameters.get("selector", "form")
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                element.submit()

                return {
                    "success": True,
                    "action": "submit_form",
                    "selector": selector
                }

            elif action == "screenshot":
                import tempfile
                import os
                temp_path = os.path.join(tempfile.gettempdir(), f"lalo_browser_screenshot_{int(asyncio.get_event_loop().time())}.png")
                self.driver.save_screenshot(temp_path)

                return {
                    "success": True,
                    "action": "screenshot",
                    "path": temp_path
                }

            elif action == "execute_script":
                script = parameters.get("script")
                if not script:
                    return {"success": False, "error": "script parameter required"}

                result = self.driver.execute_script(script)

                return {
                    "success": True,
                    "action": "execute_script",
                    "result": result
                }

            elif action == "get_title":
                return {
                    "success": True,
                    "action": "get_title",
                    "title": self.driver.title
                }

            elif action == "get_url":
                return {
                    "success": True,
                    "action": "get_url",
                    "url": self.driver.current_url
                }

            elif action == "go_back":
                self.driver.back()
                return {"success": True, "action": "go_back"}

            elif action == "go_forward":
                self.driver.forward()
                return {"success": True, "action": "go_forward"}

            elif action == "refresh":
                self.driver.refresh()
                return {"success": True, "action": "refresh"}

            elif action == "close":
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                return {"success": True, "action": "close"}

            elif action == "new_tab":
                self.driver.execute_script("window.open('about:blank', '_blank');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                return {
                    "success": True,
                    "action": "new_tab",
                    "tab_count": len(self.driver.window_handles)
                }

            elif action == "switch_tab":
                tab_index = parameters.get("tab_index", 0)
                if tab_index < len(self.driver.window_handles):
                    self.driver.switch_to.window(self.driver.window_handles[tab_index])
                    return {
                        "success": True,
                        "action": "switch_tab",
                        "tab_index": tab_index
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Tab index {tab_index} out of range"
                    }

            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Browser control failed: {str(e)}"
            }

    def __del__(self):
        """Cleanup driver on deletion"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
