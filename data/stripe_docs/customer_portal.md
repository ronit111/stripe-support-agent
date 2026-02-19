---
title: "Stripe Customer Portal"
category: "Billing"
source: "https://docs.stripe.com/customer-management/portal"
---

# Stripe Customer Portal

The Stripe customer portal is a pre-built, Stripe-hosted interface that lets your customers manage their subscriptions and billing details without you building a custom UI. Customers can update payment methods, view invoice history, manage subscriptions, and download receipts.

## What Customers Can Manage

The portal supports the following self-service actions, each of which can be enabled or disabled in your portal configuration:

### Payment Methods
- Add new credit/debit cards
- Set a default payment method
- Remove saved payment methods

### Subscriptions
- Cancel subscriptions (immediately or at period end)
- Switch between plans (upgrades and downgrades)
- Update subscription quantities (e.g., number of seats)
- Pause subscriptions (if enabled)
- Resume paused subscriptions

### Invoices and Billing
- View past invoices
- Download invoice PDFs
- View upcoming invoice details

### Customer Information
- Update billing address
- Update email address
- Update tax IDs

## Configuring the Portal

Portal configuration is done via the Stripe Dashboard (Settings > Billing > Customer portal) or the API. You create a **portal configuration** that defines which features are available and how they behave.

```python
import stripe

# Create a portal configuration
configuration = stripe.billing_portal.Configuration.create(
    business_profile={
        "headline": "Manage your subscription",
        "privacy_policy_url": "https://example.com/privacy",
        "terms_of_service_url": "https://example.com/terms",
    },
    features={
        "customer_update": {
            "enabled": True,
            "allowed_updates": ["email", "address", "tax_id"],
        },
        "payment_method_update": {
            "enabled": True,
        },
        "invoice_history": {
            "enabled": True,
        },
        "subscription_cancel": {
            "enabled": True,
            "mode": "at_period_end",  # or "immediately"
            "cancellation_reason": {
                "enabled": True,
                "options": [
                    "too_expensive",
                    "missing_features",
                    "switched_service",
                    "unused",
                    "other",
                ],
            },
        },
        "subscription_update": {
            "enabled": True,
            "default_allowed_updates": ["price", "quantity"],
            "proration_behavior": "create_prorations",
            "products": [
                {
                    "product": "prod_BASIC",
                    "prices": ["price_basic_monthly", "price_basic_annual"],
                },
                {
                    "product": "prod_PRO",
                    "prices": ["price_pro_monthly", "price_pro_annual"],
                },
                {
                    "product": "prod_ENTERPRISE",
                    "prices": ["price_enterprise_monthly", "price_enterprise_annual"],
                },
            ],
        },
    },
)
```

### Configuration Options in Detail

**`subscription_cancel.mode`**:
- `at_period_end`: The subscription stays active until the end of the current billing period. The customer continues to have access until then.
- `immediately`: The subscription is canceled right away. Depending on your settings, this may or may not issue a prorated refund.

**`subscription_update.proration_behavior`**:
- `create_prorations`: Proration line items are added to the next invoice.
- `always_invoice`: An invoice is generated immediately for the proration amount.
- `none`: No proration. The change takes effect at the next billing cycle.

**`subscription_update.products`**: Defines which plans customers can switch between. Only the products and prices listed here will be available as upgrade/downgrade options.

## Creating Portal Sessions

To send a customer to the portal, create a portal session and redirect them to the session URL.

```python
# Create a portal session
session = stripe.billing_portal.Session.create(
    customer="cus_ABC123",
    return_url="https://example.com/account",
)

# Redirect the customer to:
print(session.url)
# https://billing.stripe.com/p/session/xxx
```

The `return_url` is where the customer is redirected when they click "Back" or finish managing their account.

### Portal Session Options

