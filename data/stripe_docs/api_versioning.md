---
title: "Stripe API Versioning"
category: "Developer Experience"
source: "https://docs.stripe.com/api/versioning"
---

# Stripe API Versioning

Stripe uses API versioning to manage changes to the API over time. When Stripe introduces backwards-incompatible changes, they release a new version. Your account is pinned to a specific version, and you can upgrade at your own pace.

## How Versioning Works

Every Stripe API request is handled by a specific API version. The version determines the structure of API responses, the behavior of API endpoints, and which fields and features are available.

### Version Format

Stripe versions are date-based strings in the format `YYYY-MM-DD`, representing the date the version was released. For example: `2024-06-20`, `2024-04-10`, `2023-10-16`.

### Version Precedence

When Stripe processes an API request, the version is determined by this priority:

1. **Per-request version header**: If you include `Stripe-Version` in the request headers, that version is used.
2. **API key version (pinned version)**: Your account's pinned version, which is set when you first make an API request or when you explicitly upgrade in the Dashboard.
3. **Library default**: Stripe's official libraries bundle a default version that matches the library release.

## Pinned Version

When you create a Stripe account and make your first API request, your account is pinned to the latest API version at that time. All subsequent requests use this version by default unless you override it.

You can view and change your pinned version in the Dashboard under Developers > API version.

### Checking Your Current Version

```python
import stripe

# The stripe library sends its bundled version by default
# To see what version you're using:
print(stripe.api_version)
# e.g., "2024-06-20"
```

The version used for a request is also returned in the response headers as `Stripe-Version`.

## Overriding the Version Per Request

You can specify a different API version for individual requests using the `Stripe-Version` header. This is useful for testing newer versions before upgrading your account.

```python
import stripe

# Override version for a single request
customer = stripe.Customer.create(
    email="test@example.com",
    stripe_version="2024-06-20",
)

# Or set it globally for the library
stripe.api_version = "2024-06-20"
```

Using the `stripe-version` header does not change your account's pinned version. It only affects that specific request.

## Upgrading Your API Version

### Step 1: Review the Changelog

Before upgrading, review the API changelog to understand what changed between your current version and the target version. The changelog is available at https://docs.stripe.com/upgrades and in the Dashboard under Developers > API version.

Each changelog entry describes:
- What changed
- How it affects API responses
- What you need to update in your code

### Step 2: Test with Version Headers

Use per-request version overrides to test the new version without changing your account's pinned version.

```python
# Test a specific endpoint with the new version
customers = stripe.Customer.list(
    limit=10,
    stripe_version="2024-06-20",
)

# Verify your code handles the new response format
for customer in customers.auto_paging_iter():
    process_customer(customer)
```

### Step 3: Upgrade in the Dashboard

Once you've verified compatibility, upgrade your pinned version in the Dashboard under Developers > API version. Click "Upgrade version" and confirm.

**This change is immediate and affects all API requests that don't include a per-request version override.** There is no way to downgrade your pinned version through the Dashboard. Contact Stripe support if you need to roll back.

### Step 4: Update Your Library

After upgrading your API version, update the Stripe library in your application to a version that supports the new API version.

```bash
pip install --upgrade stripe
```

## Backwards Compatibility

Stripe considers the following changes to be **backwards-compatible** and may make them without releasing a new version:

- Adding new API endpoints
- Adding new optional request parameters to existing endpoints
- Adding new fields to existing API responses
- Adding new values to existing enums (e.g., new event types, new status values)
- Changing the order of fields in responses
- Adding new webhook event types
- Changing the length or format of opaque strings (IDs, error messages)

Stripe considers the following changes to be **backwards-incompatible** and will release a new version:

- Removing or renaming API endpoints
- Removing or renaming request parameters
- Removing or renaming response fields
- Changing the type of a response field (e.g., string to object)
- Changing the default value of a parameter
- Changing error codes or response status codes
- Changing the structure of nested objects in responses

### Implications for Your Code

Because Stripe may add new fields and enum values at any time, your code should:

- **Not fail on unknown fields**: Ignore fields you don't recognize rather than throwing errors.
- **Handle unknown enum values**: Use a default or fallback case for switch/match statements on Stripe fields.
- **Not depend on field ordering**: Process response objects by key, not by position.

```python
# Good: handles unknown statuses gracefully
status = subscription["status"]
if status == "active":
    grant_access()
elif status == "past_due":
    send_reminder()
elif status in ("canceled", "unpaid"):
    revoke_access()
else:
    # Unknown status - log and handle gracefully
    log_unknown_status(status)
    revoke_access()  # Safe default
```

## Webhook Versioning

Webhook events are sent using **your account's pinned API version**, not any per-request version override. This means the event payload structure matches your pinned version.

If you upgrade your API version, webhook payloads will immediately reflect the new version's format. Make sure your webhook handlers are updated before upgrading.

```python
# Webhook payloads always use your account's pinned version
# If your pinned version changes the structure of an invoice object,
# your webhook handler must be updated to match
```

## API Version in Stripe Libraries

Each version of the Stripe client library (Python, Node, Ruby, etc.) bundles a default API version. The library sends this version with requests if you haven't set one explicitly.

| Library Action | Version Used |
|---------------|--------------|
| No version set by you | Library's bundled default version |
| `stripe.api_version` set | Your specified version |
| Per-request `stripe_version` | The per-request version for that call only |

When upgrading the library, check the library changelog for the bundled API version to ensure compatibility.

```python
# Check the library version
import stripe
print(stripe.VERSION)       # Library version, e.g., "7.0.0"
print(stripe.api_version)   # API version the library will use
```

## Rolling vs Pinned Versions in Testing

In test mode, your pinned version applies the same as in live mode. Use test mode to verify API version compatibility before upgrading in production.

```python
# Test mode uses the same versioning as live mode
stripe.api_key = "sk_test_..."
# The same pinned version and overrides apply
```

## Common Support Scenarios

**Response format changed unexpectedly**: Check if your Stripe library was updated, as newer libraries may bundle a different API version. Also verify your account's pinned version in the Dashboard.

**Webhook payload format changed**: Webhook payloads use your account's pinned version. If you recently upgraded your API version, webhook payloads will reflect the new format. Update your webhook handlers accordingly.

**API returns fields not in the documentation**: You may be reading documentation for a different API version. Make sure the documentation version matches your pinned version. Stripe's documentation lets you select a specific API version.

**Need to roll back to a previous version**: You cannot downgrade your pinned version through the Dashboard. Contact Stripe support for assistance. In the meantime, use per-request version headers to revert specific calls to the old version format.

**Library and API version mismatch**: If your Stripe library is significantly older than your pinned API version, some fields or behaviors may not be accessible through the library. Upgrade the library to a version that supports your pinned API version.

**Different API behavior in test vs live mode**: Both modes use the same pinned version. If behavior differs, check that you're using the same library version, the same per-request overrides, and that your test and live mode account settings match.
