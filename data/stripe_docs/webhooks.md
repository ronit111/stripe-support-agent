---
title: "Webhooks"
category: "Core Concepts"
source: "https://docs.stripe.com/webhooks"
---

# Webhooks

Webhooks are HTTP callbacks that Stripe sends to your server when events occur in your Stripe account. They allow you to react to events asynchronously rather than polling the API for changes.

## Why Webhooks Matter

Many Stripe operations are asynchronous. For example:

- A payment may take time to process (especially with bank transfers or 3D Secure).
- Disputes are filed by card issuers, not triggered by your code.
- Subscription renewals happen on a schedule, not in response to a user action.
- Refunds may transition from pending to succeeded or failed over time.

Without webhooks, you would need to continuously poll the Stripe API to detect these changes. Webhooks solve this by pushing event notifications to your server in real time.

## Webhook Endpoints

A webhook endpoint is a URL on your server that receives POST requests from Stripe. You configure endpoints in the Stripe Dashboard (**Developers > Webhooks**) or via the API:

```python
import stripe

stripe.api_key = "sk_test_..."

# Create a webhook endpoint via the API
endpoint = stripe.WebhookEndpoint.create(
    url="https://yoursite.com/stripe/webhook",
    enabled_events=[
        "payment_intent.succeeded",
        "payment_intent.payment_failed",
        "customer.subscription.created",
        "customer.subscription.deleted",
        "invoice.payment_failed",
        "charge.dispute.created",
    ],
)

print(endpoint.id)      # we_...
print(endpoint.secret)  # whsec_...  (used for signature verification)
```

You can subscribe to specific event types or use `["*"]` to receive all events. Subscribing only to the events you need reduces unnecessary traffic and processing.

## Event Object Structure

Every webhook delivery contains an Event object with this structure:

```json
{
  "id": "evt_1234567890",
  "object": "event",
  "api_version": "2024-12-18.acacia",
  "created": 1700000000,
  "type": "payment_intent.succeeded",
  "livemode": true,
  "pending_webhooks": 1,
  "request": {
    "id": "req_abc123",
    "idempotency_key": "key_xyz"
  },
  "data": {
    "object": {
      "id": "pi_1234567890",
      "object": "payment_intent",
      "amount": 2000,
      "currency": "usd",
      "status": "succeeded"
    },
    "previous_attributes": {
      "status": "processing"
    }
  }
}
```

Key fields:

| Field | Description |
|-------|-------------|
| `id` | Unique event identifier. Use this to deduplicate events. |
| `type` | The event type (e.g., `payment_intent.succeeded`). |
| `data.object` | The Stripe object that triggered the event, in its current state. |
| `data.previous_attributes` | For update events, the attributes that changed (previous values). |
| `livemode` | Whether this event occurred in live mode or test mode. |
| `created` | Unix timestamp of when the event was created. |
| `api_version` | The API version used to render the event's data object. |

## Webhook Signatures and Verification

Stripe signs every webhook event with a signature to ensure it was sent by Stripe and not a malicious third party. You must verify this signature before processing any webhook event.

Each webhook endpoint has a signing secret (starts with `whsec_`). Stripe includes a `Stripe-Signature` header with each delivery that contains a timestamp and one or more signatures.

### Signature Verification in Python

```python
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)

# Your webhook endpoint's signing secret
endpoint_secret = "whsec_your_signing_secret_here"

@app.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        # Invalid payload
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature -- not from Stripe
        return jsonify({"error": "Invalid signature"}), 400

    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        print(f"Payment succeeded: {payment_intent['id']}")
        # Fulfill the order, send confirmation email, etc.

    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        print(f"Payment failed: {payment_intent['id']}")
        # Notify the customer, retry logic, etc.

    elif event["type"] == "charge.dispute.created":
        dispute = event["data"]["object"]
        print(f"Dispute created: {dispute['id']}")
        # Alert your team, begin evidence collection

    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        print(f"Invoice payment failed: {invoice['id']}")
        # Dunning logic: notify customer, retry payment

    # Return 200 to acknowledge receipt
    return jsonify({"status": "success"}), 200
```

### Important: Always return a 2xx status code promptly. If your endpoint returns a non-2xx status or times out (after 20 seconds), Stripe considers the delivery failed and will retry.

## Handling Webhooks Securely

