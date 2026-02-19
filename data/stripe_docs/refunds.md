---
title: "Refunds"
category: "Issues"
source: "https://docs.stripe.com/refunds"
---

# Refunds

Refunds allow you to return funds to a customer for a completed charge. Stripe supports full and partial refunds on most payment methods, and provides a robust API for managing the entire refund lifecycle.

## How Refunds Work

When you create a refund, Stripe sends the funds back to the customer's original payment method. The refund is processed through the same payment network (card network, bank transfer, etc.) that was used for the original charge. You can refund a payment up to 180 days after the original charge, though some payment methods have shorter windows.

Key points:

- Refunds are tied to a specific charge or PaymentIntent.
- You can issue multiple partial refunds until the total refunded amount equals the original charge.
- Refunds cannot exceed the original charge amount.
- Stripe fees on the original charge are not returned when you issue a refund. The Stripe processing fee from the original payment is retained.

## Full vs Partial Refunds

**Full refunds** return the entire charge amount to the customer. If no amount is specified in the API call, Stripe defaults to a full refund.

**Partial refunds** return a portion of the original charge. You specify the amount (in the smallest currency unit, e.g., cents for USD). You can issue multiple partial refunds on the same charge as long as the cumulative total does not exceed the original charge amount.

## Creating Refunds via the API

### Refund a PaymentIntent

```python
import stripe

stripe.api_key = "sk_test_..."

# Full refund on a PaymentIntent
refund = stripe.Refund.create(
    payment_intent="pi_1234567890",
)

print(refund.id)       # re_...
print(refund.status)   # "succeeded" or "pending"
```

### Partial Refund with a Reason

```python
import stripe

stripe.api_key = "sk_test_..."

# Partial refund of $5.00 with a reason
refund = stripe.Refund.create(
    payment_intent="pi_1234567890",
    amount=500,  # amount in cents
    reason="requested_by_customer",
)
```

### Refund a Charge Directly

```python
import stripe

stripe.api_key = "sk_test_..."

refund = stripe.Refund.create(
    charge="ch_1234567890",
    amount=1000,  # $10.00 partial refund
)
```

## Refund Reasons

When creating a refund, you can optionally specify a `reason` parameter. Accepted values:

| Reason | Description |
|--------|-------------|
| `duplicate` | The charge was made in error and is a duplicate. |
| `fraudulent` | The charge was fraudulent. |
| `requested_by_customer` | The customer requested the refund. |

If no reason is provided, the refund appears as "Other" in the Dashboard. Specifying a reason helps with reporting and can provide useful context for dispute prevention.

## Refund Timing

Refund timing depends on the customer's payment method and issuing bank:

- **Credit cards**: Refunds typically appear on the customer's statement within 5-10 business days. Some banks may take longer.
- **Debit cards**: Similar to credit cards, but can take up to 10 business days.
- **Bank transfers (ACH)**: Refunds can take 3-5 business days.
- **Other payment methods**: Timing varies. SEPA refunds may take up to 8 weeks. Boleto and OXXO refunds go to the customer's Stripe-issued refund destination.

Once a refund is submitted, its status will transition through these states:

1. **`pending`** -- The refund has been submitted and is being processed.
2. **`succeeded`** -- The refund has been successfully processed and funds sent.
3. **`failed`** -- The refund could not be processed (see below).
4. **`canceled`** -- The refund was canceled before it was processed.

## Refund Failures

Refunds can fail for several reasons:

- **Expired or canceled card**: If the customer's card has been closed since the original charge, the card network may not be able to route the refund. In this case, the bank typically still credits the customer through other means, but the process may take longer.
- **Insufficient balance**: If your Stripe account balance is insufficient to cover the refund, it will remain pending until your balance is adequate. Stripe may debit your linked bank account to cover the shortfall.
- **Network issues**: Rare processing failures on the card network side.

When a refund fails, you receive a `charge.refund.updated` webhook event. The refund object's `failure_reason` field explains why.

```python
# Retrieve a refund to check its status
refund = stripe.Refund.retrieve("re_1234567890")

if refund.status == "failed":
    print(f"Refund failed: {refund.failure_reason}")
    # failure_reason values: "lost_or_stolen_card", "expired_or_canceled_card",
    # "charge_for_pending_refund_disputed", "declined", "merchant_request", "unknown"
```

## Refunds on Connected Accounts (Stripe Connect)

If you use Stripe Connect, refund behavior depends on the charge type:

- **Direct charges**: Created on the connected account. The connected account's balance is debited. Create the refund using the connected account's credentials or with a `Stripe-Account` header.
- **Destination charges**: Created on the platform. The platform's balance is debited, and Stripe automatically reverses the transfer to the connected account.
- **Separate charges and transfers**: You must reverse the transfer separately from the refund. Stripe does not automatically handle this.

```python
# Refund a direct charge on a connected account
refund = stripe.Refund.create(
    charge="ch_1234567890",
    stripe_account="acct_connected_account_id",
)

# Refund a destination charge (reverses transfer automatically)
refund = stripe.Refund.create(
    payment_intent="pi_1234567890",
    reverse_transfer=True,
)
```

## Refund Policy Best Practices

1. **Process refunds promptly.** Delayed refunds increase the likelihood of a dispute (chargeback), which carries a non-refundable dispute fee.
2. **Communicate clearly with customers.** Let them know the refund has been initiated and provide an estimated timeline.
3. **Use partial refunds when appropriate.** For items partially used or returned, partial refunds can be fairer than a full refund.
4. **Track refund reasons.** Use the `reason` parameter and metadata to keep a record of why refunds were issued for internal auditing.
5. **Monitor your refund rate.** A high refund rate may signal issues with your product, service, or billing practices. Card networks may flag accounts with excessive refund rates.
6. **Set clear refund policies upfront.** Display your refund policy on your website and in receipts. Clear policies reduce confusion and disputes.
7. **Prefer refunds over disputes.** If a customer contacts you about an issue, proactively issuing a refund is almost always cheaper and faster than handling a dispute.

## Listening for Refund Events via Webhooks

Stripe sends several webhook events related to refunds:

- `charge.refunded` -- A charge was fully or partially refunded.
- `charge.refund.updated` -- A refund's status changed (e.g., from pending to succeeded or failed).

Listen for these events to keep your system in sync with Stripe's refund processing.
