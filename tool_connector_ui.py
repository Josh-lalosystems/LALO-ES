# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All‑Rights‑Reserved

"""
Module: UiToolConnector

Purpose:
 - Automates SAP GUI or Fiori interfaces when direct API access isn't available.
 - Uses RPA techniques or GUI scripting engines (e.g. SAP GUI scripting or Selenium).
 - Wraps functionality with consistent interface to ApiToolConnector.

Dependencies:
 - pywin32 and SAP GUI scripting engine (Windows).
 - RPA Framework’s SapGuiLibrary or Selenium for Fiori UI automation.
 - Hands-off automation flow recording.

Edge Cases:
 - SAP theme changes break locators.
 - Multi-window sessions: ensure correct session selected.
 - Wait-for-element logic required for reliability.
"""

import time
import msal
import requests
import webbrowser

class UiToolConnector:
    def __init__(self, client_id, tenant_id):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.scopes = ["Files.Read"]  # or Files.ReadWrite for more access
        self.access_token = None

    def authenticate(self):
        app = msal.PublicClientApplication(self.client_id, authority=f"https://login.microsoftonline.com/{self.tenant_id}")
        flow = app.initiate_device_flow(scopes=self.scopes)
        if "user_code" not in flow:
            raise RuntimeError("Failed to create device flow")
        import logging
        logger = logging.getLogger('tool_connector_ui')
        logger.info("Go to %s and enter code: %s", flow['verification_uri'], flow['user_code'])
        # Open the browser automatically
        webbrowser.open(flow['verification_uri'])
        result = app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            self.access_token = result["access_token"]
        else:
            raise RuntimeError(f"Authentication failed: {result.get('error_description')}")

    def execute(self, tool_name: str, input_data: dict):
        if not self.access_token:
            self.authenticate()
        if tool_name == "list_onedrive_files":
            url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                files = [item["name"] for item in resp.json().get("value", [])]
                result_summary = {"status": "success", "files": files}
            else:
                result_summary = {"status": "error", "details": resp.text}
        else:
            result_summary = {"status": "error", "details": "Unknown tool_name"}
        return type("Result", (), {"summary": result_summary, "hallucinatory": False})
