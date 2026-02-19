---
title: "Stripe Payments Overview"
category: "Payments"
source: "https://docs.stripe.com/payments"
---

# Stripe Payments Overview

## How Stripe Payments Work

Stripe provides a complete payments platform that allows businesses to accept payments online and in person. At its core, Stripe acts as an intermediary between the customer's payment method (such as a credit card or bank account) and the business's bank account, handling authorization, capture, settlement, and fund transfer.

### The Payment Flow

A typical Stripe payment follows this sequence:

1. **Customer initiates payment**: The customer enters their payment details on your website or app.
2. **PaymentIntent created**: Your server creates a PaymentIntent object, which represents a single attempt to collect payment from the customer.
3. **Payment method collected**: The customer's payment details are securely tokenized on the client side using Stripe.js or Stripe Elements.
4. **Confirmation**: The PaymentIntent is confirmed with the payment method, triggering Stripe to attempt the charge.
5. **Authorization**: Stripe communicates with the card network (Visa, Mastercard, etc.) and the issuing bank to authorize the transaction.
6. **Charge created**: Upon successful authorization, a Charge object is created and attached to the PaymentIntent.
7. **Settlement**: Funds are settled into your Stripe balance and eventually paid out to your bank account.

### Key Concepts

#### PaymentIntent

The `PaymentIntent` object is the core resource for accepting payments. It tracks the lifecycle of a payment from creation to completion. Each PaymentIntent has a `status` field that indicates where it is in the payment process.

#### Payment Methods

A `PaymentMethod` object represents a customer's payment instrument. This can be a card, a bank account, a digital wallet, or any other supported payment type. Payment methods can be used once or saved for future payments.

#### Customers

The `Customer` object lets you store payment methods and track payments for a specific person or business. Associating payments with customers enables features like saved cards, subscription billing, and payment history.

#### Charges

A `Charge` represents a single attempt to move money. When a PaymentIntent succeeds, it creates a Charge. You can refund charges partially or fully.

## Payment States

A PaymentIntent moves through several states during its lifecycle:

| Status | Description |
|--------|-------------|
| `requires_payment_method` | Created but no payment method attached yet |
| `requires_confirmation` | Payment method attached, waiting for confirmation |
| `requires_action` | Additional authentication needed (e.g., 3D Secure) |
| `processing` | Payment is being processed by the network |
| `requires_capture` | Authorized but not yet captured (manual capture flow) |
| `succeeded` | Payment completed successfully |
| `canceled` | Payment was canceled before completion |

## Basic Code Example

Here is how to create a PaymentIntent using the Stripe Python library:

```python
import stripe

stripe.api_key = "sk_test_your_test_key_here"

# Create a PaymentIntent
payment_intent = stripe.PaymentIntent.create(
    amount=2000,          # Amount in cents ($20.00)
    currency="usd",
    payment_method_types=["card"],
    metadata={
        "order_id": "order_12345",
    },
)

print(f"PaymentIntent created: {payment_intent.id}")
print(f"Client secret: {payment_intent.client_secret}")
```

The `client_secret` is passed to the frontend so Stripe.js can confirm the payment on the client side without exposing your secret key.

### Confirming on the Server Side

For server-side confirmation (useful for terminal/API-only flows):

```python
# Confirm the PaymentIntent with a payment method
confirmed_intent = stripe.PaymentIntent.confirm(
    payment_intent.id,
    payment_method="pm_card_visa",
)

print(f"Status: {confirmed_intent.status}")
# Output: Status: succeeded
```

## Integration Approaches

Stripe offers several ways to accept payments, depending on your needs:

### Stripe Checkout (Hosted)
A pre-built, Stripe-hosted payment page. Lowest integration effort. Supports one-time payments and subscriptions. Handles compliance, localization, and mobile optimization automatically.

### Stripe Elements (Embedded)
Pre-built UI components you embed directly in your website. Gives you more control over the look and feel while Stripe handles the security-sensitive parts.

### Payment Links (No-Code)
Shareable URLs that open a Stripe-hosted payment page. No coding required. Ideal for invoices, social media sales, or quick payment collection.

### Direct API
Full control over the payment flow using Stripe's API directly. Requires the most development effort but offers maximum flexibility.

## Webhooks

Stripe uses webhooks to notify your application about events that happen asynchronously, such as successful payments, failed charges, or disputes. This is the recommended way to track payment status rather than polling the API.

Common payment-related webhook events:

- `payment_intent.succeeded` - Payment completed successfully
- `payment_intent.payment_failed` - Payment attempt failed
- `charge.refunded` - A charge was refunded
- `charge.dispute.created` - A customer disputed a charge

```python
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)
endpoint_secret = "whsec_your_webhook_secret"

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return jsonify(success=False), 400
    except stripe.error.SignatureVerificationError:
        return jsonify(success=False), 400

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        print(f"Payment succeeded: {payment_intent['id']}")
        # Fulfill the order here

    return jsonify(success=True), 200
```

## Common Support Questions

**Q: How long does it take for payments to reach my bank account?**
Standard payouts arrive in 2 business days in the US. This varies by country. You can check payout schedules in the Stripe Dashboard under Settings > Payouts.

**Q: What is the difference between authorization and capture?**
Authorization places a hold on the customer's funds. Capture actually moves the money. By default, Stripe authorizes and captures in one step. You can separate these by setting `capture_method="manual"` on the PaymentIntent.

**Q: Are payments PCI compliant?**
Yes. When you use Stripe.js, Elements, or Checkout, card details are sent directly to Stripe's servers and never touch your backend. This significantly reduces your PCI compliance scope (SAQ A or SAQ A-EP depending on integration).

**Q: What happens if a payment fails?**
The PaymentIntent status changes to `requires_payment_method`. You can prompt the customer to try a different payment method. The specific failure reason is available in the `last_payment_error` field of the PaymentIntent.
