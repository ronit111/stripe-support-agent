---
title: "Usage-Based Billing"
category: "Billing"
source: "https://docs.stripe.com/billing/subscriptions/usage-based"
---

# Usage-Based Billing

Usage-based (metered) billing lets you charge customers based on how much they consume during a billing period rather than a fixed recurring amount. This model is common for API calls, compute hours, storage, bandwidth, messages sent, and similar consumption metrics.

## How Metered Billing Works

With metered billing, you:

1. Create a **Price** with `recurring[usage_type]` set to `metered`.
2. Create a **Subscription** with that price.
3. Report **usage records** throughout the billing period via the API.
4. At the end of the billing period, Stripe totals the usage, generates an invoice with the calculated amount, and collects payment.

The key difference from standard subscriptions: you don't set a `quantity` on the subscription item. Instead, you report usage incrementally and Stripe calculates the charge.

## Setting Up Metered Prices

```python
import stripe

# Create a metered price (per API call)
price = stripe.Price.create(
    product="prod_API_SERVICE",
    currency="usd",
    unit_amount=1,  # $0.01 per unit
    recurring={
        "interval": "month",
        "usage_type": "metered",
    },
)

# Create a metered price with tiered pricing
price = stripe.Price.create(
    product="prod_API_SERVICE",
    currency="usd",
    recurring={
        "interval": "month",
        "usage_type": "metered",
    },
    billing_scheme="tiered",
    tiers_mode="graduated",
    tiers=[
        {"up_to": 1000, "unit_amount": 10},       # $0.10/call for first 1,000
        {"up_to": 10000, "unit_amount": 5},        # $0.05/call for 1,001-10,000
        {"up_to": "inf", "unit_amount": 2},        # $0.02/call for 10,001+
    ],
)
```

## Creating a Metered Subscription

```python
subscription = stripe.Subscription.create(
    customer="cus_ABC123",
    items=[
        {"price": "price_metered_api_calls"},
    ],
)

# The subscription item ID is needed for reporting usage
subscription_item_id = subscription["items"]["data"][0]["id"]
# e.g., "si_ABC123"
```

A metered subscription starts with $0 in charges. The amount grows as you report usage throughout the billing period.

## Reporting Usage Records

Report usage to Stripe by creating usage records on the subscription item. You should report usage regularly (e.g., hourly or daily) rather than in a single batch at the end of the period.

```python
# Report usage for a subscription item
stripe.SubscriptionItem.create_usage_record(
    "si_ABC123",
    quantity=150,
    timestamp=1706745600,  # Unix timestamp of when usage occurred
    action="increment",    # Add to existing usage
)
```

### The `action` Parameter

| Action | Description |
|--------|-------------|
| `increment` | Adds the reported quantity to any existing usage for that timestamp. This is the default and most common option. |
| `set` | Replaces the usage for the given timestamp. Useful for correcting previously reported usage. |

### Reporting Patterns

**Incremental reporting** (recommended): Report usage as it happens throughout the billing period.

```python
# Report each batch of API calls as they occur
stripe.SubscriptionItem.create_usage_record(
    "si_ABC123",
    quantity=47,          # 47 API calls in this batch
    action="increment",
)
```

**Periodic batch reporting**: Aggregate usage and report at regular intervals (e.g., every hour).

```python
# Hourly batch report
import time

stripe.SubscriptionItem.create_usage_record(
    "si_ABC123",
    quantity=1250,           # Total calls in the past hour
    timestamp=int(time.time()),
    action="increment",
)
```

## Aggregation Methods

When you create a metered price, you can choose how Stripe aggregates usage records within a billing period. Set this via `recurring[aggregate_usage]` on the Price.

### `sum` (Default)

Adds up all usage records in the billing period. The total is multiplied by the unit price.

Best for: API calls, messages sent, emails delivered, events processed.

```python
price = stripe.Price.create(
    product="prod_ABC",
    currency="usd",
    unit_amount=1,
    recurring={
        "interval": "month",
        "usage_type": "metered",
        "aggregate_usage": "sum",
    },
)
```

