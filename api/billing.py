"""Stripe billing: checkout, webhooks, customer portal."""

from __future__ import annotations

import os
from typing import Any

from api.store import generate_api_key, get_store

PLANS: dict[str, dict[str, Any]] = {
    "free": {
        "name": "Free",
        "monthly_checks": 100,
        "price_usd": 0,
        "description": "IP-based, no API key required",
    },
    "pro": {
        "name": "Pro",
        "monthly_checks": 100_000,
        "price_usd": 29,
        "description": "API key, 100K checks/month, email support",
        "stripe_price_env": "STRIPE_PRICE_PRO",
    },
    "enterprise": {
        "name": "Enterprise",
        "monthly_checks": 10_000_000,
        "price_usd": None,
        "description": "Custom limits, SLA, private registry — contact sales",
    },
}


def stripe_enabled() -> bool:
    return bool(os.environ.get("STRIPE_SECRET_KEY", "").strip())


def public_base_url() -> str:
    return os.environ.get("MODELALIVE_PUBLIC_URL", "https://modelalive.fly.dev").rstrip("/")


def _stripe():
    import stripe

    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    return stripe


def list_plans() -> dict[str, Any]:
    return {"plans": PLANS}


def create_checkout_session(*, email: str, plan: str = "pro") -> dict[str, str]:
    if not stripe_enabled():
        raise RuntimeError("Stripe is not configured (set STRIPE_SECRET_KEY)")
    if plan not in {"pro"}:
        raise ValueError(f"Unsupported plan: {plan}")

    price_env = PLANS[plan].get("stripe_price_env")
    price_id = os.environ.get(price_env or "", "").strip() if price_env else ""
    if not price_id:
        raise RuntimeError(f"Set {price_env} to your Stripe Price ID")

    base = public_base_url()
    stripe = _stripe()
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{base}/v1/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base}/v1/billing/plans",
        metadata={"plan": plan, "product": "modelalive"},
        subscription_data={"metadata": {"plan": plan}},
    )
    return {"checkout_url": session.url or "", "session_id": session.id}


def handle_webhook(payload: bytes, sig_header: str | None) -> dict[str, str]:
    if not stripe_enabled():
        raise RuntimeError("Stripe is not configured")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()
    if not webhook_secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not set")

    stripe = _stripe()
    event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    store = get_store()

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        plan = (session.get("metadata") or {}).get("plan", "pro")
        raw_key = generate_api_key()
        store.create_key(
            raw_key=raw_key,
            tier=plan,
            email=session.get("customer_email") or session.get("customer_details", {}).get("email"),
            stripe_customer_id=session.get("customer"),
            stripe_subscription_id=session.get("subscription"),
            checkout_session_id=session.get("id"),
        )
        store.store_session_key(session["id"], raw_key)

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        store.set_subscription_status(sub["id"], status="canceled")

    elif event["type"] == "customer.subscription.updated":
        sub = event["data"]["object"]
        status = "active" if sub.get("status") == "active" else "canceled"
        store.set_subscription_status(sub["id"], status=status)

    return {"status": "ok", "type": event["type"]}


def retrieve_key_for_session(session_id: str) -> dict[str, Any] | None:
    store = get_store()
    record = store.get_key_by_session(session_id)
    if record is None:
        return None
    if record.get("key_retrieved"):
        return {"already_retrieved": True, "key_prefix": record["key_prefix"], "tier": record["tier"]}
    raw = store.pop_session_key(session_id)
    if raw is None:
        return {"pending": True, "message": "Payment processing — retry in a few seconds"}
    return {"api_key": raw, "tier": record["tier"], "key_prefix": record["key_prefix"]}


def create_portal_session(*, stripe_customer_id: str) -> dict[str, str]:
    if not stripe_enabled():
        raise RuntimeError("Stripe is not configured")
    stripe = _stripe()
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{public_base_url()}/v1/billing/plans",
    )
    return {"portal_url": session.url or ""}
