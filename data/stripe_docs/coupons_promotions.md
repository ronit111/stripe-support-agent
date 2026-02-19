---
title: "Coupons and Promotion Codes"
category: "Billing"
source: "https://docs.stripe.com/billing/subscriptions/coupons"
---

# Coupons and Promotion Codes

Stripe provides two related mechanisms for offering discounts: **coupons** and **promotion codes**. Coupons define the discount itself (amount, duration, applicability). Promotion codes are customer-facing codes that reference a coupon and add distribution controls like redemption limits and expiration dates.

## Coupons vs Promotion Codes

| Feature | Coupon | Promotion Code |
|---------|--------|----------------|
| What it is | The discount definition (amount, duration) | A customer-facing code string that applies a coupon |
| Applied via | API or Dashboard (directly to a customer or subscription) | Customer enters it at checkout or via the API |
| Customer-visible code | No (uses internal ID like `coupon_ABC`) | Yes (e.g., `SAVE20`, `WELCOME10`) |
| Redemption limits | Limited (max_redemptions on the coupon) | Per-code limits, first-time customer restrictions, expiration dates |
| Use case | Internal discounts, account credits, sales team overrides | Marketing campaigns, public promotions, referral programs |

In practice, most customer-facing discount flows use promotion codes. Coupons are applied directly when you're managing discounts programmatically.

## Creating Coupons

### Percentage Discount

```python
import stripe

coupon = stripe.Coupon.create(
    percent_off=20,
    duration="repeating",
    duration_in_months=3,
    name="20% Off for 3 Months",
)
```

### Fixed Amount Discount

```python
coupon = stripe.Coupon.create(
    amount_off=1000,  # $10.00 off
    currency="usd",
    duration="once",
    name="$10 Off First Invoice",
)
```

### Coupon Parameters

| Parameter | Description |
|-----------|-------------|
| `percent_off` | Percentage discount (1-100). Mutually exclusive with `amount_off`. |
| `amount_off` | Fixed amount discount in the smallest currency unit (cents for USD). Mutually exclusive with `percent_off`. |
| `currency` | Required when using `amount_off`. The currency for the discount. |
| `duration` | How long the discount applies. See duration section below. |
| `duration_in_months` | Required when `duration` is `repeating`. Number of months the discount applies. |
| `max_redemptions` | Maximum number of times the coupon can be redeemed across all customers. |
| `redeem_by` | Unix timestamp after which the coupon can no longer be redeemed. |
| `name` | Display name for the coupon (visible to customers on invoices). |
| `applies_to` | Restrict the coupon to specific products. |

## Duration

The `duration` parameter controls how many billing cycles the discount applies:

### `once`

The discount applies to a single invoice only. After the first invoice with the discount, subsequent invoices are charged at full price.

```python
coupon = stripe.Coupon.create(
    percent_off=50,
    duration="once",
    name="50% Off First Month",
)
```

### `repeating`

The discount applies for a specific number of months. You must also set `duration_in_months`.

```python
coupon = stripe.Coupon.create(
    percent_off=25,
    duration="repeating",
    duration_in_months=6,
    name="25% Off for 6 Months",
)
```

### `forever`

The discount applies for the lifetime of the subscription, as long as it remains active.

```python
coupon = stripe.Coupon.create(
    percent_off=15,
    duration="forever",
    name="15% Lifetime Discount",
)
```

## Applying Coupons

### To a Subscription

```python
# Apply at creation
subscription = stripe.Subscription.create(
    customer="cus_ABC123",
    items=[{"price": "price_pro_monthly"}],
    coupon="coupon_ABC",
)

# Apply to an existing subscription
stripe.Subscription.modify(
    "sub_ABC123",
    coupon="coupon_ABC",
)

# Remove a coupon from a subscription
stripe.Subscription.modify(
    "sub_ABC123",
    coupon="",  # Empty string removes the coupon
)
```

### To a Customer

Applying a coupon to a customer applies it to all of that customer's future subscription invoices.

```python
stripe.Customer.modify(
    "cus_ABC123",
    coupon="coupon_ABC",
)
```

### To a Specific Invoice

```python
# Add a discount to a draft invoice
stripe.Invoice.modify(
    "in_ABC123",
    discounts=[{"coupon": "coupon_ABC"}],
)
```

### Product-Specific Coupons

Restrict a coupon so it only discounts specific products on the invoice, rather than the entire invoice total.

```python
coupon = stripe.Coupon.create(
    percent_off=30,
    duration="once",
    applies_to={"products": ["prod_ADDON_1", "prod_ADDON_2"]},
    name="30% Off Add-ons",
)
```

## Creating Promotion Codes

Promotion codes wrap a coupon with a customer-facing code string and additional controls.