1. **Always verify signatures.** Never process a webhook without verifying the `Stripe-Signature` header. This prevents attackers from sending fake events to your endpoint.

2. **Use the raw request body.** Signature verification requires the raw request body, not a parsed JSON object. Parsing the body before verification can alter whitespace or encoding and cause verification to fail.

3. **Process events idempotently.** Stripe may deliver the same event more than once. Use the event `id` to deduplicate and ensure processing the same event twice does not cause duplicate side effects (e.g., fulfilling an order twice).

4. **Respond quickly.** Return a 200 response as soon as you receive the event. Perform heavy processing asynchronously (e.g., using a task queue). If your endpoint takes too long to respond, Stripe may mark the delivery as failed and retry.

5. **Use HTTPS.** Webhook endpoints must use HTTPS in production. Stripe will not send events to HTTP URLs in live mode.

## Retry Behavior

When a webhook delivery fails (non-2xx response or timeout), Stripe retries with exponential backoff:

- Stripe retries up to **3 days** after the initial delivery attempt.
- Retries occur at increasing intervals: roughly 1 hour, then 2 hours, then 4 hours, and so on.
- After 3 days of consecutive failures, Stripe stops retrying for that specific event.
- If your endpoint fails consistently, Stripe may disable it and send you an email notification.

You can monitor delivery attempts and failures in the Dashboard under **Developers > Webhooks > [endpoint] > Attempts**.

## Common Webhook Patterns

### Subscription Lifecycle

```
customer.subscription.created      -> New subscription activated
customer.subscription.updated      -> Plan changed, status changed, etc.
customer.subscription.deleted      -> Subscription canceled
invoice.created                    -> New invoice generated for billing cycle
invoice.finalized                  -> Invoice finalized and ready for payment
invoice.paid                       -> Invoice paid successfully
invoice.payment_failed             -> Invoice payment attempt failed
```

### Payment Lifecycle

```
payment_intent.created             -> PaymentIntent created
payment_intent.requires_action     -> Customer needs to authenticate (3DS)
payment_intent.processing          -> Payment is being processed
payment_intent.succeeded           -> Payment completed successfully
payment_intent.payment_failed      -> Payment attempt failed
```

### Dispute Lifecycle

```
charge.dispute.created             -> Dispute filed
charge.dispute.updated             -> Dispute status changed
charge.dispute.funds_withdrawn     -> Funds removed from your balance
charge.dispute.funds_reinstated    -> Funds returned (dispute won)
charge.dispute.closed              -> Dispute resolved
```

## Testing with the Stripe CLI

The Stripe CLI lets you test webhooks locally during development:

```bash
# Install the Stripe CLI and login
stripe login

# Forward events to your local server
stripe listen --forward-to localhost:5000/stripe/webhook

# In another terminal, trigger a test event
stripe trigger payment_intent.succeeded

# Trigger a specific event type
stripe trigger customer.subscription.created
```

The CLI provides a temporary webhook signing secret (displayed when you run `stripe listen`) that you use in your local application for signature verification.

## Common Event Types

Here are the most commonly used webhook event types:

| Event Type | When It Fires |
|-----------|---------------|
| `payment_intent.succeeded` | A payment completed successfully. |
| `payment_intent.payment_failed` | A payment attempt failed. |
| `charge.refunded` | A charge was refunded (full or partial). |
| `charge.dispute.created` | A dispute was filed against a charge. |
| `customer.subscription.created` | A new subscription was created. |
| `customer.subscription.updated` | A subscription was modified. |
| `customer.subscription.deleted` | A subscription was canceled. |
| `invoice.paid` | An invoice was successfully paid. |
| `invoice.payment_failed` | An invoice payment attempt failed. |
| `customer.created` | A new customer was created. |
| `customer.updated` | A customer was modified. |
| `checkout.session.completed` | A Checkout Session was completed. |

## Troubleshooting Webhooks

**Events not arriving:**
Check that your endpoint URL is correct, HTTPS is configured, and your server is reachable from the internet. Verify in the Dashboard that the endpoint is enabled and subscribed to the expected event types.

**Signature verification failing:**
Ensure you are using the raw request body (not parsed JSON) and the correct signing secret for the specific endpoint. Each endpoint has its own unique signing secret.

**Duplicate events:**
Stripe may send the same event multiple times. Always deduplicate using the event `id` and implement idempotent processing.
