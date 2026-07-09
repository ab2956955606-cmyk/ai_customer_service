from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Customer, Order
from app.rag.indexer import reindex_documents


CUSTOMERS = [
    {"name": "Alice Chen", "email": "alice@example.com", "plan": "Pro", "status": "active"},
    {"name": "Bob Li", "email": "bob@example.com", "plan": "Free", "status": "active"},
    {"name": "Charlie Zhang", "email": "charlie@example.com", "plan": "Business", "status": "active"},
]

ORDERS = [
    {
        "customer_email": "alice@example.com",
        "order_number": "ORD-1001",
        "status": "processing",
        "amount": 89.00,
        "shipping_address": "100 Market Street, San Francisco, CA",
    },
    {
        "customer_email": "bob@example.com",
        "order_number": "ORD-1002",
        "status": "shipped",
        "amount": 29.00,
        "shipping_address": "200 River Road, Austin, TX",
    },
    {
        "customer_email": "charlie@example.com",
        "order_number": "ORD-1003",
        "status": "delivered",
        "amount": 499.00,
        "shipping_address": "300 Harbor Way, Seattle, WA",
    },
]


def seed_data(db: Session) -> None:
    for data in CUSTOMERS:
        if db.query(Customer).filter(Customer.email == data["email"]).first() is None:
            db.add(Customer(**data))
    for data in ORDERS:
        if db.query(Order).filter(Order.order_number == data["order_number"]).first() is None:
            db.add(Order(**data))
    db.commit()
    reindex_documents(db)
