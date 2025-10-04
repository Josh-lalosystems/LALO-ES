# Deployment Guide

## Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (optional)

## Steps
1. Install Python dependencies: `pip install -r requirements.txt`
2. Install frontend dependencies: `cd lalo-frontend && npm install`
3. Run backend: `python -m uvicorn app:app --port 8000`
4. Run frontend: `npm start`
5. (Optional) Use Docker Compose: `docker-compose up`
