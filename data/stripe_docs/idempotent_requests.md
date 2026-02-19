---
title: "Idempotent Requests"
category: "Core Concepts"
source: "https://docs.stripe.com/api/idempotent-requests"
---

# Idempotent Requests

Idempotency is a property of API requests that ensures performing the same operation multiple times produces the same result as performing it once. In payment processing, idempotency prevents duplicate charges, refunds, or other operations caused by network failures, timeouts, or retries.

## Why Idempotency Matters for Payments

Payment processing involves real money, and network communication is inherently unreliable. Consider this scenario:

1. Your server sends a request to Stripe to create a $100 charge.
2. Stripe processes the charge and sends a response.
3. The response is lost due to a network issue. Your server never receives it.
4. Your server retries the request, not knowing the first one succeeded.
5. Without idempotency, Stripe would create a second $100 charge, and the customer is billed $200.

Idempotency keys solve this problem. When you include an idempotency key with a request, Stripe checks if it has already processed a request with that key. If it has, Stripe returns the original response without processing the request again.

## How Idempotency Keys Work

You include an idempotency key by setting the `Idempotency-Key` header on your API request. The Stripe Python library provides a convenient parameter for this:

```python
import stripe

stripe.api_key = "sk_test_..."

# Create a PaymentIntent with an idempotency key
payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    customer="cus_1234567890",
    payment_method="pm_1234567890",
    idempotency_key="order_12345_payment_attempt_1",
)
```

### What Happens with Duplicate Requests

When Stripe receives a request with an idempotency key:

1. **First request**: Stripe processes the request normally, stores the result, and associates it with the idempotency key.
2. **Subsequent requests with the same key**: Stripe returns the stored result from the first request without re-processing. This is true regardless of how many times the duplicate request is sent.

```python
import stripe

stripe.api_key = "sk_test_..."

# First call: creates the refund
refund = stripe.Refund.create(
    payment_intent="pi_1234567890",
    amount=500,
    idempotency_key="refund_order_12345",
)
print(refund.id)  # re_abc123

# Second call with same key: returns the same refund, does NOT create a new one
refund_again = stripe.Refund.create(
    payment_intent="pi_1234567890",
    amount=500,
    idempotency_key="refund_order_12345",
)
print(refund_again.id)  # re_abc123 (same as above)
```

## Key Expiry

Idempotency keys expire after **24 hours**. After expiration:

- Stripe no longer has the stored result for that key.
- A new request with the same key will be processed as a new request.
- The 24-hour window starts from the time of the original request.

This expiration window is designed to handle retry scenarios (which typically occur within minutes or hours) while allowing key reuse after a reasonable period.

## Generating Idempotency Keys

The idempotency key is a string of up to 255 characters. The key should uniquely identify the specific operation you are performing, not just the request. Best practices for key generation:

### Use UUIDs

```python
import uuid

# Generate a UUID v4 for each unique operation
idempotency_key = str(uuid.uuid4())

stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    idempotency_key=idempotency_key,
)
```

### Use Deterministic Keys Based on Business Logic

For operations tied to a specific business action, derive the key from the action itself. This ensures that retries of the same action naturally use the same key:

```python
# Deterministic key based on order ID and action
order_id = "order_12345"
idempotency_key = f"{order_id}_charge"

stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    idempotency_key=idempotency_key,
)

# For a refund on the same order
refund_key = f"{order_id}_refund"
stripe.Refund.create(
    payment_intent="pi_1234567890",
    idempotency_key=refund_key,
)
```

Deterministic keys are generally preferred over random UUIDs because they naturally prevent duplicates even across separate server instances or process restarts. If your server crashes and restarts, a retry with a deterministic key will correctly deduplicate, whereas a new UUID would not.

## When to Use Idempotency Keys

### Always use idempotency keys for:

