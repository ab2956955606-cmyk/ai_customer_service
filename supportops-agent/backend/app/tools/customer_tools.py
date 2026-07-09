from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Customer


def get_customer_by_email(db: Session, email: str | None) -> dict | None:
    if not email:
        return None
    customer = db.query(Customer).filter(Customer.email == email.lower()).first()
    if customer is None:
        return None
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "plan": customer.plan,
        "status": customer.status,
    }
