---
title: "Billing Webhooks"
category: "Billing"
source: "https://docs.stripe.com/billing/subscriptions/webhooks"
---

# Billing Webhooks

Webhooks are HTTP callbacks that Stripe sends to your server when events occur in your account. For billing, webhooks are essential for tracking payment outcomes, subscription lifecycle changes, and invoice status updates. Relying solely on API responses is insufficient because many billing events happen asynchronously (e.g., failed payment retries, subscription renewals).

## Key Billing Webhook Events

### Invoice Events

| Event | When It Fires | What To Do |
|-------|---------------|------------|
| `invoice.created` | A new invoice is created (for subscriptions, ~1 hour before payment attempt). | Add extra line items, apply credits, or modify the invoice before finalization. |
| `invoice.finalized` | The invoice is finalized and can no longer be edited. | Record the finalized invoice in your system. |
| `invoice.paid` | Payment was successfully collected. | Activate or renew the customer's service. This is the primary "success" event for subscriptions. |
| `invoice.payment_failed` | A payment attempt failed. | Notify the customer, prompt them to update their payment method. |
| `invoice.payment_action_required` | The payment requires customer action (e.g., 3D Secure authentication). | Send the customer a link to complete authentication. |
| `invoice.upcoming` | Fires ~3 days before the next subscription invoice is created. | Add pending invoice items, send renewal reminders, or check for issues. |
| `invoice.voided` | The invoice was voided. | Update your records. Stop any fulfillment associated with this invoice. |
| `invoice.marked_uncollectible` | The invoice was marked as uncollectible. | Update your records. Consider suspending service. |

### Subscription Events

| Event | When It Fires | What To Do |
|-------|---------------|------------|
| `customer.subscription.created` | A new subscription is created. | Provision the customer's service. |
| `customer.subscription.updated` | A subscription is modified (plan change, status change, cancellation scheduled). | Check the `status` and `cancel_at_period_end` fields. Update your application state accordingly. |
| `customer.subscription.deleted` | A subscription is canceled and has ended. | Revoke access to the service. |
| `customer.subscription.trial_will_end` | The trial period will end in 3 days. | Send a reminder to the customer. Prompt them to add a payment method if they haven't. |
| `customer.subscription.paused` | The subscription has been paused. | Suspend the customer's access. |
| `customer.subscription.resumed` | The subscription has been resumed. | Restore the customer's access. |
| `customer.subscription.pending_update_applied` | A pending subscription update was applied. | Update your records with the new subscription details. |
| `customer.subscription.pending_update_expired` | A pending subscription update expired without being applied. | Notify the customer that the change did not go through. |

### Payment Method Events

| Event | When It Fires |
|-------|---------------|
| `payment_method.attached` | A payment method was attached to a customer. |
| `payment_method.detached` | A payment method was detached from a customer. |
| `customer.source.expiring` | A customer's card will expire at the end of the month. |

## Handling Payment Failures

When a subscription payment fails, Stripe enters a **dunning** process: a series of automatic retries over a configurable period. Understanding and handling payment failures correctly is critical.

### The Payment Failure Flow

```
invoice.payment_failed (1st attempt)
    ↓
Stripe waits (retry schedule)
    ↓
invoice.payment_failed (2nd attempt)
    ↓
Stripe waits (retry schedule)
    ↓
invoice.payment_failed (3rd attempt)
    ↓
... up to configured number of retries
    ↓
Subscription status changes based on your settings
```

### Dunning Configuration

Configure retry behavior in the Stripe Dashboard under Settings > Billing > Subscriptions and emails > Manage failed payments. You control:

- **Number of retries**: How many times Stripe retries the payment (up to 8 attempts over the dunning period).
- **Retry schedule**: The timing between retries (e.g., 1, 3, 5, 7 days after failure).
- **Final action**: What happens after all retries are exhausted:
  - **Cancel the subscription**: Moves the subscription to `canceled`.
  - **Mark the invoice as uncollectible**: Leaves the subscription active but stops collection attempts.
  - **Leave the subscription as past_due**: Keeps retrying indefinitely (not recommended).

### Smart Retries

Stripe's Smart Retries feature uses machine learning to determine the optimal retry timing for each failed payment, rather than following a fixed schedule. This is enabled by default and typically recovers more revenue than manual retry schedules.

### Recommended Failure Handling Pattern

