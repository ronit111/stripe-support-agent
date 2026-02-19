---
title: "Strong Customer Authentication (SCA) and 3D Secure"
category: "Issues"
source: "https://docs.stripe.com/payments/3d-secure"
---

# Strong Customer Authentication (SCA) and 3D Secure

Strong Customer Authentication (SCA) is a regulatory requirement in Europe (under PSD2) that mandates additional verification for online payments. 3D Secure (3DS) is the primary authentication protocol used to satisfy SCA requirements.

## What Is SCA?

SCA requires that electronic payments be authenticated using at least two of the following three factors:

1. **Something the customer knows** -- a password, PIN, or security question.
2. **Something the customer has** -- a phone, hardware token, or card.
3. **Something the customer is** -- biometrics such as fingerprint or face recognition.

SCA applies to online card payments where both the business and the cardholder's bank are in the European Economic Area (EEA) or the United Kingdom. Transactions that fall outside this scope (e.g., one-leg-out transactions where only one party is in the EEA) are generally not subject to SCA.

## What Is 3D Secure?

3D Secure is an authentication protocol supported by major card networks under different brand names:

- **Visa**: Visa Secure
- **Mastercard**: Mastercard Identity Check
- **American Express**: American Express SafeKey
- **Discover**: ProtectBuy

3D Secure 2 (3DS2) is the current version. It provides a better user experience than the original 3DS1 by supporting app-based and biometric authentication, and by allowing the card issuer to approve low-risk transactions without requiring customer interaction (frictionless flow).

## The 3D Secure Flow

