---
title: "API Keys"
category: "Core Concepts"
source: "https://docs.stripe.com/keys"
---

# API Keys

API keys authenticate your requests to the Stripe API. Every API request must include a valid key, and the type of key you use determines what operations are permitted and whether they affect real money.

## Types of API Keys

Stripe provides three types of API keys:

### Publishable Keys

- **Prefix**: `pk_test_` (test mode) or `pk_live_` (live mode)
- **Usage**: Frontend (browser, mobile app)
- **Purpose**: Identify your Stripe account when creating tokens, confirming PaymentIntents, or initializing Stripe.js and Stripe Elements.
- **Security level**: Safe to expose in client-side code. Publishable keys can only perform a limited set of read operations and cannot access sensitive data or modify resources.

Publishable keys are designed to be embedded in your frontend code. They cannot create charges, read customer data, or perform any operation that requires secret-level access.

### Secret Keys

- **Prefix**: `sk_test_` (test mode) or `sk_live_` (live mode)
- **Usage**: Backend (server only)
- **Purpose**: Full access to the Stripe API. Used for creating charges, managing customers, issuing refunds, and all other API operations.
- **Security level**: Must be kept confidential. Never expose in client-side code, version control, or logs.

Secret keys have unrestricted access to your entire Stripe account. A compromised secret key allows an attacker to create charges, issue refunds, access customer data, and modify account settings.

### Restricted Keys

- **Prefix**: `rk_test_` or `rk_live_`
- **Usage**: Backend, with limited permissions
- **Purpose**: Provide granular, least-privilege access to specific API resources.
- **Security level**: Confidential, like secret keys, but with a smaller blast radius if compromised.

Restricted keys let you define exactly which resources and operations a key can access. For example, you can create a restricted key that can only read charges but cannot create refunds.

```python
# A restricted key with limited permissions works like a secret key
import stripe

stripe.api_key = "rk_live_..."  # Restricted key with read-only charge access

# This works if the key has "charges: read" permission
charge = stripe.Charge.retrieve("ch_1234567890")

# This would fail if the key lacks "refunds: write" permission
# stripe.Refund.create(charge="ch_1234567890")  # PermissionError
```

## Test Mode vs Live Mode

Stripe operates in two distinct modes, each with its own set of API keys and completely separate data:

| Aspect | Test Mode | Live Mode |
|--------|-----------|-----------|
| Key prefixes | `pk_test_`, `sk_test_` | `pk_live_`, `sk_live_` |
| Real money | No. Uses test card numbers. | Yes. Processes real payments. |
| Data | Separate from live mode. | Separate from test mode. |
| Dashboard view | Toggle in Dashboard header. | Toggle in Dashboard header. |
| Webhooks | Separate endpoints and events. | Separate endpoints and events. |

Test mode is a complete sandbox. Objects created in test mode (customers, charges, subscriptions) do not exist in live mode and vice versa. You can safely experiment, test integrations, and verify webhook handling in test mode without any risk.

### Test Card Numbers

In test mode, use Stripe's test card numbers instead of real cards:

| Card Number | Description |
|------------|-------------|
| `4242 4242 4242 4242` | Succeeds and processes the payment. |
| `4000 0000 0000 3220` | Triggers 3D Secure authentication. |
| `4000 0000 0000 0002` | Declines with `card_declined`. |
| `4000 0000 0000 9995` | Declines with `insufficient_funds`. |
| `4000 0025 0000 3155` | Requires SCA authentication. |

Use any future expiration date (e.g., 12/34), any 3-digit CVC, and any postal code with test cards.

## Where to Use Each Key Type

### Frontend (Browser / Mobile)

Use **publishable keys only**. These are embedded in your JavaScript, mobile app, or any code that runs on the client side.

```javascript
// Frontend: Stripe.js initialization with publishable key
const stripe = Stripe('pk_live_your_publishable_key');

// Create a PaymentMethod (uses publishable key implicitly)
const { paymentMethod, error } = await stripe.createPaymentMethod({
  type: 'card',
  card: cardElement,
});
```

### Backend (Server)

Use **secret keys or restricted keys**. These should only exist on your server, never transmitted to clients.

```python
import stripe

# Backend: Set the secret key for server-side operations
stripe.api_key = "sk_live_your_secret_key"

# Create a PaymentIntent (requires secret key)
payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    customer="cus_1234567890",
)
```

### Microservices and Third-Party Integrations

Use **restricted keys** with the minimum necessary permissions. If a microservice only needs to read charge data, create a restricted key with only `charges: read` access.

## Rolling (Rotating) API Keys

Key rotation is a security best practice. Stripe supports rolling keys so you can transition to a new key without downtime:

1. **Generate a new key** in the Dashboard under **Developers > API Keys**.
2. **Update your application** to use the new key.
3. **Verify** that the new key works correctly.
4. **Revoke the old key** once you confirm the new key is fully deployed.

Stripe's key rolling feature creates a new key and keeps the old key active for a grace period (which you control), allowing you to update your systems gradually. When you roll a standard secret key, both the old and new keys work simultaneously until you explicitly expire the old one.

```
# Rolling process:
# 1. Dashboard: Developers > API Keys > Roll key
# 2. Stripe generates a new key. Old key still works.
# 3. Update your servers with the new key.
# 4. Dashboard: Expire the old key.
```

## Key Security Best Practices

### Store Keys in Environment Variables

Never hardcode API keys in your source code. Use environment variables:

```python
import os
import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
```

```bash
# .env file (add to .gitignore)
STRIPE_SECRET_KEY=sk_live_your_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

### Never Commit Keys to Version Control

Add your `.env` file or any file containing keys to `.gitignore`. If a key is accidentally committed, roll it immediately, even if the repository is private. Git history retains the key even after the file is deleted.

### Use Restricted Keys for Third-Party Services

When integrating with third-party platforms that need access to your Stripe data, create a restricted key with only the permissions they require. This limits the damage if the third party is compromised.

### Monitor Key Usage

Review API request logs in the Stripe Dashboard to detect unusual activity. Unexpected spikes in API calls, requests from unknown IP addresses, or operations you did not initiate may indicate a compromised key.

### Separate Keys per Environment

Use different keys for development, staging, and production. Never use live mode keys in development or testing environments.

### Restrict Key Permissions

When using restricted keys, follow the principle of least privilege. Grant only the specific permissions each service needs. For example:

| Service | Recommended Permissions |
|---------|------------------------|
| Analytics dashboard | Charges: Read, Customers: Read |
| Refund processing service | Charges: Read, Refunds: Write |
| Subscription management | Customers: Read/Write, Subscriptions: Read/Write |
| Webhook handler | No API key needed (uses webhook signing secret) |

## Common Support Scenarios

**Customer sees "Invalid API Key provided":**
The key may be expired, revoked, or copied incorrectly. Verify the key exists in the Dashboard and matches the environment (test vs live). A common mistake is using a test mode key in a live mode request or vice versa.

**Authentication error with a key that worked before:**
The key may have been rolled or revoked. Check the Dashboard for key history. If another team member rolled the key, you need the new key.

**"No such customer" or "No such charge" errors:**
This often happens when using a live mode key to access test mode objects (or vice versa). Objects created in test mode do not exist in live mode and vice versa.
