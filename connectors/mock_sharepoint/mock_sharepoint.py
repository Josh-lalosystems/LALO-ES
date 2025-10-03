# Copyright (c) 2025 LALO AI LLC. All rights reserved.

from fastapi import FastAPI
import time

app = FastAPI(title="Mock SharePoint Connector")

@app.get("/fetch_document")
async def fetch_document(folder: str, filename: str):
    """
    Simulates retrieving a document from a SharePoint folder.
    """
    time.sleep(0.5)
    return {
        "system": "SharePoint",
        "folder": folder,
        "filename": filename,
        "content": f"Sample content of {filename} from {folder}."
    }
