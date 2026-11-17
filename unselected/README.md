## Unselected Architecture: Microservices

This is the same e-commerce system as `Selected`, split into four
independently deployable FastAPI services, each with its own PostgreSQL
database. The public API and the storefront are unchanged.

See **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for the component
diagram, the monolith-to-service mapping, and sequence diagrams for each
request flow.

| Service | Port | Owns | Responsibilities |
|---|---|---|---|
| `gateway` | 8080 (public) | — | Serves the frontend and images, `/health`, and routes `/auth/*`, `/products*`, `/order` |
| `auth-service` | 8001 | `auth_db.users` | Register, login (JWT), `GET /auth/me` token introspection |
| `product-service` | 8002 | `products_db.products` | Catalog, admin create and update, low-stock, internal reserve and release |
| `order-service` | 8003 | `orders_db.orders`, `order_items`, `carts`, `cart_items` | Checkout saga |

### Install dependencies and run tests locally

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r unselected/requirements.txt
cd unselected
python -m pytest -q
```

The tests run every service in-process, each against its own in-memory SQLite
database. Calls between services go through `httpx.ASGITransport`, so the
gateway → service and service → service HTTP hops are tested without Docker.

| Test module | Covers |
|---|---|
| `tests/test_api.py` | End-to-end through the gateway, including the same scenarios as `Selected/tests/test_api.py` plus checkout edge cases |
| `tests/test_auth_service.py` | Registration, login, and the `/auth/me` contract |
| `tests/test_product_service.py` | Delegated authentication, internal-endpoint guard, reserve and release, auth-service outage |
| `tests/test_order_service.py` | Price capture, product-service outage, saga compensation |
| `tests/test_gateway.py` | Static files, health aggregation, query forwarding, `/internal` not exposed, upstream outage |

### Build and run the system

From the repository root:

```bash
docker compose -f unselected/docker-compose.yaml up --build -d
docker compose -f unselected/docker-compose.yaml ps
```

On first start, each PostgreSQL container sets up its schema from its
service's `migrations/` folder. Seed demo data **once**:

```bash
docker compose -f unselected/docker-compose.yaml exec auth-service python seed.py
docker compose -f unselected/docker-compose.yaml exec product-service python seed.py
```

- Storefront: <http://localhost:8080>
- Gateway health: <http://localhost:8080/health>
- Health of all services: <http://localhost:8080/health/services>

Only the gateway publishes a host port. Each service's own OpenAPI docs are
inside the Docker network at `/docs`.

Demo credentials are the same as in `Selected`: `admin@ecom.com` / `admin123`
and `john@ecom.com` / `customer123`.

Stop with `docker compose -f unselected/docker-compose.yaml down`. Add `-v`
to also delete the three database volumes.

### Project structure

```text
unselected/
  docs/ARCHITECTURE.md        Diagrams and request flows
  docker-compose.yaml         3 databases + 4 services
  services/
    gateway/                  gateway/{main,proxy,config}.py, static/
    auth_service/             auth_service/{main,router,service,models}.py, core/, migrations/, seed.py
    product_service/          product_service/{main,router,service,models}.py, core/, migrations/, seed.py
    order_service/            order_service/{main,router,service,models,clients}.py, core/, migrations/
  tests/                      pytest suite (conftest wires the services together)
```
