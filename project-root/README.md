# Customer Data Pipeline — Backend Assessment

A 3-service Docker data pipeline built with Flask, FastAPI, and PostgreSQL.

## Architecture

```
Flask Mock Server (5000) → FastAPI Pipeline (8000) → PostgreSQL (5432)
```

| Service           | Port | Description                              |
|-------------------|------|------------------------------------------|
| `mock-server`     | 5000 | Flask REST API serving customer JSON     |
| `pipeline-service`| 8000 | FastAPI ingestion pipeline + query API   |
| `postgres`        | 5432 | PostgreSQL 15 database                   |

---

## Prerequisites

- Docker Desktop (running)
- Docker Compose v2+

---

## Quick Start

```bash
# Clone / unzip the project, then:
cd project-root

# Build and start all services
docker-compose up -d --build

# Check all services are running
docker-compose ps
```

Wait ~15 seconds for services to become healthy.

---

## API Reference

### Flask Mock Server (`http://localhost:5000`)

| Endpoint                    | Method | Description                        |
|-----------------------------|--------|------------------------------------|
| `/api/health`               | GET    | Health check                       |
| `/api/customers`            | GET    | Paginated customer list            |
| `/api/customers/{id}`       | GET    | Single customer by ID              |

**Pagination params:** `?page=1&limit=10`

```bash
# Health check
curl http://localhost:5000/api/health

# Paginated list
curl "http://localhost:5000/api/customers?page=1&limit=5"

# Single customer
curl http://localhost:5000/api/customers/CUST001
```

---

### FastAPI Pipeline Service (`http://localhost:8000`)

| Endpoint                    | Method | Description                                    |
|-----------------------------|--------|------------------------------------------------|
| `/api/health`               | GET    | Health check                                   |
| `/api/ingest`               | POST   | Fetch all Flask data → upsert into PostgreSQL  |
| `/api/customers`            | GET    | Paginated customer list from DB                |
| `/api/customers/{id}`       | GET    | Single customer from DB or 404                 |

**Interactive docs:** http://localhost:8000/docs

```bash
# Ingest all data from Flask into PostgreSQL
curl -X POST http://localhost:8000/api/ingest
# → {"status": "success", "records_processed": 22}

# Query customers from DB
curl "http://localhost:8000/api/customers?page=1&limit=5"

# Single customer from DB
curl http://localhost:8000/api/customers/CUST001
```

---

## Response Format

```json
{
  "data": [...],
  "total": 22,
  "page": 1,
  "limit": 10,
  "total_pages": 3
}
```

---

## Project Structure

```
project-root/
├── docker-compose.yml
├── README.md
├── mock-server/
│   ├── app.py                   # Flask application
│   ├── data/
│   │   └── customers.json       # 22 customer records
│   ├── Dockerfile
│   └── requirements.txt
└── pipeline-service/
    ├── main.py                  # FastAPI application + endpoints
    ├── database.py              # SQLAlchemy engine + session
    ├── models/
    │   └── customer.py          # Customer ORM model
    ├── services/
    │   └── ingestion.py         # Auto-paginated fetch + upsert logic
    ├── Dockerfile
    └── requirements.txt
```

---

## Database Schema

```sql
CREATE TABLE customers (
    customer_id     VARCHAR(50)     PRIMARY KEY,
    first_name      VARCHAR(100)    NOT NULL,
    last_name       VARCHAR(100)    NOT NULL,
    email           VARCHAR(255)    NOT NULL,
    phone           VARCHAR(20),
    address         TEXT,
    date_of_birth   DATE,
    account_balance DECIMAL(15,2),
    created_at      TIMESTAMP
);
```

---

## Stopping Services

```bash
docker-compose down          # Stop containers
docker-compose down -v       # Stop and remove volumes (wipes DB)
```

---

## Notes

- The `POST /api/ingest` endpoint handles **auto-pagination** from Flask — it fetches all pages automatically regardless of total record count.
- Upsert logic uses PostgreSQL's native `INSERT ... ON CONFLICT DO UPDATE`, so re-running `/api/ingest` is idempotent.
- Tables are created automatically on FastAPI startup via SQLAlchemy.
