---
title: "Payment Intents"
category: "Payments"
source: "https://docs.stripe.com/payments/payment-intents"
---

# Payment Intents

## What Is a PaymentIntent?

A `PaymentIntent` is the core Stripe object that represents your intent to collect a payment from a customer. It guides you through the entire payment process, tracks the state of the payment, and records all attempts to charge the customer.

Every PaymentIntent has a unique `id` (e.g., `pi_3MtwBwLkdIwHu7ix28a3tqPa`) and a `client_secret` that is used on the frontend to securely complete the payment without exposing your secret API key.

## PaymentIntent Lifecycle

A PaymentIntent transitions through the following statuses:

```
created
  │
  ▼
requires_payment_method  ──►  canceled
  │
  ▼
requires_confirmation
  │
  ▼
requires_action  (e.g., 3D Secure authentication)
  │
  ▼
processing
  │
  ├──►  succeeded
  └──►  requires_payment_method  (if payment fails, can retry)
```

### Status Descriptions

- **`requires_payment_method`**: The PaymentIntent has been created, but no payment method has been attached. This is the initial state.
- **`requires_confirmation`**: A payment method has been attached, and the PaymentIntent is ready to be confirmed. If you use automatic confirmation (the default for client-side flows), you may not see this state.
- **`requires_action`**: The payment requires additional action from the customer, such as 3D Secure authentication. Your frontend must handle this by calling `stripe.handleNextAction()`.
- **`processing`**: The payment is being processed by the card network. This is a transient state.
- **`requires_capture`**: The payment has been authorized and is awaiting capture. Only applies when `capture_method` is set to `"manual"`.
- **`succeeded`**: The payment was successful. Funds will be available in your Stripe balance.
- **`canceled`**: The PaymentIntent was canceled and no further charges will be attempted.

## Creating a PaymentIntent

```python
import stripe

stripe.api_key = "sk_test_your_test_key_here"

payment_intent = stripe.PaymentIntent.create(
    amount=5000,              # $50.00 in cents
    currency="usd",
    payment_method_types=["card"],
    description="Order #12345",
    receipt_email="customer@example.com",
    metadata={
        "order_id": "12345",
        "product": "Premium Plan",
    },
)
```

### Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `amount` | integer | Amount in the smallest currency unit (e.g., cents for USD). Required. |
| `currency` | string | Three-letter ISO currency code (e.g., `"usd"`, `"eur"`). Required. |
| `payment_method_types` | array | Accepted payment method types. Use `["card"]` for card payments, or set `automatic_payment_methods={"enabled": True}` to let Stripe determine available methods. |
| `customer` | string | ID of an existing Customer object to associate with this payment. |
| `description` | string | An arbitrary string for your records. |
| `metadata` | hash | Key-value pairs for storing additional information. Up to 50 keys, each with a string value up to 500 characters. |
| `capture_method` | string | `"automatic"` (default) or `"manual"` for auth-and-capture flows. |
| `receipt_email` | string | Email address to send the receipt to upon successful payment. |
| `statement_descriptor` | string | Text that appears on the customer's credit card statement (max 22 characters). |

## Confirming a PaymentIntent

### Client-Side Confirmation (Recommended)

Pass the `client_secret` to your frontend and use Stripe.js:

```javascript
const { error, paymentIntent } = await stripe.confirmCardPayment(
  clientSecret,
  {
    payment_method: {
      card: cardElement,
      billing_details: {
        name: "Jenny Rosen",
      },
    },
  }
);

if (error) {
  console.error(error.message);
} else if (paymentIntent.status === "succeeded") {
  console.log("Payment succeeded!");
}
```

### Server-Side Confirmation

```python
confirmed = stripe.PaymentIntent.confirm(
    "pi_3MtwBwLkdIwHu7ix28a3tqPa",
    payment_method="pm_card_visa",
)

print(confirmed.status)  # "succeeded" or "requires_action"
```

Server-side confirmation is useful for payments where the customer is not present (e.g., recurring charges, terminal integrations).

## Manual Capture (Auth and Capture)

