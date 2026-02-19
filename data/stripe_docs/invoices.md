---
title: "Stripe Invoices"
category: "Billing"
source: "https://docs.stripe.com/invoicing"
---

# Stripe Invoices

Invoices are statements of amounts owed by a customer. They are generated automatically for subscriptions or created manually for one-off charges. Stripe handles the full invoice lifecycle from creation through payment collection.

## How Invoices Work

An invoice collects one or more **line items** that represent charges to a customer. Each line item has an amount, description, and optional metadata. Stripe generates a hosted invoice page where customers can view and pay invoices, and can also send invoice emails automatically.

### Automatic vs Manual Invoices

**Automatic invoices** are created by Stripe as part of the subscription billing cycle. At each billing interval, Stripe generates an invoice, finalizes it, and attempts to charge the customer's default payment method.

**Manual invoices** (also called one-off invoices) are created by you via the API or Dashboard for ad-hoc charges, consulting fees, project milestones, or any non-recurring billing.

```python
import stripe

# Create a manual invoice
invoice = stripe.Invoice.create(
    customer="cus_ABC123",
    collection_method="send_invoice",  # Email the invoice to the customer
    days_until_due=30,
)

# Add line items
stripe.InvoiceItem.create(
    customer="cus_ABC123",
    invoice=invoice.id,
    amount=15000,  # $150.00
    currency="usd",
    description="Consulting services - January 2025",
)

stripe.InvoiceItem.create(
    customer="cus_ABC123",
    invoice=invoice.id,
    amount=5000,  # $50.00
    currency="usd",
    description="Travel expenses",
)

# Finalize and send
stripe.Invoice.finalize_invoice(invoice.id)
stripe.Invoice.send_invoice(invoice.id)
```

## Invoice Lifecycle

Invoices progress through the following statuses:

| Status | Description |
|--------|-------------|
| `draft` | The invoice is editable. Line items can be added, modified, or removed. Not visible to the customer. |
| `open` | The invoice has been finalized and is awaiting payment. No further edits to line items are allowed. |
| `paid` | Payment has been collected successfully. |
| `void` | The invoice has been voided and will not be collected. Useful for correcting mistakes. |
| `uncollectible` | The invoice has been marked as uncollectible after all payment attempts have been exhausted. |

### Status Flow

```
draft → open → paid
           ↓
         void
           ↓
       uncollectible
```

For automatic (subscription) invoices, the flow is typically:
```
draft (briefly) → open → paid
```

Stripe auto-finalizes subscription invoices approximately one hour before the payment attempt, giving webhooks time to modify the invoice if needed.

## Collection Methods

### `charge_automatically`

Stripe charges the customer's default payment method when the invoice is finalized. This is the default for subscription invoices.

```python
invoice = stripe.Invoice.create(
    customer="cus_ABC123",
    collection_method="charge_automatically",
)
```

### `send_invoice`

Stripe sends the invoice to the customer via email with a link to the hosted invoice page. The customer pays manually. You must specify `days_until_due`.

```python
invoice = stripe.Invoice.create(
    customer="cus_ABC123",
    collection_method="send_invoice",
    days_until_due=30,
)
```

## Line Items

Every invoice contains one or more line items. For subscription invoices, line items are generated automatically from the subscription's prices. For manual invoices, you add line items via the InvoiceItem API.

```python
# Add a line item with a price
stripe.InvoiceItem.create(
    customer="cus_ABC123",
    price="price_consulting_hourly",
    quantity=10,
)

# Add a line item with a custom amount
stripe.InvoiceItem.create(
    customer="cus_ABC123",
    amount=7500,
    currency="usd",
    description="Custom development work",
)
```

Pending invoice items (those not attached to a specific invoice) are automatically included in the customer's next invoice.

## Invoice Customization

### Custom Fields

Add up to four custom fields to display on the invoice PDF and hosted page.

```python
stripe.Invoice.create(
    customer="cus_ABC123",
    custom_fields=[
        {"name": "Purchase Order", "value": "PO-12345"},
        {"name": "Project", "value": "Website Redesign"},
    ],
)
```

### Footer and Memo

