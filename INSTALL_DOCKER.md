INSTALL_DOCKER.md

**Filename to save as:** `INSTALL_DOCKER.md` — copy everything below into Notepad and save.

````
# Copyright (c) 2025 LALO AI LLC. All rights reserved.

# INSTALL_DOCKER.md
## LALO Demo — Docker Compose Install & Run

This file explains how to run the LALO demo scaffold using Docker Compose. Running with Docker isolates dependencies and provides a quicker way to get a multi-service demo up and running.

---

## Prerequisites
- **Docker** (engine) installed and running.
- **Docker Compose** (v2+) — bundled with modern Docker Desktop.
- A machine with enough free disk space (~3–10 GB) to download images and Python dependencies.
- (Optional) For GPU acceleration of model workloads: Docker with NVIDIA Container Toolkit and a compatible GPU.

---

## Quick summary (one-line)
1. Update `.env` if needed → 2. `docker compose up --build` → 3. Open `http://localhost:8000`

---

## Step A — Prepare project
1. Place the repository contents on your machine.
2. Copy `.env.example` to `.env` and make any endpoint changes required:
   ```bash
   cp .env.example .env        # macOS / Linux
   copy .env.example .env      # Windows cmd
````

3. Ensure `docker-compose.yml` exists in the project root and ports are free.

---

## Step B — Build and run

From the project root:

```bash
docker compose up --build
```

* The `--build` flag forces image rebuilds on first run or if files changed.
* The compose file will spin up the following containers (example):

  * `core` (port 8000)
  * `rtinterpreter` (port 8101)
  * `mcp` (port 8102)
  * `creation` (port 8103)
  * `mock-s4` (port 8201)
  * `mock-workday` (port 8202)
  * `mock-sharepoint` (port 8203)

During the build step you will see pip installing Python dependencies into images — this may take several minutes on first run.

---

## Step C — Verify and access UI

Once the compose output shows services healthy (or listening), open:

```
http://localhost:8000
```

This is the Core UI. Use it to run the demo flow: Interpret → Approve → Plan → Approve → Execute.

---

## Useful Docker Compose commands

* Run in detached/background mode:

  ```bash
  docker compose up --build -d
  ```
* See logs for a specific service:

  ```bash
  docker compose logs -f core
  ```
* Rebuild a single service:

  ```bash
  docker compose build mcp
  ```
* Stop and remove containers:

  ```bash
  docker compose down
  ```
* Remove images and volumes (careful — will clear build cache):

  ```bash
  docker compose down --rmi all --volumes
  ```

---

## Environment variables in Docker

* `docker compose` will automatically pass environment variables defined in a `.env` file in the compose directory to the services (as configured in the `docker-compose.yml`).
* Edit `.env` to point connectors at real endpoints if you have them (e.g., S/4HANA trial). Do **not** commit secrets to source control.

---

## Notes on persistent data & logs

* The demo uses light SQLite and local pickle files for vector store by default inside the container filesystem. If you want persistence across container restarts, bind mount a host directory via volumes in `docker-compose.yml`.
* Example `docker-compose.yml` volume snippet (project root):

  ```yaml
  services:
    mcp:
      volumes:
        - ./data/mcp:/data
  ```

---

## Troubleshooting

* **Port conflict**: change service port in `docker-compose.yml` or stop the process using the port.
* **Build fails due to pip install**: ensure the Docker base image has required build tools or prebuild wheels. Re-run `docker compose build` to see detailed error logs.
* **Performance**: local models running inside containers on CPU will be slow. Use cloud/VPC with GPUs for live demos with larger models.

---

## Next steps & enhancements

* Add named Docker volumes for persistent database/files across runs.
* Provide a separate compose override for VPC/cloud deployment (env-specific scaling).
* Add healthchecks to each service and restart policies for reliability.

---

## End of file

