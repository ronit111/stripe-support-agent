---
title: "Stripe Subscriptions"
category: "Billing"
source: "https://docs.stripe.com/billing/subscriptions"
---

# Stripe Subscriptions

Subscriptions allow you to charge customers on a recurring basis. Stripe Billing handles the full lifecycle of recurring payments, from initial signup through cancellation, including trial periods, prorations, and dunning for failed payments.

## How Subscriptions Work

A subscription ties a **Customer** to one or more **Price** objects (which belong to **Products**). At each billing interval, Stripe automatically generates an **Invoice**, attempts payment against the customer's default payment method, and updates the subscription status accordingly.

### Core Objects

- **Product**: What you sell (e.g., "Pro Plan", "Enterprise Plan").
- **Price**: How much and how often you charge (e.g., $49/month, $499/year). A single Product can have multiple Prices.
- **Subscription**: The relationship between a Customer and one or more Prices, including billing cycle, status, and metadata.
- **Subscription Item**: Each Price on a subscription is represented as a Subscription Item. A subscription can have multiple items.

## Subscription Lifecycle

Every subscription moves through a series of statuses:

| Status | Description |
|--------|-------------|
| `trialing` | The subscription is in a free trial period. No invoices are generated until the trial ends. |
| `active` | The subscription is current and payment has been collected successfully. |
| `past_due` | The most recent invoice payment failed. Stripe will retry according to your retry settings. |
| `canceled` | The subscription has been canceled. No further invoices will be generated. |
| `unpaid` | All retry attempts have been exhausted. The subscription remains in this terminal state until action is taken. |
| `incomplete` | The initial payment on the subscription failed. The customer has 23 hours to complete payment. |
| `incomplete_expired` | The initial payment was not completed within 23 hours. |
| `paused` | The subscription has been paused and will not generate invoices until resumed. |

### Typical Flow

```
incomplete → active → past_due → canceled
                ↑         |
                └─────────┘  (if retry succeeds)
```

For subscriptions with trials:
```
trialing → active → past_due → canceled
```

## Creating a Subscription

```python
import stripe

# Create a subscription with a single price
subscription = stripe.Subscription.create(
    customer="cus_ABC123",
    items=[
        {"price": "price_monthly_pro"},
    ],
)

# Create a subscription with a trial period
subscription = stripe.Subscription.create(
    customer="cus_ABC123",
    items=[
        {"price": "price_monthly_pro"},
    ],
    trial_period_days=14,
)

# Create a subscription with multiple items
subscription = stripe.Subscription.create(
    customer="cus_ABC123",
    items=[
        {"price": "price_base_plan"},
        {"price": "price_addon_analytics"},
    ],
)
```

## Pricing Models

### Flat-Rate Pricing

The simplest model. Customers pay a fixed amount per billing interval.

```python
price = stripe.Price.create(
    product="prod_ABC123",
    unit_amount=4900,  # $49.00
    currency="usd",
    recurring={"interval": "month"},
)
```

### Per-Seat (Per-Unit) Pricing

Charge based on the number of units (seats, licenses, etc.). The `quantity` on the subscription item determines the total charge.

```python
subscription = stripe.Subscription.create(
    customer="cus_ABC123",
    items=[
        {
            "price": "price_per_seat",
            "quantity": 5,  # 5 seats
        },
    ],
)

# Later, update the quantity when the customer adds seats
stripe.SubscriptionItem.modify(
    "si_ITEM123",
    quantity=8,  # Now 8 seats
)
```

### Tiered Pricing

Charge different rates depending on volume. Stripe supports two tiered modes:

- **Volume**: The tier that the total quantity falls into determines the per-unit price for all units.
- **Graduated**: Each unit is priced according to the tier it falls into (like tax brackets).

```python
price = stripe.Price.create(
    product="prod_ABC123",
    currency="usd",
    recurring={"interval": "month"},
    billing_scheme="tiered",
    tiers_mode="graduated",  # or "volume"
    tiers=[
        {"up_to": 5, "unit_amount": 1000},      # $10/unit for first 5
        {"up_to": 20, "unit_amount": 800},       # $8/unit for 6-20
        {"up_to": "inf", "unit_amount": 500},    # $5/unit for 21+
    ],
)
```

## Upgrades, Downgrades, and Proration

When a customer switches plans mid-cycle, Stripe handles proration by default. It calculates the unused time on the old plan as a credit and the remaining time on the new plan as a charge, then applies the net difference to the next invoice.

```python
subscription = stripe.Subscription.retrieve("sub_ABC123")

# Upgrade to a new price
stripe.Subscription.modify(
    "sub_ABC123",
    items=[
        {
            "id": subscription["items"]["data"][0]["id"],
            "price": "price_enterprise_monthly",
        },
    ],
    proration_behavior="create_prorations",  # default behavior
)
```

### Proration Behavior Options

| Value | Description |
|-------|-------------|
| `create_prorations` | Generate proration line items on the next invoice (default). |
| `always_invoice` | Generate prorations and immediately invoice the customer. |
| `none` | Do not create any proration line items. The new price takes effect at the next billing cycle. |

## Trial Periods

Trials let customers try your product before being charged.

```python
# Trial via subscription creation
subscription = stripe.Subscription.create(
    customer="cus_ABC123",
    items=[{"price": "price_monthly_pro"}],
    trial_period_days=14,
)

# Trial with a specific end date
subscription = stripe.Subscription.create(
    customer="cus_ABC123",
    items=[{"price": "price_monthly_pro"}],
    trial_end=1672531200,  # Unix timestamp
)
```

During the trial, the subscription status is `trialing`. No invoices are generated. When the trial ends, Stripe creates the first invoice and attempts payment. If no payment method is on file, the subscription moves to `past_due` or `incomplete`.

You can require a payment method at signup even for trials by setting `payment_behavior="default_incomplete"` and confirming the SetupIntent.

## Cancellation Behavior

```python
# Cancel immediately
stripe.Subscription.cancel("sub_ABC123")

# Cancel at end of current billing period
stripe.Subscription.modify(
    "sub_ABC123",
    cancel_at_period_end=True,
)

# Undo a pending cancellation
stripe.Subscription.modify(
    "sub_ABC123",
    cancel_at_period_end=False,
)
```

When `cancel_at_period_end=True`, the subscription remains `active` until the current period ends, then moves to `canceled`. The `cancel_at` field on the subscription shows when cancellation will take effect.

## Common Support Scenarios

**Customer wants a refund for unused time after canceling**: Stripe does not automatically refund prorated amounts on cancellation. You need to manually create a refund or credit note for the unused portion.

**Subscription stuck in `incomplete`**: The initial payment failed. The customer has 23 hours to provide a valid payment method. After that, the subscription moves to `incomplete_expired` and cannot be recovered. Create a new subscription instead.

**Customer charged during trial**: Check whether the trial was configured correctly. Verify `trial_end` or `trial_period_days` was set. If the trial ended and payment was collected, the billing is correct.

**Multiple charges on plan change**: This happens when `proration_behavior` is set to `always_invoice`. Each mid-cycle change generates an immediate invoice for the proration difference.

## Key Webhook Events

- `customer.subscription.created` - New subscription created
- `customer.subscription.updated` - Subscription modified (plan change, status change)
- `customer.subscription.deleted` - Subscription canceled
- `customer.subscription.trial_will_end` - Trial ending in 3 days (useful for sending reminders)
- `invoice.paid` - Subscription payment succeeded
- `invoice.payment_failed` - Subscription payment failed
