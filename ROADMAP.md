# Copyright (c) 2025 LALO AI LLC. All rights reserved.

# LALO Demo Roadmap (Engineering-ready Summary)

## Objective
Deliver a runnable LALO MVP demo that showcases the full multi-step alignment workflow:
- RTI (Recursive Task Interpreter) → MCP (Action Planner) → CPS (Creation Server) → Execution
- Live connectors (S/4HANA, Workday, SharePoint/AWS/local share) and RPA fallback
- Human-in-the-loop approvals, confidence gating, and vector-memory retrieval

## Phased Plan

### Phase 0 — Prep & Access
- Acquire S/4HANA and Workday trial sandboxes.
- Prepare Azure AD test tenant for SSO demonstration.
- Identify SharePoint / S3 sample data and local share folders for templates.

### Phase 1 — Core Demo Scaffold (this repo)
- FastAPI microservices:
  - RTI, MCP, CPS, Core UI
  - Mock connectors for S4, Workday, SharePoint
- Lightweight vector store (TF-IDF / sklearn) for template retrieval
- Simple creation artifact generator (CPS) with sandbox hooks
- Mock SSO UX and documentation

### Phase 2 — Connectors & Verification
- Build real REST/OData connector for S/4HANA (OData query examples)
- Build Workday SOAP/OAuth connector or use integration layer (Apideck/Merge)
- Add SharePoint (Microsoft Graph) and S3 connectors
- Add Playwright templates for RPA UI automation of legacy systems

### Phase 3 — Model Integration & Reasoning
- Add plugin adapters for:
  - Local GPT-OSS (quantized, CPU-friendly variants)
  - Sapient HRM (Hierarchical Reasoning Model)
  - External APIs (OpenAI, Anthropic) as optional providers
- Implement confidence scoring using embeddings + similarity checks

### Phase 4 — Security & Production Readiness
- Implement Azure AD SSO flow and role-based access control
- Harden CPS sandbox (containerized test runners)
- Add immutable audit logs + vector DB persistence (FAISS/Chroma/Weaviate)
- Add CI/CD pipelines and Docker Compose / Helm charts for cloud

### Phase 5 — Performance & Multi-environment Demos
- Demo same workflow on:
  - Local mid-tier laptop (16GB, CPU-only)
  - VPC with GPU-backed instances (low-latency, higher throughput)
- Measure latency/throughput & produce comparison artifacts for investors

## Deliverables
- Working demo scaffold with docs and scripts
- Step-by-step demo operator guide
- Connector templates and RPA scripts
- Model plugin documentation and sample configs

## Notes
- The roadmap is intentionally modular: connectors, alignment logic, and model plugins are interchangeable.
- For enterprise demos, always run in a secured VPC and avoid sending sensitive PII to external model APIs.
