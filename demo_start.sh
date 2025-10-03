#!/usr/bin/env bash
# Copyright (c) 2025 LALO AI LLC. All rights reserved.

# Convenience script to start all demo services in background (Unix/macOS/Linux).
# NOTE: for development it's better to run uvicorn per-service in separate terminals.
# Make executable: chmod +x demo_start.sh

echo "Starting LALO demo services..."
uvicorn rtinterpreter.main:app --port 8101 --reload &
RTI_PID=$!
sleep 0.5

uvicorn mcp.main:app --port 8102 --reload &
MCP_PID=$!
sleep 0.5

uvicorn creation.main:app --port 8103 --reload &
CPS_PID=$!
sleep 0.5

uvicorn connectors.mock_s4.mock_s4:app --port 8201 --reload &
S4_PID=$!
sleep 0.5

uvicorn connectors.mock_workday.mock_workday:app --port 8202 --reload &
WORK_PID=$!
sleep 0.5

uvicorn connectors.mock_sharepoint.mock_sharepoint:app --port 8203 --reload &
SP_PID=$!
sleep 0.5

uvicorn core.main:app --port 8000 --reload &
CORE_PID=$!
sleep 0.5

echo "Services started."
echo "Core UI: http://localhost:8000"
echo "To stop services, run: kill $RTI_PID $MCP_PID $CPS_PID $S4_PID $WORK_PID $SP_PID $CORE_PID"