```python
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, "whsec_YOUR_WEBHOOK_SECRET"
        )
    except ValueError:
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({"error": "Invalid signature"}), 400

    if event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        customer_id = invoice["customer"]
        attempt_count = invoice["attempt_count"]

        if attempt_count == 1:
            # First failure: send a gentle reminder
            send_payment_failed_email(customer_id, "gentle_reminder")
        elif attempt_count == 2:
            # Second failure: more urgent notice
            send_payment_failed_email(customer_id, "urgent_reminder")
        elif attempt_count >= 3:
            # Final attempts: warn about service suspension
            send_payment_failed_email(customer_id, "final_warning")

    elif event["type"] == "invoice.paid":
        invoice = event["data"]["object"]
        customer_id = invoice["customer"]
        subscription_id = invoice["subscription"]

        # Payment succeeded - ensure service is active
        activate_service(customer_id, subscription_id)

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]

        # Subscription is fully canceled - revoke access
        revoke_service(customer_id, subscription["id"])

    return jsonify({"status": "success"}), 200
```

## Subscription State Change Handling

The `customer.subscription.updated` event fires for many different changes. Inspect the `previous_attributes` field to understand what changed.

```python
if event["type"] == "customer.subscription.updated":
    subscription = event["data"]["object"]
    previous = event["data"].get("previous_attributes", {})

    # Check for status change
    if "status" in previous:
        old_status = previous["status"]
        new_status = subscription["status"]
        handle_status_change(subscription["id"], old_status, new_status)

    # Check for plan change
    if "items" in previous:
        handle_plan_change(subscription)

    # Check for cancellation scheduled
    if "cancel_at_period_end" in previous:
        if subscription["cancel_at_period_end"]:
            # Customer scheduled cancellation
            send_cancellation_scheduled_email(
                subscription["customer"],
                subscription["current_period_end"],
            )
        else:
            # Customer reversed their cancellation
            send_cancellation_reversed_email(subscription["customer"])
```

## Webhook Handling Best Practices

### 1. Verify Webhook Signatures

Always verify the `Stripe-Signature` header to confirm the webhook came from Stripe and was not tampered with.

```python
endpoint_secret = "whsec_YOUR_WEBHOOK_SECRET"

try:
    event = stripe.Webhook.construct_event(
        payload, sig_header, endpoint_secret
    )
except stripe.error.SignatureVerificationError:
    return "Invalid signature", 400
```

### 2. Handle Events Idempotently

Stripe may send the same event more than once. Use the event ID (`event["id"]`) to deduplicate.

```python
event_id = event["id"]

if already_processed(event_id):
    return jsonify({"status": "already processed"}), 200

process_event(event)
mark_as_processed(event_id)
```

### 3. Respond Quickly

Return a 2xx response within a few seconds. If you need to do heavy processing, queue the event and process it asynchronously.

```python
@app.route("/webhook", methods=["POST"])
def webhook():
    event = verify_and_parse(request)
    # Queue for async processing
    task_queue.enqueue(process_stripe_event, event)
    return jsonify({"status": "received"}), 200
```

### 4. Handle Retries Gracefully

If your endpoint returns a non-2xx status, Stripe retries the webhook with exponential backoff for up to 3 days. Make sure your handler is idempotent so retries don't cause duplicate actions.

### 5. Use the Correct Event Ordering

Events may arrive out of order. Don't assume `invoice.paid` arrives after `invoice.created`. Use the object's state (e.g., `subscription.status`) rather than relying on event sequence.

## Minimum Recommended Webhook Events

For a basic subscription billing integration, handle at minimum:

1. **`invoice.paid`** - Confirm service activation/renewal.
2. **`invoice.payment_failed`** - Notify customers and handle dunning.
3. **`customer.subscription.updated`** - Track plan changes and cancellation scheduling.
4. **`customer.subscription.deleted`** - Revoke access when a subscription fully ends.
5. **`customer.subscription.trial_will_end`** - Send trial ending reminders.

## Testing Webhooks

### Stripe CLI

The Stripe CLI can forward webhook events to your local development server:

```bash
stripe listen --forward-to localhost:4242/webhook
```

### Trigger Test Events

```bash
stripe trigger invoice.payment_failed
stripe trigger customer.subscription.updated
```

### Dashboard

You can also send test webhook events from the Stripe Dashboard under Developers > Webhooks > your endpoint > Send test webhook.

## Common Support Scenarios

**Webhooks not arriving**: Check the endpoint URL is correct and publicly accessible. Review the webhook logs in the Dashboard under Developers > Webhooks. Look for failed delivery attempts and their HTTP response codes.

**Duplicate events**: Stripe guarantees at-least-once delivery, not exactly-once. Implement idempotent event handling using the event ID.

**Events arriving out of order**: Use the object state from the event payload rather than assuming events arrive sequentially. Check `subscription.status` directly rather than inferring it from event order.

**Subscription canceled but webhook not received**: The `customer.subscription.deleted` event only fires when the subscription is actually terminated. If `cancel_at_period_end=True`, the event fires at the end of the period, not when the cancellation is scheduled. Listen for `customer.subscription.updated` to catch the scheduling.

**Payment failed but subscription still active**: This is expected behavior during dunning. The subscription moves to `past_due` during retries. It only moves to `canceled` or `unpaid` after all retries are exhausted (based on your dunning settings).
