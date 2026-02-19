---
title: "Error Handling"
category: "Payments"
source: "https://docs.stripe.com/error-handling"
---

# Error Handling

## Overview

When working with the Stripe API, errors are inevitable. Cards get declined, API requests contain invalid parameters, network issues occur, and rate limits are hit. Proper error handling ensures your integration gracefully manages these failures and provides clear feedback to your users.

Stripe errors are returned as JSON objects with a consistent structure, and the Stripe Python library raises specific exception types for each error category.

## Error Object Structure

Every Stripe error includes these fields:

```json
{
  "error": {
    "type": "card_error",
    "code": "card_declined",
    "decline_code": "insufficient_funds",
    "message": "Your card has insufficient funds.",
    "param": null,
    "charge": "ch_1MoC4d..."
  }
}
```

| Field | Description |
|-------|-------------|
| `type` | The category of error (see Error Types below) |
| `code` | A short string identifying the specific error |
| `decline_code` | For card declines, the specific reason from the issuer |
| `message` | A human-readable description of the error |
| `param` | The parameter related to the error (for invalid request errors) |
| `charge` | The Charge ID if one was created during the failed attempt |
| `payment_intent` | The PaymentIntent if one is associated with the error |
| `doc_url` | A link to Stripe's documentation about this error |

## Error Types

### `card_error`
The customer's card was declined or could not be processed. These are the most common errors in payment flows. The customer should be prompted to use a different payment method or contact their bank.

### `invalid_request_error`
The API request had invalid parameters, was missing required parameters, or was otherwise malformed. This typically indicates a bug in your code. Examples: providing a negative amount, using an invalid currency code, or referencing a non-existent object ID.

### `authentication_error`
The API key used is invalid, expired, or has insufficient permissions. Check that you are using the correct key (test vs. live) and that it has not been revoked.

### `api_error`
An unexpected error occurred on Stripe's side. These are rare but can happen. Your code should retry the request with exponential backoff.

### `rate_limit_error`
Too many API requests hit Stripe in a short time. Implement exponential backoff and reduce request frequency. The default rate limit is 100 read requests per second and 100 write requests per second in live mode.

### `idempotency_error`
An idempotency key was reused with different request parameters. Each unique request should use a unique idempotency key, or the same key must be used with identical parameters.

### `api_connection_error`
A network problem prevented the request from reaching Stripe. This could be a DNS issue, timeout, or connectivity problem. Retry the request.

## Common Error Codes

### Card Decline Codes

| Code | Decline Code | Description | Customer Message |
|------|-------------|-------------|------------------|
| `card_declined` | `insufficient_funds` | The card has insufficient funds | "Your card has insufficient funds. Please try a different card." |
| `card_declined` | `lost_card` | The card has been reported lost | "Your card was declined. Please contact your bank." |
| `card_declined` | `stolen_card` | The card has been reported stolen | "Your card was declined. Please contact your bank." |
| `card_declined` | `generic_decline` | The card was declined for an unspecified reason | "Your card was declined. Please try a different card or contact your bank." |
| `card_declined` | `do_not_honor` | The issuing bank declined without a specific reason | "Your card was declined. Please contact your bank." |
| `card_declined` | `fraudulent` | The issuer suspects fraud | "Your card was declined. Please contact your bank." |
| `card_declined` | `transaction_not_allowed` | The card does not support this type of transaction | "Your card does not support this type of purchase." |
| `card_declined` | `card_not_supported` | The card does not support this type of purchase | "Your card does not support this type of purchase." |

### Other Common Error Codes

| Code | Type | Description |
|------|------|-------------|
| `expired_card` | `card_error` | The card has expired |
| `incorrect_cvc` | `card_error` | The CVC number is incorrect |
| `incorrect_number` | `card_error` | The card number is incorrect |
| `processing_error` | `card_error` | A processing error occurred (retry may work) |
| `amount_too_small` | `invalid_request_error` | The charge amount is below the minimum |
| `amount_too_large` | `invalid_request_error` | The charge amount exceeds the maximum |
| `balance_insufficient` | `invalid_request_error` | Account balance is insufficient for this payout |
| `resource_missing` | `invalid_request_error` | The referenced resource (customer, price, etc.) does not exist |
| `parameter_invalid_integer` | `invalid_request_error` | A parameter expected an integer but received something else |
| `payment_intent_unexpected_state` | `invalid_request_error` | The PaymentIntent is in a state that does not allow the requested operation |