For businesses that need to authorize first and capture later (e.g., hotels, car rentals, or order fulfillment workflows):

```python
# Step 1: Create with manual capture
intent = stripe.PaymentIntent.create(
    amount=10000,
    currency="usd",
    payment_method_types=["card"],
    capture_method="manual",
)

# Step 2: Confirm the intent (authorization happens here)
stripe.PaymentIntent.confirm(
    intent.id,
    payment_method="pm_card_visa",
)
# Status is now "requires_capture"

# Step 3: Capture the payment (can be partial)
captured = stripe.PaymentIntent.capture(
    intent.id,
    amount_to_capture=8000,  # Capture $80 of the $100 authorization
)
```

Uncaptured PaymentIntents expire after 7 days (or 2 days for in-person payments). After expiration, the authorization is released and the PaymentIntent moves to `canceled`.

## Updating a PaymentIntent

You can update a PaymentIntent before it is confirmed:

```python
stripe.PaymentIntent.modify(
    "pi_3MtwBwLkdIwHu7ix28a3tqPa",
    amount=7500,
    metadata={"order_id": "67890"},
)
```

After confirmation, only `description`, `metadata`, `receipt_email`, and `statement_descriptor` can be updated.

## Canceling a PaymentIntent

```python
stripe.PaymentIntent.cancel(
    "pi_3MtwBwLkdIwHu7ix28a3tqPa",
    cancellation_reason="requested_by_customer",
)
```

Valid cancellation reasons: `duplicate`, `fraudulent`, `requested_by_customer`, `abandoned`.

## PaymentIntents vs. the Legacy Charges API

The Charges API was Stripe's original payment integration. The PaymentIntents API replaced it and is now the recommended approach.

| Feature | Charges API (Legacy) | PaymentIntents API |
|---------|---------------------|--------------------|
| 3D Secure / SCA support | Limited | Full, built-in |
| Payment method types | Cards only | Cards, bank debits, wallets, BNPL, and more |
| Client-side confirmation | Not supported | Supported via `client_secret` |
| Automatic retries | No | Status-based retry flow |
| Webhook-driven flow | Limited | Designed for async/webhook patterns |
| Regulatory compliance | Does not meet SCA requirements | Fully SCA-compliant |

If you are still using the Charges API, Stripe recommends migrating to PaymentIntents. The Charges API still works for simple card payments, but it cannot handle Strong Customer Authentication (SCA) requirements in the EU and other regions.

## Retrieving a PaymentIntent

```python
intent = stripe.PaymentIntent.retrieve("pi_3MtwBwLkdIwHu7ix28a3tqPa")

print(f"Status: {intent.status}")
print(f"Amount: {intent.amount}")
print(f"Currency: {intent.currency}")
print(f"Payment Method: {intent.payment_method}")
```

## Listing PaymentIntents

```python
intents = stripe.PaymentIntent.list(
    limit=10,
    created={"gte": 1672531200},  # Created after Jan 1, 2023
)

for intent in intents.auto_paging_iter():
    print(f"{intent.id}: {intent.status} - {intent.amount} {intent.currency}")
```

## Common Support Questions

**Q: A PaymentIntent is stuck in `processing`. What should I do?**
The `processing` state is typically brief (seconds to minutes). For card payments, it rarely lasts more than a few minutes. If it persists, it usually means the payment network is slow. Do not create a new PaymentIntent; wait for the webhook event (`payment_intent.succeeded` or `payment_intent.payment_failed`).

**Q: Can I change the amount of a PaymentIntent after confirmation?**
No. Once confirmed, the amount cannot be changed. You would need to cancel the PaymentIntent and create a new one with the correct amount.

**Q: What happens if the customer's browser closes during 3D Secure?**
The PaymentIntent remains in `requires_action`. The customer can return and complete authentication. The authorization hold may eventually expire depending on the card issuer.

**Q: Can I reuse a PaymentIntent that failed?**
Yes. A failed PaymentIntent returns to `requires_payment_method`. You can attach a new payment method and confirm it again.