```python
# Create a coupon first
coupon = stripe.Coupon.create(
    percent_off=20,
    duration="repeating",
    duration_in_months=3,
)

# Create a promotion code for that coupon
promo = stripe.PromotionCode.create(
    coupon=coupon.id,
    code="WELCOME20",
    max_redemptions=500,
    expires_at=1735689600,  # Expires Dec 31, 2024
)
```

### Promotion Code Parameters

| Parameter | Description |
|-----------|-------------|
| `coupon` | The coupon ID this promotion code references (required). |
| `code` | The customer-facing code string. If not provided, Stripe generates a random code. |
| `max_redemptions` | Maximum total redemptions for this specific promotion code. |
| `expires_at` | Unix timestamp after which the code is no longer valid. |
| `active` | Whether the code is currently active (default: `true`). Set to `false` to deactivate. |
| `restrictions.first_time_transaction` | If `true`, only first-time customers can use this code. |
| `restrictions.minimum_amount` | Minimum order amount required to use the code. |
| `restrictions.minimum_amount_currency` | Currency for the minimum amount. |
| `customer` | Restrict this code to a single customer. |

### Restricting to First-Time Customers

```python
promo = stripe.PromotionCode.create(
    coupon=coupon.id,
    code="NEWUSER25",
    restrictions={
        "first_time_transaction": True,
    },
)
```

### Minimum Amount Requirement

```python
promo = stripe.PromotionCode.create(
    coupon=coupon.id,
    code="SAVE10",
    restrictions={
        "minimum_amount": 5000,           # $50.00 minimum
        "minimum_amount_currency": "usd",
    },
)
```

### Single-Customer Code

```python
promo = stripe.PromotionCode.create(
    coupon=coupon.id,
    code="VIPRONIT",
    customer="cus_ABC123",  # Only this customer can redeem
)
```

## Applying Promotion Codes

### At Checkout (Stripe Checkout)

```python
session = stripe.checkout.Session.create(
    mode="subscription",
    line_items=[{"price": "price_pro_monthly", "quantity": 1}],
    allow_promotion_codes=True,  # Shows a promo code input field
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
)
```

### Via the API

```python
subscription = stripe.Subscription.create(
    customer="cus_ABC123",
    items=[{"price": "price_pro_monthly"}],
    promotion_code="promo_CODE123",  # Use the promotion code ID, not the string
)
```

To find a promotion code by its string:

```python
codes = stripe.PromotionCode.list(code="WELCOME20")
promo_code_id = codes.data[0].id  # "promo_CODE123"
```

## Deactivating and Managing Codes

```python
# Deactivate a promotion code
stripe.PromotionCode.modify(
    "promo_CODE123",
    active=False,
)

# Delete a coupon (also invalidates all associated promotion codes)
stripe.Coupon.delete("coupon_ABC")

# List all promotion codes for a coupon
codes = stripe.PromotionCode.list(coupon="coupon_ABC")
```

## Stacking Discounts

By default, Stripe applies one discount per subscription or invoice. To stack multiple discounts on a single invoice, use the `discounts` array:

```python
stripe.Subscription.create(
    customer="cus_ABC123",
    items=[{"price": "price_pro_monthly"}],
    discounts=[
        {"coupon": "coupon_LOYALTY_10"},
        {"coupon": "coupon_ANNUAL_5"},
    ],
)
```

Discounts are applied sequentially. A 20% discount followed by a 10% discount on a $100 charge results in $72 ($100 * 0.80 * 0.90), not $70.

## Common Support Scenarios

**Promotion code says "invalid"**: Check that the code is `active`, has not exceeded `max_redemptions`, has not passed its `expires_at` date, and that the customer meets any restrictions (first-time, minimum amount, specific customer).

**Discount not appearing on invoice**: Verify the coupon's `duration`. If set to `once`, it only applies to the first invoice. If the subscription has already received one discounted invoice, subsequent invoices will be at full price.

**Customer wants to change their coupon**: Remove the existing coupon by setting `coupon=""` on the subscription, then apply the new coupon. The new coupon's duration starts fresh.

**Coupon applies to wrong line items**: If the coupon should only apply to specific products, use the `applies_to` parameter. Without it, the coupon discounts the entire invoice.

**Multiple customers using a single-use code**: The `max_redemptions` on a promotion code limits the total number of customers who can use it. If set to 1, only one customer can redeem it. The `max_redemptions` on the underlying coupon is a separate, global limit.

**Discount on annual plan seems wrong**: For percentage-off coupons with `duration="repeating"`, the `duration_in_months` counts actual months, not billing periods. On an annual subscription, a 3-month repeating coupon would still expire after 3 months (well before the first renewal).