If you report 100, 200, and 150 over the billing period, the total usage is 450.

### `last_during_period`

Uses only the last usage record reported during the billing period. Previous records are ignored.

Best for: Active user counts, storage used (where the final value represents the current state), number of seats.

```python
price = stripe.Price.create(
    product="prod_STORAGE",
    currency="usd",
    unit_amount=100,  # $1.00 per GB
    recurring={
        "interval": "month",
        "usage_type": "metered",
        "aggregate_usage": "last_during_period",
    },
)
```

If you report 50GB, then 75GB, then 60GB, the charge is based on 60GB (the last reported value).

### `max`

Uses the highest usage record reported during the billing period.

Best for: Peak concurrent users, maximum bandwidth, high-water-mark billing.

```python
price = stripe.Price.create(
    product="prod_BANDWIDTH",
    currency="usd",
    unit_amount=500,  # $5.00 per unit
    recurring={
        "interval": "month",
        "usage_type": "metered",
        "aggregate_usage": "max",
    },
)
```

If you report 100, 350, and 200, the charge is based on 350 (the maximum).

## Billing Cycle Behavior

- Usage records are accumulated throughout the billing period.
- At the end of the billing period, Stripe calculates the total usage based on the aggregation method.
- An invoice is generated with a line item reflecting the total usage and the calculated charge.
- Usage resets to zero at the start of each new billing period.
- Usage reported after the billing period ends but with a timestamp within the previous period is still included (there is a brief grace window).

### Retrieving Current Usage

You can retrieve a usage record summary for the current billing period:

```python
usage_summary = stripe.SubscriptionItem.list_usage_record_summaries(
    "si_ABC123",
    limit=1,
)

current_usage = usage_summary.data[0]
print(f"Total usage: {current_usage.total_usage}")
print(f"Period: {current_usage.period.start} - {current_usage.period.end}")
```

## Combining Metered and Fixed Pricing

A common SaaS pattern is a base subscription fee plus metered overages. You can achieve this by adding both a fixed price and a metered price to the same subscription.

```python
subscription = stripe.Subscription.create(
    customer="cus_ABC123",
    items=[
        {"price": "price_base_plan_49"},           # $49/month base fee
        {"price": "price_metered_api_overages"},   # $0.01 per API call over included amount
    ],
)
```

To implement an "included usage" model (e.g., 10,000 API calls included, then $0.01 per extra call), use tiered pricing with a free first tier:

```python
price = stripe.Price.create(
    product="prod_API",
    currency="usd",
    recurring={
        "interval": "month",
        "usage_type": "metered",
    },
    billing_scheme="tiered",
    tiers_mode="graduated",
    tiers=[
        {"up_to": 10000, "unit_amount": 0},    # First 10,000 calls free
        {"up_to": "inf", "unit_amount": 1},     # $0.01 per call after that
    ],
)
```

## Common Support Scenarios

**Customer says their usage is wrong**: Retrieve the usage record summaries to see what was reported. Check timestamps to confirm records fall within the correct billing period. If usage was over-reported, use `action="set"` to correct the value for a specific timestamp.

**Usage not appearing on invoice**: Usage records must be reported before the billing period ends. If reported after invoice finalization, they won't be included on the current invoice. They will carry over or be lost depending on your configuration.

**Subscription shows $0 charge**: For metered subscriptions, this is normal if no usage has been reported yet. Usage is billed in arrears at the end of the billing period.

**Need to give a customer credit for usage**: Create a credit note on the paid invoice, or report a negative adjustment in the next period if your application logic supports it. Stripe usage records only accept positive quantities, so credits must be handled via credit notes or invoice-level adjustments.

**Customer wants real-time usage visibility**: Stripe does not provide a customer-facing usage dashboard. You need to build this by tracking usage in your own database and using `list_usage_record_summaries` for reconciliation.
