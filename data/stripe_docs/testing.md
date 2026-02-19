---
title: "Testing"
category: "Payments"
source: "https://docs.stripe.com/testing"
---

# Testing

## Test Mode vs. Live Mode

Every Stripe account has two modes that operate as completely separate environments:

### Test Mode
- Uses test API keys (prefixed with `sk_test_` and `pk_test_`).
- No real money is moved. No actual charges are processed.
- Test data is completely isolated from live data.
- Simulates the full payment flow including webhooks.
- Free to use with no transaction fees.

### Live Mode
- Uses live API keys (prefixed with `sk_live_` and `pk_live_`).
- Processes real payments with real money.
- Connected to actual card networks and banks.
- Standard Stripe fees apply.

You can toggle between modes in the Stripe Dashboard using the "Test mode" toggle in the top navigation.

## Test API Keys

Find your test API keys in the Stripe Dashboard under **Developers > API keys** (with test mode enabled).

```python
import stripe

# Use test keys during development
stripe.api_key = "sk_test_your_test_key_here"

# Switch to live keys for production
# stripe.api_key = "sk_live_your_live_key_here"
```

Test mode API keys can safely be included in client-side code and test suites. Never include live mode secret keys in client-side code or public repositories.

## Test Card Numbers

Stripe provides specific card numbers that simulate different outcomes in test mode. These cards only work with test API keys.

### Successful Payments

| Card Number | Brand | Description |
|-------------|-------|-------------|
| `4242424242424242` | Visa | Succeeds and immediately processes the payment |
| `4000056655665556` | Visa (debit) | Succeeds with a debit card |
| `5555555555554444` | Mastercard | Succeeds and immediately processes the payment |
| `378282246310005` | American Express | Succeeds and immediately processes the payment |
| `6011111111111117` | Discover | Succeeds and immediately processes the payment |
| `3056930009020004` | Diners Club | Succeeds and immediately processes the payment |
| `3566002020360505` | JCB | Succeeds and immediately processes the payment |
| `6200000000000005` | UnionPay | Succeeds and immediately processes the payment |

### Declined Payments

| Card Number | Error Code | Description |
|-------------|------------|-------------|
| `4000000000000002` | `card_declined` | Generic decline |
| `4000000000009995` | `card_declined` (insufficient_funds) | Insufficient funds decline |
| `4000000000009987` | `card_declined` (lost_card) | Lost card decline |
| `4000000000009979` | `card_declined` (stolen_card) | Stolen card decline |
| `4000000000000069` | `expired_card` | Expired card |
| `4000000000000127` | `incorrect_cvc` | Incorrect CVC |
| `4000000000000119` | `processing_error` | Processing error |
| `4242424242424241` | `incorrect_number` | Incorrect card number |
| `4000000000000101` | `card_declined` (cvc_check_fail) | CVC check fails |

### 3D Secure / Authentication Test Cards

| Card Number | Behavior |
|-------------|----------|
| `4000002500003155` | Requires 3D Secure 2 authentication on every transaction |
| `4000002760003184` | Requires 3D Secure 2 authentication, but the user can fail authentication |
| `4000008260003178` | Requires 3D Secure authentication. Attempts to pay with this card without performing 3D Secure will fail. |
| `4000000000003220` | 3D Secure 2 required on setup, but succeeds for off-session payments |
| `4000000000003055` | 3D Secure is supported but not required. Stripe will not trigger authentication. |
| `4000000000003063` | 3D Secure is supported but not required. Stripe requests authentication, and the customer completes it. |

### Other Test Scenarios

| Card Number | Scenario |
|-------------|----------|
| `4000000000005126` | Succeeds, but triggers an `issuer_decline` on capture (for manual capture) |
| `4000000000000259` | Succeeds, then later a dispute is created |
| `4000003800000446` | Succeeds with a `funds_not_yet_available` status (delayed settlement) |
| `4000000000000341` | Attaching to a Customer succeeds, but first charge attempt fails |

### Test Card Details

For all test cards, use:
- **Expiration date**: Any future date (e.g., `12/34`)
- **CVC**: Any 3-digit number (4 digits for Amex, e.g., `1234`)
- **ZIP/Postal code**: Any valid format

```python
# Example: creating a PaymentMethod with a test card
pm = stripe.PaymentMethod.create(
    type="card",
    card={
        "number": "4242424242424242",
        "exp_month": 12,
        "exp_year": 2034,
        "cvc": "123",
    },
)
```

In most integrations, you will use Stripe's pre-built test tokens instead of raw card numbers:

```python
# Using test payment method tokens
stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    payment_method="pm_card_visa",           # Successful Visa
    confirm=True,
)

stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    payment_method="pm_card_chargeDeclined", # Declined card
    confirm=True,
)
```

## Testing with the Stripe CLI

The Stripe CLI is a command-line tool for testing webhooks locally and interacting with the Stripe API.

### Installation

```bash
# macOS
brew install stripe/stripe-cli/stripe

# Windows (Scoop)
scoop install stripe

# Linux (Debian/Ubuntu)
# Download from https://github.com/stripe/stripe-cli/releases
```

