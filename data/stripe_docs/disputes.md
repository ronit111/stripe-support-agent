---
title: "Disputes and Chargebacks"
category: "Issues"
source: "https://docs.stripe.com/disputes"
---

# Disputes and Chargebacks

A dispute (also called a chargeback) occurs when a cardholder questions a payment with their card issuer. The issuer creates a formal dispute which triggers Stripe to notify you and debit the disputed amount plus a dispute fee from your Stripe balance.

## What Is a Dispute?

When a customer contacts their bank or card issuer to contest a charge, the issuer initiates a dispute. This process is governed by card network rules (Visa, Mastercard, etc.) and the issuer's policies. Key facts:

- The disputed amount is immediately debited from your Stripe account balance (or goes negative if insufficient balance exists).
- Stripe charges a non-refundable dispute fee of $15.00 USD per dispute (varies by country and currency).
- Even if you win the dispute, the dispute fee is not returned in most regions.
- Disputes can be filed up to 120 days after the original charge, though the window varies by card network and dispute type.

## Dispute Lifecycle

Disputes progress through a defined set of statuses:

### 1. `warning_needs_response`
Some card networks (mainly Visa) send an early fraud warning before a formal dispute. This is an inquiry stage. You can proactively refund the charge to prevent the dispute from escalating. No dispute fee is charged at this stage.

### 2. `needs_response`
A formal dispute has been filed. You have a limited window (typically 7-21 days depending on the card network) to respond with evidence. If you do not respond, the dispute is automatically lost.

### 3. `under_review`
You have submitted evidence, and the card issuer is reviewing it. This review period can last 60-90 days. No further action is needed during this stage.

### 4. `won`
The issuer ruled in your favor. The disputed amount is returned to your Stripe balance. The dispute fee is typically not refunded.

### 5. `lost`
The issuer ruled in favor of the cardholder. The debited amount remains with the cardholder. The dispute fee is not refunded.

### 6. `charge_refunded`
You chose to accept the dispute by not responding, or you refunded the charge. The cardholder keeps the funds.

## Dispute Reason Codes

Each dispute includes a `reason` field that explains why the cardholder filed it. Common reasons:

| Reason Code | Description | Typical Cause |
|------------|-------------|---------------|
| `fraudulent` | The cardholder claims they did not authorize the charge. | Stolen card or credentials. Most common dispute type. |
| `product_not_received` | The customer claims they did not receive the product or service. | Shipping issues, delivery failures, or unclear fulfillment. |
| `product_unacceptable` | The product was received but was defective, damaged, or not as described. | Quality issues or mismatch with listing description. |
| `duplicate` | The cardholder was charged multiple times for the same product or service. | Double-charges from retry logic or system errors. |
| `subscription_canceled` | The customer claims they canceled a subscription but were still charged. | Cancellation not processed or timing mismatch. |
| `unrecognized` | The cardholder does not recognize the charge on their statement. | Poor statement descriptor or legitimate forgotten purchase. |
| `credit_not_processed` | The customer expected a refund or credit that was not issued. | Delayed or missing refund. |
| `general` | Does not fall into another category. | Varies. |

## Responding to Disputes

To respond to a dispute, you submit evidence that supports the legitimacy of the charge. Stripe provides a structured evidence submission interface via the Dashboard and API.

### Evidence Types

Depending on the dispute reason, relevant evidence includes:

- **For `fraudulent`**: AVS (Address Verification) match, CVC verification, 3D Secure authentication proof, IP address and device information, customer communication logs, prior undisputed transactions from the same customer.
- **For `product_not_received`**: Shipping tracking numbers, delivery confirmation, signed delivery receipts, carrier tracking URLs.
- **For `product_unacceptable`**: Photos of item condition, return policy documentation, customer communications showing acceptance.
- **For `duplicate`**: Proof that each charge corresponds to a separate product/service, itemized receipts, order confirmations.
- **For `subscription_canceled`**: Cancellation policy, proof the customer did not cancel, usage logs showing continued access.

### Submitting Evidence via the API

```python
import stripe

stripe.api_key = "sk_test_..."

# Submit evidence for a dispute
stripe.Dispute.modify(
    "dp_1234567890",
    evidence={
        "customer_name": "Jane Smith",
        "customer_email_address": "jane@example.com",
        "shipping_tracking_number": "1Z999AA10123456784",
        "shipping_carrier": "UPS",
        "shipping_date": "2025-12-01",
        "product_description": "Premium wireless headphones",
        "uncategorized_text": "Customer confirmed receipt via email on Dec 5.",
    },
    submit=True,  # Set to True to finalize. False saves as draft.
)
```

Setting `submit=True` finalizes the evidence and sends it to the card issuer. You can only submit evidence once per dispute, so gather all evidence before submitting. Setting `submit=False` saves a draft that you can update later.

### Tips for Effective Dispute Responses

1. **Be thorough.** Include every piece of relevant evidence. You only get one submission.
2. **Be concise.** Card issuers review many disputes. Clear, organized evidence is more persuasive.
3. **Include customer communication.** Emails or messages showing the customer acknowledged the purchase or delivery are powerful evidence.
4. **Provide visual evidence.** Screenshots, photos, and signed receipts strengthen your case.
5. **Respond quickly.** Do not wait until the deadline. Submit as soon as your evidence is ready.

## Stripe's Dispute Fee

Stripe charges a dispute fee when a formal dispute is filed, regardless of the outcome. The fee varies by region:

- **United States**: $15.00 USD
- **Europe**: 15.00 EUR
- **United Kingdom**: 10.00 GBP
- **Other regions**: Varies; check Stripe's pricing page.

This fee covers the administrative cost of managing the dispute process. It is non-refundable even if you win the dispute (except in Australia and certain other jurisdictions where regulation requires refund on a win).

## Preventing Disputes

Prevention is far more cost-effective than fighting disputes. Strategies include:

1. **Use clear statement descriptors.** Ensure your business name on the customer's card statement is recognizable. Unrecognized charges are a top dispute trigger.
2. **Enable 3D Secure.** Authentication shifts liability to the card issuer for fraud-related disputes.
3. **Collect signatures on delivery.** For physical goods, proof of delivery is your strongest defense.
4. **Respond to customer inquiries quickly.** Customers who cannot reach you will contact their bank instead.
5. **Issue refunds proactively.** If a customer is unhappy, a refund is cheaper than a dispute ($15+ fee, time, and a hit to your dispute ratio).
6. **Use Stripe Radar.** Machine learning-based fraud detection blocks fraudulent payments before they result in disputes.
7. **Monitor your dispute rate.** Card networks flag businesses with dispute rates above 0.75%-1%. Exceeding these thresholds can result in fines or account termination.

## Dispute-Related Webhook Events

- `charge.dispute.created` -- A new dispute has been filed.
- `charge.dispute.updated` -- A dispute's status or evidence has changed.
- `charge.dispute.funds_reinstated` -- Funds were returned after winning a dispute.
- `charge.dispute.funds_withdrawn` -- Funds were withdrawn due to a dispute.
- `charge.dispute.closed` -- A dispute has been resolved (won or lost).

Listen for `charge.dispute.created` to trigger your dispute response workflow as soon as a dispute is opened.