1. **Customer initiates payment.** The customer enters their card details and submits the payment.
2. **Stripe evaluates whether 3DS is needed.** Based on the card, issuer, and regulatory requirements, Stripe determines if authentication is required.
3. **Authentication challenge (if needed).** The customer is redirected to their bank's authentication page or shown a modal/popup. They verify their identity via SMS code, banking app notification, biometric, or password.
4. **Authentication result.** The bank returns an authentication result: success, failure, or attempted (the bank's 3DS server was available but the card was not enrolled).
5. **Payment proceeds or fails.** If authentication succeeds, the payment is processed. If it fails, the payment is declined.

### Frictionless vs Challenge Flow

3DS2 supports a **frictionless flow** where the issuer approves the transaction without requiring the customer to interact with an authentication challenge. This happens when the issuer's risk assessment determines the transaction is low-risk based on factors like the customer's transaction history, device, and amount.

The frictionless flow is transparent to the customer and has no impact on conversion rates. The challenge flow (where the customer must interact) can add friction and may cause some customers to abandon the payment.

## How Stripe Handles 3DS

Stripe integrates 3D Secure directly into the PaymentIntents and SetupIntents APIs. When you use these APIs, Stripe automatically:

1. **Determines if 3DS is required** based on the card's issuer, the customer's location, SCA regulations, and Radar's risk assessment.
2. **Triggers the authentication flow** when needed. The PaymentIntent transitions to a `requires_action` status, and your frontend handles the redirect or modal.
3. **Processes the result** and either completes the payment or returns an error.

### Automatic 3DS with PaymentIntents

```python
import stripe

stripe.api_key = "sk_test_..."

# Create a PaymentIntent -- Stripe handles 3DS automatically
payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="eur",
    payment_method="pm_card_visa",
    confirmation_method="automatic",
    confirm=True,
    return_url="https://yoursite.com/payment/complete",
)

if payment_intent.status == "requires_action":
    # Customer needs to authenticate
    # Redirect them to payment_intent.next_action.redirect_to_url.url
    # Or use Stripe.js to handle the modal
    redirect_url = payment_intent.next_action.redirect_to_url.url
    print(f"Redirect customer to: {redirect_url}")

elif payment_intent.status == "succeeded":
    print("Payment completed without 3DS challenge (frictionless or not required)")
```

### Frontend Handling with Stripe.js

On the frontend, Stripe.js handles the 3DS authentication flow:

```javascript
// Using Stripe.js to handle 3DS
const { error, paymentIntent } = await stripe.confirmCardPayment(
  clientSecret,
  {
    payment_method: {
      card: cardElement,
    },
    return_url: 'https://yoursite.com/payment/complete',
  }
);

if (error) {
  // Authentication failed or customer abandoned
  console.error(error.message);
} else if (paymentIntent.status === 'succeeded') {
  // Payment successful
  console.log('Payment complete');
}
```

### Requesting 3DS Explicitly

You can request 3DS authentication even when it is not strictly required:

```python
# Force 3DS authentication
payment_intent = stripe.PaymentIntent.create(
    amount=5000,
    currency="usd",
    payment_method="pm_card_visa",
    payment_method_options={
        "card": {
            "request_three_d_secure": "any",  # Request 3DS on all attempts
        },
    },
    confirm=True,
    return_url="https://yoursite.com/payment/complete",
)
```

Values for `request_three_d_secure`:

- `"any"` -- Request 3DS on every transaction regardless of exemptions.
- `"automatic"` (default) -- Stripe decides whether to trigger 3DS based on risk, regulations, and exemptions.

## SCA Exemptions

Not all transactions require SCA, even in the EEA. Stripe automatically applies exemptions when possible to reduce unnecessary friction. Common exemptions:

### Low-Value Transactions
Transactions under 30 EUR may be exempt. However, exemptions are limited: after five consecutive exempt transactions or a cumulative total of 100 EUR since the last authenticated transaction, SCA is required.

### Transaction Risk Analysis (TRA)
Payment providers with low fraud rates can request exemptions for transactions up to certain thresholds (e.g., 250 EUR for fraud rates below 0.06%). Stripe applies TRA exemptions automatically when eligible.

### Merchant-Initiated Transactions (MIT)
Recurring payments where the customer is not present (e.g., subscription renewals) can be exempt after the initial authenticated setup. The first payment must be authenticated with SCA; subsequent charges can use the stored credential without re-authentication.

### Trusted Beneficiaries
Customers can add merchants to a "trusted beneficiary" list with their bank, exempting future transactions from SCA. This is managed by the customer's bank and is not something merchants can directly control.

### Corporate Payments
Payments made with corporate or virtual cards issued to businesses (not individuals) may be exempt from SCA.

## Impact on Conversion Rates

3DS authentication introduces an additional step in the checkout flow, which can reduce conversion rates. The impact varies:

- **3DS2 frictionless flow**: Minimal impact. The customer does not see an authentication challenge.
- **3DS2 challenge flow**: Moderate impact. The customer must interact with their bank's authentication interface. Drop-off rates of 5-15% are common during the challenge step.
- **3DS1 (legacy)**: Higher impact. Older interface, often a full-page redirect. Drop-off rates can be higher.

### Minimizing Conversion Impact

1. **Use Stripe's automatic 3DS handling.** Stripe applies 3DS only when required or when it improves the chance of authorization.
2. **Apply for exemptions.** Stripe automatically requests exemptions (TRA, low-value) where eligible.
3. **Authenticate during setup, not checkout.** For subscriptions, authenticate the card when saved (via SetupIntent) so future charges proceed without 3DS.
4. **Optimize your checkout flow.** Use Stripe Elements or Checkout for a seamless, embedded authentication experience rather than redirects.

## Liability Shift

A key benefit of 3D Secure is the **liability shift**. When a payment is successfully authenticated with 3DS, liability for fraud-related disputes shifts from the merchant to the card issuer. If a customer disputes an authenticated payment as fraudulent, the card issuer bears the cost, not you.

This makes 3DS valuable even outside the EEA, as a tool for fraud prevention and dispute liability management.

```python
# Check if a charge had successful 3DS and liability shift
charge = stripe.Charge.retrieve("ch_1234567890")

three_d_secure = charge.payment_method_details.card.three_d_secure
if three_d_secure:
    print(f"3DS version: {three_d_secure.version}")         # "2.1.0" or "1.0.2"
    print(f"Authentication result: {three_d_secure.result}") # "authenticated", "attempt_acknowledged"
```

## Common Support Scenarios

**Customer says they were declined after authentication:**
This can happen if the card issuer declines the payment even after successful 3DS authentication (e.g., insufficient funds). Check the PaymentIntent's `last_payment_error` for the specific decline reason.

**Customer cannot complete the 3DS challenge:**
The customer should contact their bank. Common issues include outdated phone numbers for SMS delivery, expired banking app sessions, or browser compatibility problems.

**Recurring charges failing after initial authentication:**
Ensure the initial payment or SetupIntent was authenticated with SCA. The resulting PaymentMethod must be stored on a Customer object with proper `off_session` mandate data for future merchant-initiated transactions.
