---
title: "Customers"
category: "Core Concepts"
source: "https://docs.stripe.com/customers"
---

# Customers

The Customer object is a core resource in Stripe that represents a buyer. Customers allow you to store payment methods, track payment history, manage subscriptions, and maintain a persistent relationship across multiple transactions.

## Why Use Customer Objects?

Without Customer objects, every payment is a one-off transaction with no link to prior activity. Customer objects enable:

- **Stored payment methods**: Save cards and bank accounts for future use without re-collecting details.
- **Recurring billing**: Attach subscriptions to customers for automatic recurring charges.
- **Payment history**: View all charges, invoices, and subscriptions associated with a customer in one place.
- **Metadata and organization**: Store arbitrary data on the customer object for your internal systems.
- **Customer balance**: Apply credits or prepaid balances to future invoices.

## Creating a Customer

```python
import stripe

stripe.api_key = "sk_test_..."

# Create a basic customer
customer = stripe.Customer.create(
    name="Jane Smith",
    email="jane@example.com",
    phone="+14155551234",
    description="Premium plan customer since 2025",
    metadata={
        "internal_id": "usr_98765",
        "plan": "premium",
        "signup_source": "website",
    },
)

print(customer.id)  # cus_...
```

### Customer Fields

| Field | Description |
|-------|-------------|
| `name` | The customer's full name. |
| `email` | Email address. Used for invoice delivery and receipt sending. |
| `phone` | Phone number in E.164 format. |
| `description` | An internal description or note. Not visible to the customer. |
| `metadata` | A dictionary of up to 50 key-value pairs. Keys max 40 characters, values max 500 characters. |
| `address` | The customer's billing address object (line1, line2, city, state, postal_code, country). |
| `shipping` | Shipping address and recipient information. |
| `balance` | An integer representing the customer's balance in the smallest currency unit. Negative = credit, positive = amount owed. |
| `tax_exempt` | Tax exemption status: `none`, `exempt`, or `reverse`. |
| `preferred_locales` | An ordered list of preferred locales for communication (e.g., `["en", "fr"]`). |

## Storing Payment Methods on Customers

The most common use of Customer objects is storing payment methods for future charges. You attach a PaymentMethod to a Customer, making it available for future payments without re-collecting card details.

### Attach a Payment Method

```python
# Attach a PaymentMethod to a Customer
stripe.PaymentMethod.attach(
    "pm_1234567890",
    customer="cus_1234567890",
)

# Set it as the customer's default payment method
stripe.Customer.modify(
    "cus_1234567890",
    invoice_settings={
        "default_payment_method": "pm_1234567890",
    },
)
```

### Using a SetupIntent for Secure Storage

To securely collect and store payment details (especially with SCA/3DS), use a SetupIntent:

```python
# Create a SetupIntent for a customer
setup_intent = stripe.SetupIntent.create(
    customer="cus_1234567890",
    payment_method_types=["card"],
    usage="off_session",  # Indicates the card will be used for future off-session payments
)

# After the customer completes authentication on the frontend,
# the PaymentMethod is automatically attached to the customer.
print(setup_intent.client_secret)  # Send this to your frontend
```

### Listing a Customer's Payment Methods

```python
# List all card payment methods for a customer
payment_methods = stripe.Customer.list_payment_methods(
    "cus_1234567890",
    type="card",
)

for pm in payment_methods.data:
    card = pm.card
    print(f"{pm.id}: {card.brand} ending in {card.last4}, exp {card.exp_month}/{card.exp_year}")
```

## Default Payment Method

A customer can have a default payment method set at two levels:

1. **Invoice-level default** (`invoice_settings.default_payment_method`): Used for subscriptions and invoices. This is the most commonly used default.
2. **Customer-level default** (`default_source`): A legacy field from the Sources API. For new integrations, use `invoice_settings.default_payment_method` instead.

When a subscription creates an invoice, Stripe charges the invoice-level default payment method. If none is set, it falls back to the customer-level default source.

## Customer Metadata

