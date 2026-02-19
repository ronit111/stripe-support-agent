---
title: "Metadata"
category: "Developer Experience"
source: "https://docs.stripe.com/api/metadata"
---

# Metadata

Metadata is a powerful feature in Stripe that lets you attach custom key-value pairs to most Stripe objects. This allows you to store additional structured information relevant to your business directly on Stripe objects, making it easier to track, search, and reconcile data between Stripe and your own systems.

## What Is Metadata?

Metadata is a set of key-value pairs that you can attach to objects like charges, customers, subscriptions, invoices, payment intents, and more. Stripe does not use metadata internally — it exists entirely for your benefit.

Common use cases include:
- **Order tracking**: Attach your internal order ID to a PaymentIntent
- **User mapping**: Store your application's user ID on a Customer object
- **Campaign attribution**: Tag charges with marketing campaign identifiers
- **Feature flags**: Mark subscriptions with plan tiers or feature access levels
- **Audit trails**: Store the ID of the admin who initiated a refund

## Working with Metadata

### Setting Metadata

You can set metadata when creating or updating most Stripe objects:

```python
import stripe

customer = stripe.Customer.create(
    email="jenny@example.com",
    metadata={
        "internal_user_id": "usr_12345",
        "signup_source": "landing_page_v2",
        "plan_tier": "professional",
    }
)

# Update metadata on an existing object
stripe.Customer.modify(
    "cus_abc123",
    metadata={
        "plan_tier": "enterprise",
        "account_manager": "jane",
    }
)
```

### Removing Metadata

To remove a metadata key, set its value to an empty string:

```python
stripe.Customer.modify(
    "cus_abc123",
    metadata={
        "signup_source": "",  # Removes this key
    }
)
```

### Reading Metadata

Metadata is returned as part of the object in API responses:

```python
customer = stripe.Customer.retrieve("cus_abc123")
user_id = customer.metadata.get("internal_user_id")
```

## Metadata Limits

- **Maximum 50 keys** per object
- **Key length**: Up to 40 characters
- **Value length**: Up to 500 characters
- **Keys and values** must be strings

These limits are per-object. Each Stripe object can have its own independent set of up to 50 metadata key-value pairs.

## Supported Objects

Metadata can be set on most Stripe objects, including Customers, PaymentIntents, Charges, Subscriptions, Invoices, Products, Prices, Refunds, Transfers, and Coupons.

## Searching by Metadata

Stripe's Search API allows you to query objects by their metadata values:

```python
results = stripe.Customer.search(
    query='metadata["internal_user_id"]:"usr_12345"'
)

results = stripe.PaymentIntent.search(
    query='metadata["order_id"]:"order_67890"'
)
```

The Search API supports metadata queries on Customers, Charges, PaymentIntents, Subscriptions, Invoices, and Prices.

## Best Practices

**Use consistent key naming**: Establish a naming convention (e.g., snake_case) and document it for your team.

**Store IDs, not data**: Use metadata to store reference IDs that link to your own database rather than duplicating data.

**Don't store sensitive information**: Metadata is visible in the Dashboard and API responses. Never store passwords, credit card numbers, or sensitive PII.

**Use metadata for reconciliation**: Attach your internal IDs to Stripe objects so you can match webhook events to your own records.