```python
# Create a session that deep-links to subscription management
session = stripe.billing_portal.Session.create(
    customer="cus_ABC123",
    return_url="https://example.com/account",
    flow_data={
        "type": "subscription_cancel",
        "subscription_cancel": {
            "subscription": "sub_ABC123",
        },
    },
)

# Create a session for updating payment method
session = stripe.billing_portal.Session.create(
    customer="cus_ABC123",
    return_url="https://example.com/account",
    flow_data={
        "type": "payment_method_update",
    },
)
```

### Flow Types

The `flow_data.type` parameter lets you deep-link to a specific portal page:

| Flow Type | Description |
|-----------|-------------|
| `payment_method_update` | Go directly to payment method management. |
| `subscription_cancel` | Go directly to the cancellation flow for a specific subscription. |
| `subscription_update` | Go directly to the plan switching flow. |
| `subscription_update_confirm` | Go directly to the confirmation step of a plan switch. |

## Customization

### Branding

The portal automatically uses your Stripe account's branding settings (logo, colors, icon). Configure these in the Dashboard under Settings > Branding.

### Multiple Configurations

You can create multiple portal configurations for different use cases:

```python
# Configuration for basic plan customers (no upgrade to enterprise)
basic_config = stripe.billing_portal.Configuration.create(
    features={
        "subscription_update": {
            "enabled": True,
            "products": [
                {
                    "product": "prod_BASIC",
                    "prices": ["price_basic_monthly", "price_basic_annual"],
                },
                {
                    "product": "prod_PRO",
                    "prices": ["price_pro_monthly", "price_pro_annual"],
                },
            ],
        },
        # ... other features
    },
)

# Use a specific configuration when creating the session
session = stripe.billing_portal.Session.create(
    customer="cus_ABC123",
    return_url="https://example.com/account",
    configuration=basic_config.id,
)
```

### Default Configuration

One configuration is marked as the default. If you don't specify a `configuration` when creating a session, the default is used. Set the default in the Dashboard or via the API:

```python
stripe.billing_portal.Configuration.modify(
    "bpc_CONFIG123",
    default_return_url="https://example.com/account",
    is_default=True,
)
```

## Portal Webhooks

The portal triggers standard Stripe webhook events when customers take actions:

| Customer Action | Webhook Event |
|----------------|---------------|
| Cancels subscription | `customer.subscription.updated` (with `cancel_at_period_end=true`) or `customer.subscription.deleted` |
| Switches plan | `customer.subscription.updated` |
| Updates quantity | `customer.subscription.updated` |
| Adds payment method | `payment_method.attached` |
| Removes payment method | `payment_method.detached` |
| Updates email | `customer.updated` |
| Updates address | `customer.updated` |
| Updates tax ID | `customer.tax_id.created` or `customer.tax_id.deleted` |

There is also a portal-specific event:
- `billing_portal.session.created` - Fires when a portal session is created.

## Common Support Scenarios

**Portal link expired**: Portal sessions are valid for a limited time. Create a new session via the API and send the customer the fresh URL. Sessions are single-use and expire once accessed or after a timeout.

**Customer cannot see the option to cancel**: Verify that `subscription_cancel` is enabled in your portal configuration. Check that the customer has an active subscription.

**Customer cannot switch plans**: Ensure that `subscription_update` is enabled and that the target product/price is listed in the `products` array of your configuration. Only explicitly listed products and prices appear as options.

**Customer updated payment method but subscription still failing**: The portal updates the default payment method on the Customer object. If the subscription has a specific payment method set (overriding the customer default), the new payment method won't be used. Check the subscription's `default_payment_method` field.

**Need to customize the portal beyond what Stripe offers**: The portal supports branding (logo, colors) and feature toggles, but does not support custom HTML/CSS, additional fields, or custom workflows. For deeper customization, you need to build your own management UI using the Stripe API.

**Portal shows wrong prices or plans**: Check your portal configuration's `products` array. The portal only displays products and prices explicitly listed there. If you created new prices, update the portal configuration to include them.
