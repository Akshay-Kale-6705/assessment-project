import os
import requests
import dlt
from dlt.sources.rest_api import rest_api_source
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models.customer import Customer

FLASK_BASE_URL = os.getenv("FLASK_BASE_URL", "http://mock-server:5000")


def fetch_all_customers_from_flask() -> list[dict]:
    """Fetch all customers from Flask mock server, handling pagination automatically."""
    all_customers = []
    page = 1
    limit = 10

    while True:
        url = f"{FLASK_BASE_URL}/api/customers"
        response = requests.get(url, params={"page": page, "limit": limit}, timeout=10)
        response.raise_for_status()

        payload = response.json()
        data = payload.get("data", [])
        total = payload.get("total", 0)

        all_customers.extend(data)

        # Stop when we've fetched all records
        if len(all_customers) >= total or not data:
            break

        page += 1

    return all_customers


def _coerce_customer(raw: dict) -> dict:
    """Coerce raw JSON fields to proper Python types for SQLAlchemy."""
    dob = raw.get("date_of_birth")
    created = raw.get("created_at")
    balance = raw.get("account_balance")

    return {
        "customer_id": raw["customer_id"],
        "first_name": raw["first_name"],
        "last_name": raw["last_name"],
        "email": raw["email"],
        "phone": raw.get("phone"),
        "address": raw.get("address"),
        "date_of_birth": date.fromisoformat(dob) if dob else None,
        "account_balance": Decimal(str(balance)) if balance is not None else None,
        "created_at": datetime.fromisoformat(created) if created else None,
    }


def upsert_customers(db: Session, customers: list[dict]) -> int:
    """
    Upsert customer records into PostgreSQL.
    Uses INSERT ... ON CONFLICT DO UPDATE (native PostgreSQL upsert).
    """
    if not customers:
        return 0

    coerced = [_coerce_customer(c) for c in customers]

    stmt = pg_insert(Customer).values(coerced)
    stmt = stmt.on_conflict_do_update(
        index_elements=["customer_id"],
        set_={
            "first_name": stmt.excluded.first_name,
            "last_name": stmt.excluded.last_name,
            "email": stmt.excluded.email,
            "phone": stmt.excluded.phone,
            "address": stmt.excluded.address,
            "date_of_birth": stmt.excluded.date_of_birth,
            "account_balance": stmt.excluded.account_balance,
            "created_at": stmt.excluded.created_at,
        },
    )

    db.execute(stmt)
    db.commit()
    return len(coerced)


def run_ingestion_pipeline(db: Session) -> dict:
    """
    Full pipeline: fetch from Flask → upsert into PostgreSQL.
    Returns a result summary dict.
    """
    customers = fetch_all_customers_from_flask()
    records_processed = upsert_customers(db, customers)
    return {
        "status": "success",
        "records_processed": records_processed,
    }
