# Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of LALO AI Platform and is protected by copyright law.
# Unauthorized copying, modification, distribution, or use of this software,
# via any medium, is strictly prohibited without the express written permission
# of LALO AI SYSTEMS, LLC.
#

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