### Login

```bash
stripe login
# Opens a browser window to authenticate with your Stripe account
```

### Forwarding Webhooks Locally

The most common use of the Stripe CLI is forwarding webhook events to your local development server:

```bash
stripe listen --forward-to localhost:4242/webhook
```

This command:
1. Creates a temporary webhook endpoint on Stripe.
2. Forwards all events to your local server.
3. Prints a webhook signing secret (starts with `whsec_`). Use this in your code.

```
> Ready! Your webhook signing secret is whsec_1234abcd...
```

### Triggering Test Events

You can manually trigger specific events for testing:

```bash
# Trigger a successful payment
stripe trigger payment_intent.succeeded

# Trigger a failed payment
stripe trigger payment_intent.payment_failed

# Trigger a checkout session completion
stripe trigger checkout.session.completed

# Trigger a customer subscription creation
stripe trigger customer.subscription.created

# Trigger a dispute
stripe trigger charge.dispute.created
```

### Making API Calls

```bash
# Create a PaymentIntent
stripe payment_intents create --amount=2000 --currency=usd

# List recent payments
stripe payment_intents list --limit=5

# Retrieve a specific object
stripe payment_intents retrieve pi_1234abcd
```

## Testing Specific Scenarios

### Testing Disputes

Use the card `4000000000000259`. A charge on this card succeeds initially, and then a dispute is automatically created after a short delay. This lets you test your dispute handling workflow.

```python
# This will succeed, then generate a dispute
intent = stripe.PaymentIntent.create(
    amount=5000,
    currency="usd",
    payment_method="pm_card_createDispute",
    confirm=True,
)
```

### Testing Refunds

Refunds in test mode work the same as in live mode. Create a charge and then refund it:

```python
# Create a successful payment
intent = stripe.PaymentIntent.create(
    amount=5000,
    currency="usd",
    payment_method="pm_card_visa",
    confirm=True,
)

# Full refund
refund = stripe.Refund.create(payment_intent=intent.id)

# Partial refund
refund = stripe.Refund.create(
    payment_intent=intent.id,
    amount=2000,  # Refund $20 of the $50 charge
)
```

### Testing Subscriptions

```python
# Create a customer with a test card
customer = stripe.Customer.create(
    payment_method="pm_card_visa",
    invoice_settings={"default_payment_method": "pm_card_visa"},
)

# Create a subscription
subscription = stripe.Subscription.create(
    customer=customer.id,
    items=[{"price": "price_monthly_test"}],
)
```

Use the test clock feature to simulate time progression for subscriptions:

```python
# Create a test clock
test_clock = stripe.test_helpers.TestClock.create(
    frozen_time=1672531200,  # Jan 1, 2023
    name="Subscription lifecycle test",
)

# Create a customer attached to the test clock
customer = stripe.Customer.create(
    test_clock=test_clock.id,
    payment_method="pm_card_visa",
    invoice_settings={"default_payment_method": "pm_card_visa"},
)

# Advance the clock to trigger billing cycles
stripe.test_helpers.TestClock.advance(
    test_clock.id,
    frozen_time=1675209600,  # Feb 1, 2023
)
```

### Testing ACH Direct Debit

Use the test routing number `110000000` and any valid 12-digit account number.

### Testing International Payment Methods

For iDEAL:
```python
pm = stripe.PaymentMethod.create(
    type="ideal",
    ideal={"bank": "ing"},
)
```

For SEPA Direct Debit, use the test IBAN: `DE89370400440532013000`.

## Test Mode Limitations

- Real card numbers do not work in test mode (and vice versa for test numbers in live mode).
- Some payment methods have test-specific bank details (test IBANs, test routing numbers).
- Webhook delivery in test mode may have slightly different timing than live mode.
- Test mode does not connect to real card networks, so some edge cases (like real issuer behavior) cannot be perfectly simulated.
- Stripe recommends testing with live mode using small amounts ($0.50) for a final integration check before going to production.

## Common Support Questions

**Q: Can I use real card numbers in test mode?**
No. Test mode only accepts Stripe's designated test card numbers. Real card numbers will be rejected. Similarly, test card numbers do not work in live mode.

**Q: My test webhook is not being received. What should I do?**
Verify that the Stripe CLI is running with `stripe listen --forward-to <your_url>`. Check that your endpoint URL is correct and your server is running. Look at the CLI output for delivery attempts and error codes. Also confirm that the webhook signing secret in your code matches the one displayed by the CLI.

**Q: Do test mode charges appear on customer credit card statements?**
No. Test mode charges are entirely simulated. No real transactions are processed and nothing appears on any real credit card statement.

**Q: How do I test in live mode safely?**
Create a charge for the minimum amount ($0.50 USD) using a real card, then immediately refund it. The refund returns the full amount. You may still see a temporary hold on the card statement that resolves within a few days.

**Q: Can I delete test mode data?**
Yes. You can clear all test mode data in the Stripe Dashboard under **Developers > Overview > Test Data > Delete all test data**. This is irreversible and removes all test mode objects (customers, payments, subscriptions, etc.).
