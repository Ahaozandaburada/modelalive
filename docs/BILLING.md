# Model Alive — Billing & Stripe Setup

## Pricing tiers

| Tier | Checks/month | Price | How |
|------|--------------|-------|-----|
| **Free** | 100 | $0 | No key — IP-based on hosted API |
| **Pro** | 100,000 | $29/mo | Stripe Checkout → API key |
| **Enterprise** | Custom | Contact | Manual |

## 1. Stripe Dashboard

1. https://dashboard.stripe.com → **Products** → **Add product**
2. Name: `Model Alive Pro`
3. Pricing: **Recurring** → $29/month
4. Copy the **Price ID** (`price_...`)

## 2. Webhook

1. **Developers** → **Webhooks** → **Add endpoint**
2. URL: `https://modelalive.fly.dev/v1/billing/webhook`
3. Events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copy **Signing secret** (`whsec_...`)

## 3. Fly secrets

```bash
fly secrets set \
  STRIPE_SECRET_KEY="sk_live_..." \
  STRIPE_WEBHOOK_SECRET="whsec_..." \
  STRIPE_PRICE_PRO="price_..." \
  MODELALIVE_PUBLIC_URL="https://modelalive.fly.dev" \
  MODELALIVE_ENFORCE_QUOTA=1 \
  -a modelalive
```

Test mode: use `sk_test_...` and test price ID first.

## 4. Customer flow

```bash
# See plans
curl https://modelalive.fly.dev/v1/billing/plans

# Start checkout
curl -X POST https://modelalive.fly.dev/v1/billing/checkout \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","plan":"pro"}'
# → { "checkout_url": "https://checkout.stripe.com/..." }

# After payment → success URL returns session_id
# Retrieve API key ONCE:
curl "https://modelalive.fly.dev/v1/billing/key?session_id=cs_..."

# Use key
curl -H "X-API-Key: ma_live_..." \
  "https://modelalive.fly.dev/v1/alive?model=gpt-4o"

# Check usage
curl -H "X-API-Key: ma_live_..." https://modelalive.fly.dev/v1/usage

# Manage subscription
curl -X POST -H "X-API-Key: ma_live_..." https://modelalive.fly.dev/v1/billing/portal
```

## 5. Persistence

API keys and usage are stored in SQLite at `/data/modelalive.db` on Fly.

Mount is configured in `fly.toml`. Create volume once:

```bash
fly volumes create modelalive_data --region iad --size 1 -a modelalive
fly deploy -a modelalive
```

## 6. Local dev

```bash
export MODELALIVE_DB_PATH=/tmp/modelalive-test.db
export STRIPE_SECRET_KEY=sk_test_...
export STRIPE_WEBHOOK_SECRET=whsec_...
export STRIPE_PRICE_PRO=price_...
stripe listen --forward-to localhost:8080/v1/billing/webhook
uvicorn api.main:app --reload
```