```python
stripe.Invoice.create(
    customer="cus_ABC123",
    footer="Thank you for your business. Payment terms: Net 30.",
    description="Invoice for Q1 2025 services",
)
```

### Account-Level Defaults

Set default invoice settings at the account level in the Stripe Dashboard under Settings > Billing > Invoices. These include default payment terms, footer text, numbering scheme, and memo.

## Paying Invoices

### Pay an Open Invoice via API

```python
# Pay using the customer's default payment method
stripe.Invoice.pay("in_ABC123")

# Pay using a specific payment method
stripe.Invoice.pay(
    "in_ABC123",
    payment_method="pm_CARD123",
)
```

### Hosted Invoice Page

Every finalized invoice has a `hosted_invoice_url` field containing a link to a Stripe-hosted page where the customer can view and pay the invoice. This page supports multiple payment methods based on your account configuration.

```python
invoice = stripe.Invoice.retrieve("in_ABC123")
print(invoice.hosted_invoice_url)
# https://invoice.stripe.com/i/acct_xxx/inv_xxx
```

## Voiding and Marking Uncollectible

### Void an Invoice

Voiding an invoice cancels it without collecting payment. The invoice remains on record but is no longer payable. Use this to correct invoicing mistakes.

```python
stripe.Invoice.void_invoice("in_ABC123")
```

Voiding a subscription invoice does not cancel the subscription. The next billing cycle will generate a new invoice.

### Mark as Uncollectible

If all payment attempts fail and you decide not to pursue collection, mark the invoice as uncollectible.

```python
stripe.Invoice.mark_uncollectible("in_ABC123")
```

## Credit Notes

Credit notes allow you to adjust an invoice after it has been finalized. They can issue a credit to the customer's balance, refund to the original payment method, or create an out-of-band credit.

```python
credit_note = stripe.CreditNote.create(
    invoice="in_ABC123",
    lines=[
        {
            "type": "invoice_line_item",
            "invoice_line_item": "il_LINEITEM123",
            "quantity": 1,
        },
    ],
    reason="order_change",
)
```

## Invoice Webhooks

Key events to listen for:

| Event | Description |
|-------|-------------|
| `invoice.created` | A new invoice has been created. For subscriptions, this fires ~1 hour before payment. |
| `invoice.finalized` | The invoice has been finalized and is no longer editable. |
| `invoice.paid` | Payment was successfully collected. |
| `invoice.payment_failed` | The payment attempt failed. |
| `invoice.payment_action_required` | The payment requires additional customer action (e.g., 3D Secure). |
| `invoice.voided` | The invoice was voided. |
| `invoice.marked_uncollectible` | The invoice was marked as uncollectible. |
| `invoice.sent` | The invoice email was sent to the customer. |
| `invoice.upcoming` | Fires a few days before a subscription invoice is created, allowing you to add extra line items. |

### Modifying Upcoming Invoices

The `invoice.upcoming` event fires a few days before the next subscription invoice is created. You can use this window to add one-off charges or credits:

```python
# In your webhook handler for invoice.upcoming
stripe.InvoiceItem.create(
    customer=event.data.object.customer,
    amount=2500,
    currency="usd",
    description="Platform fee",
)
```

## Common Support Scenarios

**Customer says they were double-charged**: Check whether two separate invoices were generated (e.g., a proration invoice and a regular cycle invoice). Review the invoice list for the customer with `stripe.Invoice.list(customer="cus_ABC123")`.

**Invoice shows $0**: Zero-dollar invoices can occur when a 100% discount coupon is applied, or when proration credits exactly offset new charges. These invoices are finalized and marked as paid automatically.

**Customer did not receive the invoice email**: Verify the customer's email address on the Customer object. Check that `collection_method` is `send_invoice`. You can resend via `stripe.Invoice.send_invoice("in_ABC123")`.

**Need to edit a finalized invoice**: Finalized invoices cannot be edited. Void the invoice and create a new one, or issue a credit note to adjust the amount.

**Pending invoice items**: If a customer has pending invoice items (InvoiceItems not attached to a specific invoice), these will be swept into the next automatically-generated invoice. To view pending items: `stripe.InvoiceItem.list(customer="cus_ABC123", pending=True)`.