Metadata is one of the most useful features of Customer objects. You can store up to 50 key-value pairs on each customer, which enables you to link Stripe customers to your internal systems without maintaining a separate mapping table.

```python
# Create a customer with metadata
customer = stripe.Customer.create(
    email="alex@example.com",
    metadata={
        "user_id": "12345",
        "tier": "enterprise",
        "account_manager": "Sarah K.",
        "contract_end": "2026-12-31",
    },
)

# Update metadata later
stripe.Customer.modify(
    customer.id,
    metadata={
        "tier": "enterprise_plus",  # Update an existing key
        "renewal_status": "confirmed",  # Add a new key
    },
)

# Remove a metadata key by setting it to an empty string
stripe.Customer.modify(
    customer.id,
    metadata={
        "account_manager": "",  # This removes the key
    },
)
```

## Searching Customers

Stripe provides a Search API for finding customers based on various criteria:

```python
# Search customers by email
results = stripe.Customer.search(
    query="email:'jane@example.com'",
)

# Search by metadata
results = stripe.Customer.search(
    query="metadata['user_id']:'12345'",
)

# Search by name (partial match)
results = stripe.Customer.search(
    query="name~'Jane'",
)

# Combine search criteria
results = stripe.Customer.search(
    query="email:'jane@example.com' AND metadata['tier']:'enterprise'",
)

for customer in results.data:
    print(f"{customer.id}: {customer.name} ({customer.email})")
```

The Search API supports these operators:
- `:'value'` -- exact match
- `~'value'` -- contains (substring match)
- `>'value'` and `<'value'` -- comparison (for dates and numbers)

Note: The Search API indexes data asynchronously. Newly created or updated customers may take up to a few minutes to appear in search results.

## Customer Balance

Customer balance represents credits or debits applied to a customer's account. It affects how invoices are paid:

- **Negative balance** (credit): Applied automatically to the customer's next invoice, reducing the amount charged to their payment method.
- **Positive balance** (debit): Represents an amount the customer owes, added to their next invoice.

```python
# Apply a $50 credit to a customer's balance
stripe.Customer.create_balance_transaction(
    "cus_1234567890",
    amount=-5000,  # Negative = credit (in cents)
    currency="usd",
    description="Goodwill credit for service disruption",
)

# Check the customer's current balance
customer = stripe.Customer.retrieve("cus_1234567890")
print(f"Balance: {customer.balance}")  # -5000 means $50 credit

# List balance transactions
transactions = stripe.Customer.list_balance_transactions(
    "cus_1234567890",
)
for txn in transactions.data:
    print(f"{txn.amount} {txn.currency} -- {txn.description}")
```

## Linking Customers to Subscriptions

Subscriptions are always associated with a Customer. When you create a subscription, you specify the customer and the price (pricing plan):

```python
# Create a subscription for a customer
subscription = stripe.Subscription.create(
    customer="cus_1234567890",
    items=[
        {"price": "price_monthly_premium"},
    ],
    default_payment_method="pm_1234567890",
)
```

All invoices generated by the subscription are linked to the customer, and Stripe automatically charges the customer's default payment method on each billing cycle.

## Deleting Customers

Deleting a customer permanently removes the customer object and cancels any active subscriptions:

```python
# Delete a customer (irreversible)
deleted = stripe.Customer.delete("cus_1234567890")
print(deleted.deleted)  # True
```

Deletion is permanent. All associated subscriptions are canceled, and the customer's payment methods are detached. Past charges and invoices remain in your Stripe account for record-keeping.

## Common Support Scenarios

**Customer says they were charged but have no account:**
The customer may have made a guest checkout without a Customer object. Search by email or card fingerprint in the Dashboard to find the associated payments.

**Duplicate customers:**
If a customer has multiple Customer objects (e.g., from multiple sign-ups), you can merge them by moving subscriptions and payment methods to a single Customer and deleting the duplicates.

**Customer wants to update their card:**
Create a new SetupIntent for the customer, have them complete the flow, then set the new PaymentMethod as their default. The old PaymentMethod can be detached.
