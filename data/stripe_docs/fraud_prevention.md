---
title: "Fraud Prevention with Stripe Radar"
category: "Issues"
source: "https://docs.stripe.com/radar"
---

# Fraud Prevention with Stripe Radar

Stripe Radar is a suite of machine learning-powered tools for detecting and preventing fraudulent transactions. It is built directly into Stripe's payment processing pipeline and evaluates every payment in real time.

## How Radar Works

Radar uses machine learning models trained on data from millions of businesses across the Stripe network. Because Stripe processes payments for companies of all sizes and industries worldwide, Radar's models have an exceptionally broad view of fraud patterns. Every payment processed through Stripe contributes signals that improve fraud detection for the entire network.

When a payment is attempted, Radar evaluates hundreds of signals, including:

- **Card information**: Card number, CVC, expiration date, AVS (address verification) results.
- **Behavioral signals**: IP address, device fingerprint, browser metadata, session behavior.
- **Transaction patterns**: Purchase amount, frequency, velocity of attempts, geographic anomalies.
- **Network-wide intelligence**: Whether the card or email has been involved in fraud on other Stripe accounts.
- **Historical data**: The customer's past transaction history with your business and across the Stripe network.

## Risk Scoring

Radar assigns a risk score to every payment attempt, expressed as a risk level and a numerical score:

| Risk Level | Score Range | Description |
|-----------|-------------|-------------|
| `normal` | 0-19 | Low risk. Payment is unlikely to be fraudulent. |
| `elevated` | 20-64 | Moderate risk. Some suspicious signals detected. |
| `highest` | 65-99 | High risk. Strong indicators of fraud. |

You can view the risk assessment for any payment in the Stripe Dashboard under the payment details, or access it programmatically via the API:

```python
import stripe

stripe.api_key = "sk_test_..."

# Retrieve a PaymentIntent and inspect its risk evaluation
payment_intent = stripe.PaymentIntent.retrieve(
    "pi_1234567890",
    expand=["latest_charge"],
)

charge = payment_intent.latest_charge
outcome = charge.outcome

print(f"Risk level: {outcome.risk_level}")    # "normal", "elevated", or "highest"
print(f"Risk score: {outcome.risk_score}")     # 0-99
print(f"Seller message: {outcome.seller_message}")
print(f"Network status: {outcome.network_status}")
```

## Default Radar Behavior

