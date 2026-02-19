---
title: "Payment Methods"
category: "Payments"
source: "https://docs.stripe.com/payments/payment-methods"
---

# Payment Methods

## Overview

A `PaymentMethod` object in Stripe represents a customer's payment instrument. It securely stores the details needed to complete a payment, such as card numbers, bank account information, or wallet tokens. PaymentMethods are the modern replacement for the legacy `Source` and `Token` objects.

## Types of Payment Methods

### Cards

Cards are the most widely used payment method. Stripe supports all major card networks:

- **Visa**
- **Mastercard**
- **American Express**
- **Discover**
- **Diners Club**
- **JCB**
- **UnionPay**
- **Cartes Bancaires** (France)
- **Interac** (Canada, debit)

Cards can be used for one-time payments, recurring subscriptions, and saving for future use.

### Bank Debits and Transfers

- **ACH Direct Debit** (US) - Pull funds directly from a US bank account. Lower fees than cards. 3-5 business day settlement.
- **SEPA Direct Debit** (Europe) - Pull funds from European bank accounts in the SEPA zone.
- **BACS Direct Debit** (UK) - Pull funds from UK bank accounts.
- **Bancontact** (Belgium) - Bank-based payment popular in Belgium.
- **iDEAL** (Netherlands) - Real-time bank transfer used by Dutch consumers.
- **Sofort/Klarna** (Europe) - Bank transfer method popular in Germany, Austria, and other EU countries.

### Digital Wallets

- **Apple Pay** - Payments via Apple devices using stored cards. Requires domain verification and HTTPS.
- **Google Pay** - Payments via Android devices and Chrome browser.
- **Link** - Stripe's own one-click checkout that saves payment details across Stripe merchants.

### Buy Now, Pay Later (BNPL)

- **Klarna** - Installment payments and pay-later options across Europe and the US.
- **Afterpay / Clearpay** - Pay-in-four installment plans.
- **Affirm** - Monthly installment plans for larger purchases.

### Regional Methods

- **WeChat Pay** (China)
- **Alipay** (China)
- **Boleto** (Brazil)
- **OXXO** (Mexico)
- **Konbini** (Japan)
- **PIX** (Brazil)

## Creating a PaymentMethod

### On the Client Side (Recommended)

Using Stripe.js to securely create a PaymentMethod without sensitive data touching your server:

```javascript
const { paymentMethod, error } = await stripe.createPaymentMethod({
  type: "card",
  card: cardElement,
  billing_details: {
    name: "Jenny Rosen",
    email: "jenny@example.com",
  },
});
```

### On the Server Side

Using test tokens for server-side creation (primarily for testing):

```python
import stripe

stripe.api_key = "sk_test_your_test_key_here"

payment_method = stripe.PaymentMethod.create(
    type="card",
    card={"token": "tok_visa"},
)

print(f"PaymentMethod ID: {payment_method.id}")
# Output: pm_1MqLiJLkdIwHu7ixUEgbFCnp
```

## Attaching Payment Methods to Customers

To save a payment method for future use, attach it to a Customer object:

```python
# Create a customer
customer = stripe.Customer.create(
    name="Jenny Rosen",
    email="jenny@example.com",
)

# Attach the payment method
stripe.PaymentMethod.attach(
    "pm_1MqLiJLkdIwHu7ixUEgbFCnp",
    customer=customer.id,
)

# Optionally set as the default payment method
stripe.Customer.modify(
    customer.id,
    invoice_settings={
        "default_payment_method": "pm_1MqLiJLkdIwHu7ixUEgbFCnp",
    },
)
```

## Listing a Customer's Payment Methods

```python
payment_methods = stripe.Customer.list_payment_methods(
    "cus_ABC123",
    type="card",
)

for pm in payment_methods.data:
    card = pm.card
    print(f"{pm.id}: {card.brand} ending in {card.last4}, expires {card.exp_month}/{card.exp_year}")
```

## Detaching a Payment Method

To remove a payment method from a customer:

```python
stripe.PaymentMethod.detach("pm_1MqLiJLkdIwHu7ixUEgbFCnp")
```

This does not delete the PaymentMethod object, but it can no longer be used for payments through that customer.

