# Copyright (c) 2025 LALO AI LLC. All rights reserved.

from fastapi import FastAPI
import time

app = FastAPI(title="Mock Workday Connector")

@app.get("/employee_list")
async def employee_list(department: str = "All"):
    """
    Simulates fetching employee data from Workday.
    """
    time.sleep(0.5)
    employees = [
        {"name": "Alice Johnson", "department": "Production", "role": "Supervisor"},
        {"name": "Bob Smith", "department": "Marketing", "role": "Analyst"}
    ]
    if department != "All":
        employees = [e for e in employees if e["department"] == department]
    return {"system": "Workday", "department": department, "employees": employees}
