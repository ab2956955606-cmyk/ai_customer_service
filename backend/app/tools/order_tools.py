from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models import Order


ORDER_RE = re.compile(r"\bORD-\d{4,}\b", re.IGNORECASE)


def extract_order_number(text: str) -> str | None:
    match = ORDER_RE.search(text)
    return match.group(0).upper() if match else None


def order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "customer_email": order.customer_email,
        "order_number": order.order_number,
        "status": order.status,
        "amount": order.amount,
        "shipping_address": order.shipping_address,
    }


def get_order_by_number(db: Session, order_number: str | None) -> dict | None:
    if not order_number:
        return None
    order = db.query(Order).filter(Order.order_number == order_number.upper()).first()
    return order_to_dict(order) if order else None


def search_orders_by_customer(db: Session, email: str | None) -> list[dict]:
    if not email:
        return []
    orders = (
        db.query(Order)
        .filter(Order.customer_email == email.lower())
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )
    return [order_to_dict(order) for order in orders]


def update_shipping_address(db: Session, order_id: int, new_address: str) -> dict:
    order = db.get(Order, order_id)
    if order is None:
        raise ValueError("Order not found")
    order.shipping_address = new_address
    db.commit()
    db.refresh(order)
    return order_to_dict(order)


def cancel_order(db: Session, order_id: int) -> dict:
    order = db.get(Order, order_id)
    if order is None:
        raise ValueError("Order not found")
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return order_to_dict(order)
