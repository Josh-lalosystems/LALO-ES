# Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of LALO AI Platform and is protected by copyright law.
# Unauthorized copying, modification, distribution, or use of this software,
# via any medium, is strictly prohibited without the express written permission
# of LALO AI SYSTEMS, LLC.
#

# API Documentation

## Connector Endpoints
- `POST /api/connectors` — Add connector
- `GET /api/connectors` — List connectors
- `GET /api/connectors/{name}` — Get connector
- `PUT /api/connectors/{name}` — Update connector
- `DELETE /api/connectors/{name}` — Remove connector
- `POST /api/connectors/{name}/test` — Test connection
- `POST /api/connectors/{name}/sync` — Trigger sync

## Feedback Endpoints
- `POST /api/feedback` — Add feedback
- `GET /api/feedback` — List feedback

## Learning Endpoints
- (Planned) `/api/learning/*`