With Radar enabled (included for free in Stripe's standard pricing), Stripe automatically:

1. **Blocks payments with the highest risk level** when the risk score indicates a very high probability of fraud.
2. **Allows payments with normal and elevated risk levels** to proceed.
3. **Blocks known fraudulent cards** from the network-wide blocklist.
4. **Applies CVC and AVS checks** and blocks payments that fail these checks (configurable).

## Radar Rules

Radar rules let you customize how payments are handled based on specific conditions. Rules use a straightforward syntax and can perform three actions:

- **Block**: Reject the payment.
- **Allow**: Override a block and allow the payment.
- **Review**: Flag the payment for manual review (requires Radar for Fraud Teams).

### Rule Syntax

Rules follow the pattern: `{action} if {attribute} {operator} {value}`

Examples of built-in and custom rules:

```
Block if :risk_level: = 'highest'
Block if :ip_country: = 'NG'
Block if :card_country: != :ip_country:
Block if :amount_in_usd: > 5000 AND :risk_level: = 'elevated'
Allow if :is_3d_secure: = 'true'
Review if :risk_level: = 'elevated' AND :amount_in_usd: > 1000
```

### Available Attributes

Rules can reference a wide range of attributes:

- **Payment attributes**: `:amount_in_usd:`, `:currency:`, `:is_recurring:`
- **Card attributes**: `:card_country:`, `:card_brand:`, `:card_funding:` (credit, debit, prepaid)
- **Address verification**: `:address_zip_check:`, `:address_line1_check:`, `:cvc_check:`
- **Customer info**: `:customer_email:`, `:customer_email_domain:`
- **Geolocation**: `:ip_country:`, `:ip_address:`
- **Risk data**: `:risk_level:`, `:risk_score:`
- **Authentication**: `:is_3d_secure:`
- **Lists**: `:card_fingerprint: in @block_list`

### Managing Rules via the Dashboard

You create and manage Radar rules in the Stripe Dashboard under **Radar > Rules**. Rules are evaluated in priority order, and the first matching rule determines the action. You can enable, disable, and reorder rules without writing code.

## Blocklists and Allowlists

Radar supports custom lists for fine-grained control:

- **Block lists**: Add specific card fingerprints, email addresses, email domains, IP addresses, or customer IDs that should always be blocked.
- **Allow lists**: Add trusted values that should bypass Radar's risk evaluation.

Lists are managed in the Dashboard under **Radar > Lists** and can be referenced in rules using the `in @list_name` syntax.

```python
# You can also manage lists via the API
# Add an email to a block list
stripe.radar.ValueListItem.create(
    value_list="rsl_1234567890",  # Your block list ID
    value="fraudster@example.com",
)
```

## Radar for Fraud Teams

Radar for Fraud Teams is an upgraded tier (additional fee per screened transaction) that adds:

1. **Manual review queue**: Payments flagged with `Review` rules are placed in a review queue in the Dashboard. Your team can approve or reject them manually.
2. **Advanced rules**: Access to additional attributes and more complex rule logic, including velocity checks (e.g., "block if more than 3 payments from same IP in 1 hour").
3. **Deeper insights**: Enhanced reporting on fraud patterns, rule performance, and false positive/negative rates.
4. **Block and allow lists with group management**: Organize lists by category and manage them at scale.

### Manual Review Workflow

```python
# When a payment is placed in review, it has outcome.type = "manual_review"
# You approve or reject via the Dashboard or API

# Approve a payment in review
payment_intent = stripe.PaymentIntent.capture("pi_1234567890")

# Or reject it
payment_intent = stripe.PaymentIntent.cancel("pi_1234567890")
```

When a payment is in review, the charge is authorized but not captured. You have a limited window (typically 7 days for card payments) to approve or reject before the authorization expires.

## Handling Blocked Payments

When Radar blocks a payment, the PaymentIntent or Charge outcome provides details:

```python
try:
    payment_intent = stripe.PaymentIntent.create(
        amount=2000,
        currency="usd",
        payment_method="pm_card_visa",
        confirm=True,
    )
except stripe.error.CardError as e:
    err = e.error
    if err.code == "card_declined" and err.decline_code == "fraudulent":
        print("Payment blocked by Radar as suspected fraud.")
```

## Best Practices for Fraud Prevention

1. **Collect CVC and postal code.** These basic checks significantly reduce fraud with minimal friction.
2. **Enable 3D Secure for high-risk transactions.** Shifts liability for fraud to the card issuer and provides strong authentication.
3. **Start with default rules, then customize.** Radar's defaults work well. Add custom rules based on patterns you observe in your specific business.
4. **Monitor rule performance.** Track how each rule affects your block rate, false positive rate, and dispute rate. Overly aggressive rules can block legitimate customers.
5. **Use metadata.** Attach relevant order information to payments so reviewers have context when evaluating flagged transactions.
6. **Review elevated-risk payments.** If you have Radar for Fraud Teams, use the review queue for payments that are suspicious but not clearly fraudulent.
7. **Keep your block lists updated.** Add known fraudsters and remove entries that are no longer relevant.
8. **Combine Radar with 3D Secure.** Radar identifies risk, and 3D Secure authenticates the cardholder. Together, they provide layered protection.

## Radar Webhook Events

- `radar.early_fraud_warning.created` -- An early fraud warning was issued by the card network.
- `radar.early_fraud_warning.updated` -- An early fraud warning was updated.

These events let you take proactive action (such as issuing a refund) before a formal dispute is filed.