- **Creating charges and PaymentIntents**: The most critical use case. Duplicate charges directly cost your customers money.
- **Creating refunds**: A duplicate refund returns money twice.
- **Creating transfers**: Duplicate transfers send money to a connected account twice.
- **Creating subscriptions**: Duplicate subscriptions result in double-billing.
- **Any mutating (POST) request**: If the operation has side effects, idempotency keys protect against duplicates.

### Not needed for:

- **GET requests**: Read operations are naturally idempotent. Calling `stripe.Customer.retrieve()` multiple times always returns the current state.
- **DELETE requests**: Deleting the same resource twice is usually safe (the second call returns a "not found" or "already deleted" result).
- **List operations**: Listing resources does not modify state.

## Handling Idempotency Errors

### Mismatched Parameters

If you send a request with the same idempotency key but different parameters, Stripe returns a `400` error:

```python
try:
    # First request: $20 charge
    stripe.PaymentIntent.create(
        amount=2000,
        currency="usd",
        idempotency_key="key_123",
    )

    # Second request with same key but different amount: ERROR
    stripe.PaymentIntent.create(
        amount=3000,  # Different amount!
        currency="usd",
        idempotency_key="key_123",
    )
except stripe.error.InvalidRequestError as e:
    print(e)  # "Keys for idempotent requests can only be used with the same parameters..."
```

This is a safety feature. Stripe prevents you from accidentally reusing a key for a different operation.

### Concurrent Requests

If two requests with the same idempotency key arrive simultaneously, Stripe processes one and returns a `409 Conflict` for the other. The client should retry after a brief delay.

```python
import stripe
import time

def create_payment_with_retry(amount, idempotency_key, max_retries=3):
    for attempt in range(max_retries):
        try:
            return stripe.PaymentIntent.create(
                amount=amount,
                currency="usd",
                idempotency_key=idempotency_key,
            )
        except stripe.error.APIError as e:
            if e.http_status == 409 and attempt < max_retries - 1:
                time.sleep(1)  # Wait and retry
                continue
            raise
```

## Common Pitfalls

### 1. Using Random Keys without Storing Them

If you generate a random UUID and do not store it, you cannot retry with the same key if the response is lost. Store the key alongside the operation in your database before making the API call.

```python
import uuid

# Store the key BEFORE making the API call
idempotency_key = str(uuid.uuid4())
save_to_database(order_id="12345", idempotency_key=idempotency_key, status="pending")

# Now make the API call
try:
    payment_intent = stripe.PaymentIntent.create(
        amount=2000,
        currency="usd",
        idempotency_key=idempotency_key,
    )
    update_database(order_id="12345", status="succeeded", stripe_id=payment_intent.id)
except Exception:
    # On retry, retrieve the stored key and use it again
    pass
```

### 2. Reusing Keys Across Different Operations

Each distinct operation should have its own idempotency key. Do not reuse a key from a charge for a refund, or from one customer's payment for another's.

### 3. Ignoring the 24-Hour Expiry

If your retry logic spans more than 24 hours (unlikely but possible in some batch processing systems), the idempotency key will have expired and the request will be processed as new. Design your retry windows to complete well within 24 hours.

### 4. Not Using Idempotency Keys at All

The most common pitfall is simply not using idempotency keys. If your retry logic or queue system can deliver the same request more than once, you need idempotency keys. This includes:

- Message queues with at-least-once delivery (SQS, RabbitMQ, Kafka).
- Webhook handlers that trigger API calls (webhooks can be delivered more than once).
- User-facing forms that can be submitted multiple times (double-click).

## Idempotency with Stripe Connect

When using Stripe Connect, idempotency keys are scoped to the account making the request. A key used on your platform account is independent of the same key used on a connected account (via the `Stripe-Account` header).

```python
# Platform account: key "abc" is independent
stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    idempotency_key="abc",
)

# Connected account: same key "abc" is treated as a separate key
stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    idempotency_key="abc",
    stripe_account="acct_connected_123",
)
```
