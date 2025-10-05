"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
Keyboard and Mouse Automation Tool for LALO

Allows LALO to control the user's keyboard and mouse for automation tasks.
Uses pyautogui for cross-platform automation.
"""

from typing import Dict, Any, List, Optional
import time

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    import logging
    logger = logging.getLogger('core.tools.automation_tool')
    logger.warning("pyautogui not installed. Install with: pip install pyautogui")

from .base_tool import BaseTool, ToolParameter

class KeyboardMouseTool(BaseTool):
    """Tool for automating keyboard and mouse actions"""

    def __init__(self):
        super().__init__(
            name="keyboard_mouse_automation",
            description="Control keyboard and mouse to automate user actions. Can type text, click, move mouse, press keys, etc.",
            category="automation",
            required_permissions=["automation:keyboard", "automation:mouse"]
        )

        self.parameters = [
            ToolParameter(
                name="action",
                type="string",
                description="Action to perform",
                required=True,
                enum=["type", "click", "move", "press_key", "hotkey", "screenshot", "get_position"]
            ),
            ToolParameter(
                name="text",
                type="string",
                description="Text to type (for 'type' action)",
                required=False
            ),
            ToolParameter(
                name="x",
                type="integer",
                description="X coordinate (for 'click' or 'move' actions)",
                required=False
            ),
            ToolParameter(
                name="y",
                type="integer",
                description="Y coordinate (for 'click' or 'move' actions)",
                required=False
            ),
            ToolParameter(
                name="key",
                type="string",
                description="Key to press (for 'press_key' action)",
                required=False
            ),
            ToolParameter(
                name="keys",
                type="array",
                description="Keys for hotkey combination (e.g., ['ctrl', 'c'])",
                required=False
            ),
            ToolParameter(
                name="clicks",
                type="integer",
                description="Number of clicks (default: 1)",
                required=False,
                default=1
            ),
            ToolParameter(
                name="button",
                type="string",
                description="Mouse button",
                required=False,
                default="left",
                enum=["left", "right", "middle"]
            ),
            ToolParameter(
                name="interval",
                type="number",
                description="Interval between actions in seconds",
                required=False,
                default=0.0
            ),
        ]

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute keyboard/mouse automation action"""
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "error": "pyautogui library not installed. Install with: pip install pyautogui"
            }

        action = parameters.get("action")

        try:
            if action == "type":
                text = parameters.get("text", "")
                interval = parameters.get("interval", 0.0)
                pyautogui.write(text, interval=interval)
                return {
                    "success": True,
                    "action": "type",
                    "text_length": len(text)
                }

            elif action == "click":
                x = parameters.get("x")
                y = parameters.get("y")
                clicks = parameters.get("clicks", 1)
                button = parameters.get("button", "left")

                if x is not None and y is not None:
                    pyautogui.click(x, y, clicks=clicks, button=button)
                else:
                    pyautogui.click(clicks=clicks, button=button)

                return {
                    "success": True,
                    "action": "click",
                    "position": (x, y) if x and y else None,
                    "clicks": clicks,
                    "button": button
                }

            elif action == "move":
                x = parameters.get("x")
                y = parameters.get("y")

                if x is None or y is None:
                    return {
                        "success": False,
                        "error": "x and y coordinates required for move action"
                    }

                pyautogui.moveTo(x, y)
                return {
                    "success": True,
                    "action": "move",
                    "position": (x, y)
                }

            elif action == "press_key":
                key = parameters.get("key")

                if not key:
                    return {
                        "success": False,
                        "error": "key parameter required for press_key action"
                    }

                pyautogui.press(key)
                return {
                    "success": True,
                    "action": "press_key",
                    "key": key
                }

            elif action == "hotkey":
                keys = parameters.get("keys", [])

                if not keys or not isinstance(keys, list):
                    return {
                        "success": False,
                        "error": "keys array required for hotkey action (e.g., ['ctrl', 'c'])"
                    }

                pyautogui.hotkey(*keys)
                return {
                    "success": True,
                    "action": "hotkey",
                    "keys": keys
                }

            elif action == "screenshot":
                screenshot = pyautogui.screenshot()
                # Save to temp file
                import tempfile
                import os
                temp_path = os.path.join(tempfile.gettempdir(), f"lalo_screenshot_{int(time.time())}.png")
                screenshot.save(temp_path)

                return {
                    "success": True,
                    "action": "screenshot",
                    "path": temp_path,
                    "size": screenshot.size
                }

            elif action == "get_position":
                position = pyautogui.position()
                return {
                    "success": True,
                    "action": "get_position",
                    "position": (position.x, position.y)
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Automation failed: {str(e)}"
            }

    def _validate_safety(self, parameters: Dict[str, Any]) -> bool:
        """Validate that automation is safe to execute"""
        # Add safety checks here
        # For example, prevent destructive hotkeys, screen bounds, etc.
        return True
