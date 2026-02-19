---
title: "Payment Links"
category: "Payments"
source: "https://docs.stripe.com/payment-links"
---

# Payment Links

## What Are Payment Links?

Payment Links are shareable URLs that open a Stripe-hosted payment page. They let you accept payments without writing any code or building a website. When a customer clicks a Payment Link, they are taken to a checkout page where they can complete the payment.

Each Payment Link generates a unique URL like `https://buy.stripe.com/test_abc123` that you can share via email, text message, social media, QR codes, or embed as a button on a website.

## Payment Links vs. Checkout Sessions

While Payment Links use the same underlying Checkout infrastructure, there are important differences:

| Feature | Payment Links | Checkout Sessions |
|---------|--------------|-------------------|
| Creation | Dashboard or API, reusable | API only, single-use |
| Code required | No | Yes |
| Reusability | Same link works for many customers | Each session is unique per customer |
| Customization | Dashboard settings, limited API options | Full API control over parameters |
| Dynamic pricing | Fixed prices only | Dynamic `price_data` supported |
| Quantity adjustment | Customer can adjust (if enabled) | Set at creation |
| Use case | Quick setup, no-code scenarios | Custom integrations, dynamic carts |

Payment Links are the simplest way to start accepting payments. Checkout Sessions give you more programmatic control.

## Creating Payment Links

### Via the Stripe Dashboard (No Code)

1. Go to **Payment Links** in the Stripe Dashboard.
2. Click **+ New** to create a new link.
3. Add products (create new ones or select existing ones from your catalog).
4. Configure options: allow quantity adjustment, collect shipping, enable promo codes.
5. Click **Create link**.
6. Copy and share the URL.

### Via the API

```python
import stripe

stripe.api_key = "sk_test_your_test_key_here"

# Create a Payment Link with an existing Price
payment_link = stripe.PaymentLink.create(
    line_items=[
        {
            "price": "price_1MotwRLkdIwHu7ixYcPLm5uZ",
            "quantity": 1,
        },
    ],
)

print(f"Payment Link URL: {payment_link.url}")
# Output: https://buy.stripe.com/test_abc123
```

### With Multiple Items

```python
payment_link = stripe.PaymentLink.create(
    line_items=[
        {
            "price": "price_starter_plan",
            "quantity": 1,
        },
        {
            "price": "price_setup_fee",
            "quantity": 1,
        },
    ],
)
```

### With Customization Options

```python
payment_link = stripe.PaymentLink.create(
    line_items=[
        {
            "price": "price_1MotwRLkdIwHu7ixYcPLm5uZ",
            "adjustable_quantity": {
                "enabled": True,
                "minimum": 1,
                "maximum": 10,
            },
            "quantity": 1,
        },
    ],
    after_completion={
        "type": "redirect",
        "redirect": {"url": "https://example.com/thank-you"},
    },
    allow_promotion_codes=True,
    billing_address_collection="required",
    shipping_address_collection={
        "allowed_countries": ["US", "CA", "GB", "DE", "FR"],
    },
    phone_number_collection={"enabled": True},
    custom_fields=[
        {
            "key": "company_name",
            "label": {"type": "custom", "custom": "Company Name"},
            "type": "text",
        },
    ],
    metadata={
        "campaign": "spring_sale_2024",
    },
)
```

## Key Configuration Options

### After Completion Behavior

Control what happens after the customer completes payment:

- **Redirect**: Send the customer to a specific URL on your site.
- **Hosted confirmation**: Display a Stripe-hosted confirmation page (default).

```python
# Redirect after completion
after_completion = {
    "type": "redirect",
    "redirect": {"url": "https://example.com/success"},
}

# Or show hosted confirmation page
after_completion = {
    "type": "hosted_confirmation",
    "hosted_confirmation": {
        "custom_message": "Thank you for your purchase! We'll email your receipt shortly.",
    },
}
```

### Adjustable Quantities

Allow customers to change the quantity on the payment page:

```python
line_items = [
    {
        "price": "price_abc123",
        "quantity": 1,
        "adjustable_quantity": {
            "enabled": True,
            "minimum": 1,
            "maximum": 99,
        },
    },
]
```

### Subscriptions via Payment Links

Payment Links support subscription products. Use a recurring Price:

```python
payment_link = stripe.PaymentLink.create(
    line_items=[
        {
            "price": "price_monthly_subscription",  # A recurring Price object
            "quantity": 1,
        },
    ],
)
```

### Automatic Tax Collection

```python
payment_link = stripe.PaymentLink.create(
    line_items=[{"price": "price_abc123", "quantity": 1}],
    automatic_tax={"enabled": True},
)
```

## Managing Payment Links

### Updating a Payment Link

You can update certain properties of an active Payment Link:

```python
stripe.PaymentLink.modify(
    "plink_1MoC4dLkdIwHu7ixALzrwFwR",
    active=False,  # Deactivate the link
)
```

Updatable fields: `active`, `after_completion`, `allow_promotion_codes`, `custom_fields`, `metadata`, `shipping_address_collection`, `phone_number_collection`.

You cannot change the `line_items` of an existing Payment Link. Create a new one instead.

### Deactivating a Payment Link

```python
stripe.PaymentLink.modify(
    "plink_1MoC4dLkdIwHu7ixALzrwFwR",
    active=False,
)
```

Deactivated links show a message that the link is no longer active. You can reactivate them by setting `active=True`.

### Listing Payment Links

```python
links = stripe.PaymentLink.list(limit=10, active=True)

for link in links.data:
    print(f"{link.id}: {link.url}")
```

## Retrieving Payments from a Link

To see payments made through a specific Payment Link, retrieve the associated Checkout Sessions:

```python
sessions = stripe.checkout.Session.list(
    payment_link="plink_1MoC4dLkdIwHu7ixALzrwFwR",
    limit=20,
)

for session in sessions.data:
    print(f"Session {session.id}: {session.payment_status} - {session.amount_total}")
```

## Use Cases

### Invoicing Clients
Create a Payment Link for the invoice amount and send it via email. The client clicks the link and pays instantly.

### Social Media Sales
Share a Payment Link on Instagram, Twitter, or Facebook to sell products directly from your social media posts.

### QR Codes
Generate a QR code from the Payment Link URL for in-person payments, printed materials, or packaging.

### Email Marketing
Include Payment Links in marketing emails for flash sales, product launches, or upsell campaigns.

### Recurring Donations
Create a subscription Payment Link for recurring donations to nonprofits or creators.

## Webhooks for Payment Links

Payment Links use the same webhook events as Checkout:

- `checkout.session.completed` - Payment was successful.
- `checkout.session.async_payment_succeeded` - Async payment method confirmed.
- `checkout.session.async_payment_failed` - Async payment failed.

The webhook payload includes the `payment_link` field so you can identify which link the payment came from.

## Common Support Questions

**Q: Is there a limit on how many times a Payment Link can be used?**
No. By default, a Payment Link can be used an unlimited number of times by different customers. Each customer who clicks the link gets their own Checkout session.

**Q: Can I set an expiration date on a Payment Link?**
Payment Links do not have a built-in expiration. To stop accepting payments, deactivate the link by setting `active=False`. You can use the `restrictions` parameter to limit the number of completed sessions if you want to auto-deactivate after a certain number of sales.

**Q: Can I customize the payment page's appearance?**
Yes. Payment Links use the same branding settings as Checkout (logo, colors, font), configured in the Stripe Dashboard under Settings > Branding.

**Q: Do Payment Links work for international customers?**
Yes. The payment page automatically localizes to the customer's browser language and shows relevant payment methods for their location (if automatic payment methods are enabled).

**Q: Can I track which marketing campaign a payment came from?**
Yes. Use the `metadata` parameter when creating the link, or append UTM parameters to the URL for analytics tracking. The metadata is available on the resulting Checkout Session.