## Saving Payment Methods for Future Use

### Using SetupIntents

A `SetupIntent` is designed specifically for saving payment methods without charging the customer immediately. It handles authentication (like 3D Secure) upfront so that future off-session payments can proceed without customer interaction.

```python
# Create a SetupIntent
setup_intent = stripe.SetupIntent.create(
    customer="cus_ABC123",
    payment_method_types=["card"],
    usage="off_session",  # Indicates this will be used for future off-session payments
)

# The client_secret is used on the frontend to collect and confirm the payment method
print(f"Client secret: {setup_intent.client_secret}")
```

On the frontend, confirm the SetupIntent:

```javascript
const { setupIntent, error } = await stripe.confirmCardSetup(
  clientSecret,
  {
    payment_method: {
      card: cardElement,
      billing_details: { name: "Jenny Rosen" },
    },
  }
);
```

### Using a PaymentIntent with `setup_future_usage`

You can also save a payment method while collecting a payment:

```python
payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    customer="cus_ABC123",
    payment_method_types=["card"],
    setup_future_usage="off_session",
)
```

The `setup_future_usage` parameter tells Stripe to save the payment method and perform any necessary authentication for future off-session use.

## Charging a Saved Payment Method Off-Session

Once a payment method is saved, you can charge it without the customer being present:

```python
try:
    payment_intent = stripe.PaymentIntent.create(
        amount=3000,
        currency="usd",
        customer="cus_ABC123",
        payment_method="pm_1MqLiJLkdIwHu7ixUEgbFCnp",
        off_session=True,
        confirm=True,
    )
    print(f"Payment succeeded: {payment_intent.id}")
except stripe.error.CardError as e:
    err = e.error
    print(f"Payment failed: {err.code}")
    # You may need to ask the customer to come back on-session
    if err.payment_intent:
        print(f"PaymentIntent ID: {err.payment_intent['id']}")
```

## Automatic Payment Methods

Instead of specifying `payment_method_types` explicitly, you can enable automatic payment methods:

```python
payment_intent = stripe.PaymentIntent.create(
    amount=5000,
    currency="eur",
    automatic_payment_methods={"enabled": True},
)
```

When enabled, Stripe automatically determines which payment methods to show based on the currency, customer location, and your Stripe Dashboard settings. This lets you enable new payment methods from the Dashboard without changing code.

## The PaymentMethod Object

Key fields on a PaymentMethod:

| Field | Description |
|-------|-------------|
| `id` | Unique identifier (e.g., `pm_1MqLiJLkdIwHu7ix...`) |
| `type` | The type of payment method (`card`, `us_bank_account`, `sepa_debit`, etc.) |
| `card` | Card-specific details: `brand`, `last4`, `exp_month`, `exp_year`, `funding` (credit/debit/prepaid) |
| `billing_details` | Customer billing info: `name`, `email`, `phone`, `address` |
| `customer` | The Customer this payment method is attached to, if any |
| `created` | Timestamp of when the PaymentMethod was created |

## Common Support Questions

**Q: A customer's card was declined. What should they do?**
Common decline reasons include insufficient funds, incorrect card details, or the card issuer blocking the transaction. The customer should verify their card details, ensure they have sufficient funds, or contact their bank. They can also try a different payment method.

**Q: How do I update a customer's card expiration date?**
Stripe automatically updates card details for many major issuers through the Automatic Card Updater program. If not updated automatically, the customer needs to provide their new card details, which creates a new PaymentMethod.

**Q: Can a payment method be used without attaching it to a customer?**
Yes. For one-time payments, you can pass the payment method directly to a PaymentIntent without attaching it to a customer. Attaching is only necessary for saving the payment method for future use.

**Q: What is the difference between a SetupIntent and a PaymentIntent with `setup_future_usage`?**
A SetupIntent is used when you want to save a payment method without charging the customer. A PaymentIntent with `setup_future_usage` saves the payment method while also collecting a payment. Both handle authentication for future off-session use.

**Q: Does Stripe store full card numbers?**
Stripe securely stores payment credentials in its PCI-compliant vault. Your application only ever sees tokenized references (PaymentMethod IDs) and masked card details (last 4 digits, brand, expiration).
