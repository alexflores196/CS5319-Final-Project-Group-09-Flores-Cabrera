## Selected Architecture: Layered Monolith Platform and Setup

### Implementation platform

The selected implementation is a Python FastAPI application. It was tested locally with **Python 3.15.0**. The Docker image uses `python:3.12-slim`; the database uses the PostgreSQL `16-alpine` image. The development environment used **Docker 29.9.3** and **Docker Compose 5.7.0**.

- **Python:** Download from [python.org/downloads](https://www.python.org/downloads/). Install Python for macOS and verify it with `python3 --version`.
- **Docker and Docker Compose:** Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/), install it, and start Docker Desktop. Docker Compose is included. Verify the installation with `docker --version` and `docker compose version`.
- **PostgreSQL:** No separate local installation is needed. Compose downloads and runs the `postgres:16-alpine` image.

### Install dependencies and run tests locally

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r Selected/requirements.txt
cd Selected
python -m pytest -q
```

### Build and run the system

From the repository root, build the Docker image and start the API and database:

```bash
docker compose -f Selected/docker-compose.yaml up --build -d
docker compose -f Selected/docker-compose.yaml ps
```

On the first run, PostgreSQL initializes its schema using the SQL files in `Selected/migrations/`. After the containers start, seed the demo users and products **once**:

```bash
docker compose -f Selected/docker-compose.yaml exec api python seed.py
```

The storefront is at <http://localhost:8080>, the API documentation is at <http://localhost:8080/docs>, and the health check is at <http://localhost:8080/health>.

Stop the services while preserving database data with:

```bash
docker compose -f Selected/docker-compose.yaml down
```

To also delete the database volume and its data, use `docker compose -f Selected/docker-compose.yaml down -v`.
