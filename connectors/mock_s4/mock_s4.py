# Copyright (c) 2025 LALO AI LLC. All rights reserved.

from fastapi import FastAPI
import time

app = FastAPI(title="Mock S4/HANA Connector")

@app.get("/production_report")
async def production_report(year: int, quarter: int):
    """
    Simulates fetching a production report for a given year/quarter.
    """
    time.sleep(0.5)
    return {
        "system": "S4/HANA",
        "year": year,
        "quarter": quarter,
        "data": [
            {"product": "High Margin Shoe A", "units": 1200, "margin": 0.45},
            {"product": "High Margin Shoe B", "units": 950, "margin": 0.48}
        ]
    }
