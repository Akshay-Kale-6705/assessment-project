from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from database import get_db, init_db
from models.customer import Customer
from services.ingestion import run_ingestion_pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    init_db()
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title="Customer Data Pipeline Service",
    description="FastAPI service that ingests customer data from Flask mock server into PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "pipeline-service"}


@app.post("/api/ingest")
def ingest(db: Session = Depends(get_db)):
    """
    Fetch all customer data from Flask mock server (with auto-pagination)
    and upsert into PostgreSQL.
    """
    try:
        result = run_ingestion_pipeline(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/api/customers")
def list_customers(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=10, ge=1, le=100, description="Records per page"),
    db: Session = Depends(get_db),
):
    """Return paginated customer list from the database."""
    total = db.query(Customer).count()
    offset = (page - 1) * limit
    customers = db.query(Customer).offset(offset).limit(limit).all()

    return {
        "data": [c.to_dict() for c in customers],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 0,
    }


@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Return a single customer by ID or 404 if not found."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")
    return {"data": customer.to_dict()}