## Handling Errors in Python

The Stripe Python library raises specific exception classes:

```python
import stripe

stripe.api_key = "sk_test_your_test_key_here"

try:
    payment_intent = stripe.PaymentIntent.create(
        amount=2000,
        currency="usd",
        payment_method="pm_card_visa",
        confirm=True,
    )
    print(f"Payment succeeded: {payment_intent.id}")

except stripe.error.CardError as e:
    # Card was declined
    err = e.error
    print(f"Card error: {err.code}")
    print(f"Decline code: {err.decline_code}")
    print(f"Message: {err.message}")
    # Show a user-friendly message and prompt for a different card

except stripe.error.InvalidRequestError as e:
    # Invalid parameters — likely a bug in your code
    print(f"Invalid request: {e.user_message}")
    # Log this error and fix the code

except stripe.error.AuthenticationError as e:
    # API key is invalid
    print(f"Authentication failed: {e.user_message}")
    # Check your API key configuration

except stripe.error.RateLimitError as e:
    # Too many requests
    print(f"Rate limited: {e.user_message}")
    # Implement backoff and retry

except stripe.error.APIConnectionError as e:
    # Network error
    print(f"Network error: {e.user_message}")
    # Retry the request

except stripe.error.APIError as e:
    # Stripe server error
    print(f"Stripe API error: {e.user_message}")
    # Retry with exponential backoff

except Exception as e:
    # Unexpected error
    print(f"Unexpected error: {str(e)}")
```

## Retry Strategies

### Exponential Backoff

For transient errors (`api_error`, `rate_limit_error`, `api_connection_error`), implement exponential backoff:

```python
import time
import random
import stripe

def create_payment_with_retry(amount, currency, max_retries=3):
    for attempt in range(max_retries):
        try:
            return stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method_types=["card"],
            )
        except (stripe.error.APIError,
                stripe.error.RateLimitError,
                stripe.error.APIConnectionError) as e:
            if attempt == max_retries - 1:
                raise  # Give up after max retries

            # Exponential backoff with jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Retry {attempt + 1}/{max_retries} in {wait_time:.1f}s: {e}")
            time.sleep(wait_time)

        except stripe.error.CardError:
            raise  # Don't retry card errors — they won't succeed on retry
        except stripe.error.InvalidRequestError:
            raise  # Don't retry bad requests — fix the code instead
```

### Idempotency Keys

Use idempotency keys to safely retry requests without risking duplicate charges:

```python
import uuid

idempotency_key = str(uuid.uuid4())

payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    payment_method_types=["card"],
    idempotency_key=idempotency_key,
)

# If you retry with the same key, Stripe returns the same result
# instead of creating a duplicate PaymentIntent
```

Idempotency keys expire after 24 hours. They are especially important for create and confirm operations where a network timeout could leave you unsure whether the request succeeded.

## Webhook Error Handling

When processing webhooks, always return a `2xx` status code promptly. If you return an error status, Stripe will retry the webhook delivery:

```python
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        event = stripe.Webhook.construct_event(
            request.get_data(),
            request.headers["Stripe-Signature"],
            endpoint_secret,
        )
    except ValueError:
        # Invalid payload
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature — possible tampering
        return "Invalid signature", 400

    # Process the event
    try:
        handle_event(event)
    except Exception as e:
        # Log the error but still return 200 to prevent retries
        # Process failed events asynchronously
        log_failed_event(event, e)

    return "", 200
```

## Common Support Questions

**Q: The customer's card was declined with `generic_decline`. What does that mean?**
A `generic_decline` means the issuing bank declined the transaction without providing a specific reason. The customer should contact their bank for details, or try a different card.

**Q: I am getting `authentication_error`. What is wrong?**
This means your API key is invalid. Check that you are using the correct key for the environment (test keys start with `sk_test_`, live keys start with `sk_live_`). Also verify the key has not been rolled or revoked in the Dashboard.

**Q: Should I show the Stripe error message directly to customers?**
For `card_error` types, the `message` field is generally safe to display to customers. For other error types (`invalid_request_error`, `api_error`, etc.), show a generic message like "Something went wrong. Please try again." and log the detailed error for debugging.

**Q: How do I handle `payment_intent_unexpected_state`?**
This occurs when you try to perform an action on a PaymentIntent that is not in the correct state. For example, trying to confirm a PaymentIntent that has already succeeded. Retrieve the PaymentIntent first to check its current status before performing operations.
