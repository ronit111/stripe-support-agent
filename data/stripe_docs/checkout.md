---
title: "Stripe Checkout"
category: "Payments"
source: "https://docs.stripe.com/payments/checkout"
---

# Stripe Checkout

## What Is Stripe Checkout?

Stripe Checkout is a pre-built, Stripe-hosted payment page that provides a complete checkout experience. Instead of building your own payment form, you redirect customers to a secure page hosted by Stripe where they enter their payment details. After completing (or canceling) the payment, customers are redirected back to your website.

Checkout handles payment collection, validation, error messages, mobile responsiveness, localization into 30+ languages, and compliance with regulations like Strong Customer Authentication (SCA) in Europe.

## Checkout Modes

Checkout supports three modes, set via the `mode` parameter:

### `payment` - One-Time Payments
Collects a single payment from the customer. Use this for e-commerce orders, donations, or any one-time transaction.

### `subscription` - Recurring Payments
Creates a subscription that charges the customer on a recurring basis. Requires at least one recurring price in the `line_items`.

### `setup` - Save Payment Method
Collects payment method details and saves them for future use without charging the customer immediately. Creates a SetupIntent behind the scenes.

## Creating a Checkout Session

### One-Time Payment Example

```python
import stripe

stripe.api_key = "sk_test_your_test_key_here"

session = stripe.checkout.Session.create(
    mode="payment",
    line_items=[
        {
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "Premium T-Shirt",
                    "description": "Comfortable cotton t-shirt",
                    "images": ["https://example.com/tshirt.jpg"],
                },
                "unit_amount": 2500,  # $25.00
            },
            "quantity": 2,
        },
    ],
    success_url="https://example.com/success?session_id={CHECKOUT_SESSION_ID}",
    cancel_url="https://example.com/cancel",
)

# Redirect the customer to session.url
print(f"Checkout URL: {session.url}")
```

### Subscription Example

```python
session = stripe.checkout.Session.create(
    mode="subscription",
    line_items=[
        {
            "price": "price_1MoBy5LkdIwHu7ixZhnattbh",  # Pre-created recurring Price
            "quantity": 1,
        },
    ],
    success_url="https://example.com/success?session_id={CHECKOUT_SESSION_ID}",
    cancel_url="https://example.com/cancel",
)
```

### Using Pre-Created Prices

If you have products and prices defined in the Stripe Dashboard or via the API, reference them by ID:

```python
session = stripe.checkout.Session.create(
    mode="payment",
    line_items=[
        {
            "price": "price_1MotwRLkdIwHu7ixYcPLm5uZ",
            "quantity": 1,
        },
    ],
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
)
```

## Key Parameters

| Parameter | Description |
|-----------|-------------|
| `mode` | `"payment"`, `"subscription"`, or `"setup"`. Required. |
| `line_items` | Array of items the customer is purchasing. Required for `payment` and `subscription` modes. |
| `success_url` | URL to redirect to after successful payment. Required. Use `{CHECKOUT_SESSION_ID}` as a template variable. |
| `cancel_url` | URL to redirect to if the customer cancels. Required. |
| `customer` | ID of an existing Customer to associate with the session. |
| `customer_email` | Pre-fill the email field. Ignored if `customer` is set. |
| `payment_method_types` | Limit accepted payment methods. Omit to use automatic payment methods. |
| `allow_promotion_codes` | Set to `True` to allow customers to enter promo codes. |
| `shipping_address_collection` | Collect shipping addresses. Pass `allowed_countries` array. |
| `billing_address_collection` | Set to `"required"` to always collect billing address. |
| `metadata` | Key-value pairs attached to the Checkout Session. |
| `expires_after` | Minutes until the session expires (minimum 30, maximum 1440, default 1440 / 24 hours). |
| `locale` | Force a specific locale (e.g., `"fr"` for French). Defaults to browser locale. |

## Customization Options

### Branding

Customize the appearance of your Checkout page in the Stripe Dashboard under **Settings > Branding**:

- Upload your logo and icon
- Set brand colors (background, button, accent)
- Choose a font

### Collecting Additional Information

```python
session = stripe.checkout.Session.create(
    mode="payment",
    line_items=[{"price": "price_abc123", "quantity": 1}],
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
    # Collect shipping address
    shipping_address_collection={
        "allowed_countries": ["US", "CA", "GB"],
    },
    # Collect phone number
    phone_number_collection={"enabled": True},
    # Require billing address
    billing_address_collection="required",
    # Allow promo codes
    allow_promotion_codes=True,
    # Add custom fields
    custom_fields=[
        {
            "key": "delivery_instructions",
            "label": {"type": "custom", "custom": "Delivery Instructions"},
            "type": "text",
            "optional": True,
        },
    ],
)
```

### Tax Collection

Stripe Checkout supports automatic tax calculation via Stripe Tax:

```python
session = stripe.checkout.Session.create(
    mode="payment",
    line_items=[{"price": "price_abc123", "quantity": 1}],
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
    automatic_tax={"enabled": True},
)
```

## Handling Completion with Webhooks

While the `success_url` redirect confirms payment to the customer, you should always use webhooks to fulfill orders on the server side. The redirect can fail (browser closes, network issues), so webhooks are the reliable method.

```python
# Listen for the checkout.session.completed event
@app.route("/webhook", methods=["POST"])
def webhook():
    event = stripe.Webhook.construct_event(
        request.get_data(),
        request.headers.get("Stripe-Signature"),
        endpoint_secret,
    )

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # Retrieve line items
        line_items = stripe.checkout.Session.list_line_items(session["id"])

        # Fulfill the order
        fulfill_order(session, line_items)

    return "", 200
```

Key webhook events for Checkout:

| Event | When It Fires |
|-------|---------------|
| `checkout.session.completed` | Customer completed the Checkout form. For card payments, the payment is typically already successful. |
| `checkout.session.async_payment_succeeded` | For async payment methods (bank debits), the payment has been confirmed. |
| `checkout.session.async_payment_failed` | An async payment method failed after the session completed. |
| `checkout.session.expired` | The session expired before the customer completed checkout. |

## Retrieving Session Data

After a customer completes checkout, retrieve the session to access payment details:

```python
session = stripe.checkout.Session.retrieve(
    "cs_test_abc123",
    expand=["line_items", "payment_intent"],
)

print(f"Payment status: {session.payment_status}")
print(f"Customer email: {session.customer_details.email}")
print(f"Amount total: {session.amount_total}")
```

## Guest Checkout vs. Customer Accounts

By default, Checkout operates in guest mode. To associate the session with a Stripe Customer:

```python
# Use an existing customer
session = stripe.checkout.Session.create(
    customer="cus_ABC123",
    # ...
)

# Or let Stripe create a new customer
session = stripe.checkout.Session.create(
    customer_creation="always",
    # ...
)
```

## Common Support Questions

**Q: Can I embed Checkout directly in my page instead of redirecting?**
Yes. Stripe offers an embedded Checkout mode using `ui_mode="embedded"`. This renders the Checkout form inside an iframe on your page rather than redirecting to stripe.com.

**Q: Why did my Checkout session expire?**
Checkout sessions expire after 24 hours by default (configurable via `expires_after`). If the customer did not complete payment within that window, the session expires and a `checkout.session.expired` webhook event fires.

**Q: Can I change the price or items after creating a session?**
No. Checkout Sessions are immutable once created. You need to create a new session with the updated items.

**Q: How do I handle abandoned checkouts?**
Listen for the `checkout.session.expired` webhook event. You can use the `customer_email` or `customer` from the expired session to send a follow-up email encouraging the customer to complete their purchase.

**Q: Can Checkout collect recurring and one-time payments together?**
Yes, in `subscription` mode, you can include both recurring prices and one-time prices in the `line_items` array. The one-time items are charged immediately along with the first subscription payment.
