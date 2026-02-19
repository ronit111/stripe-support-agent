---
title: "Currencies"
category: "Payments"
source: "https://docs.stripe.com/currencies"
---

# Currencies

## Multi-Currency Support Overview

Stripe supports processing payments in 135+ currencies, allowing businesses to charge customers in their local currency. This reduces friction at checkout and can improve conversion rates, since customers are more likely to complete a purchase when they see prices in a familiar currency.

## Presentment Currency vs. Settlement Currency

Understanding these two concepts is essential:

### Presentment Currency
The currency the customer sees and pays in. This is the `currency` parameter you set when creating a PaymentIntent, Checkout Session, or other payment object. For example, a European customer might pay in EUR.

### Settlement Currency
The currency Stripe uses to deposit funds into your bank account (your payout currency). This is determined by your Stripe account's country and bank account configuration. For example, a US-based business receives payouts in USD.

When the presentment currency differs from the settlement currency, Stripe automatically converts the funds at the current exchange rate. Stripe charges a currency conversion fee (typically 1% on top of the exchange rate for most accounts, or 2% for currency conversions involving non-default settlement currencies).

### Example

A US-based business charges a customer 50.00 EUR:
1. The customer pays 50.00 EUR (presentment currency).
2. Stripe converts EUR to USD at the prevailing exchange rate.
3. The business receives approximately $54.25 USD (settlement currency), minus the conversion fee and standard processing fees.

## How Amounts Work

Stripe represents amounts as integers in the smallest currency unit. For most currencies, this is cents (or equivalent).

```python
import stripe

# Charging $25.50 USD — amount is in cents
stripe.PaymentIntent.create(
    amount=2550,
    currency="usd",
)

# Charging 30.00 EUR — amount is in euro cents
stripe.PaymentIntent.create(
    amount=3000,
    currency="eur",
)
```

## Zero-Decimal Currencies

Some currencies do not have a sub-unit (no cents equivalent). For these currencies, the amount represents the full currency unit.

| Currency | Code | Example |
|----------|------|---------|
| Japanese Yen | `jpy` | `amount=1000` means 1,000 JPY |
| Korean Won | `krw` | `amount=50000` means 50,000 KRW |
| Chilean Peso | `clp` | `amount=15000` means 15,000 CLP |
| Vietnamese Dong | `vnd` | `amount=500000` means 500,000 VND |
| Paraguayan Guarani | `pyg` | `amount=100000` means 100,000 PYG |
| Rwandan Franc | `rwf` | `amount=5000` means 5,000 RWF |
| Ugandan Shilling | `ugx` | `amount=100000` means 100,000 UGX |
| Djiboutian Franc | `djf` | `amount=2000` means 2,000 DJF |
| Guinean Franc | `gnf` | `amount=10000` means 10,000 GNF |
| Vanuatu Vatu | `vuv` | `amount=5000` means 5,000 VUV |
| XAF (CFA Franc BEAC) | `xaf` | `amount=5000` means 5,000 XAF |
| XOF (CFA Franc BCEAO) | `xof` | `amount=5000` means 5,000 XOF |
| XPF (CFP Franc) | `xpf` | `amount=5000` means 5,000 XPF |

### Three-Decimal Currencies

A small number of currencies use three decimal places. Stripe treats these as having the smallest unit be 1/1000:

| Currency | Code | Example |
|----------|------|---------|
| Bahraini Dinar | `bhd` | `amount=1000` means 1.000 BHD |
| Kuwaiti Dinar | `kwd` | `amount=1000` means 1.000 KWD |
| Omani Rial | `omr` | `amount=1000` means 1.000 OMR |

## Minimum Charge Amounts

Stripe enforces minimum charge amounts that vary by currency. Payments below these amounts will be rejected. Here are common minimums:

| Currency | Minimum Amount | Equivalent |
|----------|---------------|------------|
| USD | 50 | $0.50 |
| EUR | 50 | 0.50 EUR |
| GBP | 30 | 0.30 GBP |
| CAD | 50 | $0.50 CAD |
| AUD | 50 | $0.50 AUD |
| JPY | 50 | 50 JPY |
| CHF | 50 | 0.50 CHF |
| HKD | 400 | $4.00 HKD |
| SGD | 50 | $0.50 SGD |
| SEK | 300 | 3.00 SEK |
| DKK | 250 | 2.50 DKK |
| NOK | 300 | 3.00 NOK |
| MXN | 1000 | $10.00 MXN |
| BRL | 50 | R$0.50 BRL |
| INR | 50 | 0.50 INR |

These minimums apply to the total charge amount, including any application fees.

## Supported Currencies by Payment Method

Not all payment methods support all currencies:

### Cards
Cards support the widest range of currencies (135+). Major currencies include: USD, EUR, GBP, CAD, AUD, JPY, CHF, SEK, NOK, DKK, SGD, HKD, NZD, BRL, MXN, INR, and many more.

### ACH Direct Debit
Only supports `usd`.

### SEPA Direct Debit
Only supports `eur`.

### iDEAL
Only supports `eur`.

### Bancontact
Only supports `eur`.

### Alipay
Supports `cny`, `aud`, `cad`, `eur`, `gbp`, `hkd`, `jpy`, `sgd`, `usd`, and others.

### Apple Pay / Google Pay
Support the same currencies as the underlying card networks.

## Currency Conversion and Exchange Rates

When a presentment currency differs from the settlement currency, Stripe handles conversion automatically:

```python
# A US-based business charging in EUR
# Stripe converts the settlement to USD automatically
payment_intent = stripe.PaymentIntent.create(
    amount=4999,       # 49.99 EUR
    currency="eur",    # Customer pays in EUR
    # Settlement happens in USD based on account settings
)
```

### Exchange Rate Details

- Stripe uses rates from financial markets at the time of the charge.
- The conversion fee (typically 1%) is applied on top of the mid-market exchange rate.
- Converted amounts are visible on the Balance Transaction object.

```python
# Retrieve balance transaction to see conversion details
balance_transaction = stripe.BalanceTransaction.retrieve(
    "txn_1MoC4dLkdIwHu7ixALzrwFwR"
)

print(f"Amount: {balance_transaction.amount}")            # In settlement currency
print(f"Currency: {balance_transaction.currency}")        # Settlement currency
print(f"Exchange rate: {balance_transaction.exchange_rate}")
```

## Multi-Currency Payouts

By default, Stripe settles in your account's default currency. If you add bank accounts in multiple currencies (e.g., a USD account and a EUR account), you can receive payouts in those currencies directly, avoiding conversion fees.

To set up multi-currency payouts:
1. Go to **Settings > Payouts** in the Stripe Dashboard.
2. Add a bank account denominated in the desired currency.
3. Stripe will automatically route payouts in matching currencies to the appropriate bank account.

## Common Support Questions

**Q: Why was my charge rejected for an invalid amount?**
Check that the amount meets the minimum charge for the specified currency. Also verify that you are using the correct smallest unit. For zero-decimal currencies like JPY, `amount=100` means 100 JPY (not 1 JPY).

**Q: Can I refund in a different currency than the original charge?**
No. Refunds are always issued in the same currency as the original charge. If currency conversion was involved, Stripe converts the refund amount at the current exchange rate, which may differ from the original rate.

**Q: How do I avoid currency conversion fees?**
Set up a bank account in the same currency as the charges you receive. For example, if you frequently charge in EUR, add a EUR-denominated bank account. Stripe will pay out EUR directly without conversion.

**Q: Where can I see the exchange rate that was used?**
The exchange rate is recorded on the BalanceTransaction object. You can view this in the Stripe Dashboard under a payment's details, or retrieve it via the API.

**Q: Does Stripe support cryptocurrency payments?**
Stripe does not directly process cryptocurrency payments as a standard payment method. Check Stripe's current documentation for the latest on crypto-related features, as offerings may evolve.
