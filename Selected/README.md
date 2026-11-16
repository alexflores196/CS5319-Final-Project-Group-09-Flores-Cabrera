# E-commerce API

A FastAPI e-commerce application with authentication, role-based access control (RBAC), a product catalog, product images, inventory tracking, and simulated checkout. PostgreSQL is used for the Docker Compose environment.

## Features

- Customer registration and login with JWT authentication
- Role-based access control for admin-only actions
- Product catalog with locally served images
- Admin product creation and editing, including price, inventory, and image path
- Low-stock product reporting
- Simulated checkout with inventory deduction
- Static frontend served by the API
- Automated API tests using `pytest`

## Tech stack

- Python and FastAPI
- SQLAlchemy async ORM
- PostgreSQL with `asyncpg`
- Pydantic
- Docker Compose
- `pytest`, `pytest-asyncio`, and `httpx`

## Run with Docker Compose

**Prerequisite:** Docker Desktop or Docker Engine with the Compose plugin.

From the project root, build and start the application:

```bash
docker compose up --build -d
```

Check that the API and database are running:

```bash
docker compose ps
docker compose logs --tail=100 api
```

The storefront is available at <http://localhost:8080>. Interactive API documentation is at <http://localhost:8080/docs>, and the health endpoint is at <http://localhost:8080/health>.

PostgreSQL runs the SQL files in `migrations/` when its data volume is initialized for the first time.

### Seed demo data

After the containers are running, create the demo users and products:

```bash
docker compose exec api python seed.py
```

Run this once for a fresh database. Running it again may fail because the demo email addresses already exist.

### Demo credentials

| Role | Email | Password |
|---|---|---|
| Admin | `admin@ecom.com` | `admin123` |
| Customer | `john@ecom.com` | `customer123` |

These credentials and the default database credentials in `docker-compose.yaml` are for local development only. Do not use them in a public or production deployment.

### Admin workflow

1. Open the storefront and sign in with the admin credentials above.
2. Select **Admin Panel**.
3. Use **Add Product** to create a product with its initial inventory and image path.
4. Use **Manage Products** to edit a product’s details, price, inventory, or image path.

Product image paths should point to files under `static/images/products/`, for example:

`/static/images/products/wireless-headphones.jpg`

### Stop the application

```bash
docker compose down
```

This stops the containers but preserves the database volume. To delete the local database volume as well:

```bash
docker compose down -v
```

**Warning:** `docker compose down -v` permanently deletes the database data stored in that volume. Database initialization scripts run again only when PostgreSQL initializes a new data volume.

## Run the tests

Create and activate a virtual environment, install the dependencies, and run the tests:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

The API tests cover registration and login, RBAC for product creation and editing, low-stock reporting, and inventory deduction during checkout.

## API overview

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a customer |
| `POST` | `/auth/login` | Log in and receive a JWT |
| `GET` | `/products` | List active products |
| `POST` | `/products` | Create a product (admin only) |
| `PUT` | `/products/{product_id}` | Update a product (admin only) |
| `GET` | `/products/low-stock?threshold=5` | List products at or below the stock threshold (admin only) |
| `POST` | `/order` | Place an order and deduct inventory |

Authenticated endpoints expect a bearer token in the `Authorization` header:

```text
Authorization: Bearer <access_token>
```

## Project structure

```text
app/
  core/          Configuration, database, and security
  modules/
    auth/        Registration, login, and authentication
    cart/        Cart models
    orders/      Order models, routes, and services
    products/    Product models, routes, and services
    users/       User models
migrations/      PostgreSQL schema initialization scripts
static/          Frontend and product image files
tests/           Automated tests
docker-compose.yaml
Dockerfile
seed.py
```