---
title: "Stripe API Pagination"
category: "Developer Experience"
source: "https://docs.stripe.com/api/pagination"
---

# Stripe API Pagination

Stripe's list API endpoints use cursor-based pagination to return results in manageable chunks. All list endpoints return a maximum of 100 objects per request, with a default of 10. Pagination is handled through cursor parameters that point to specific objects in the result set.

## How Cursor-Based Pagination Works

Unlike offset-based pagination (e.g., `page=2&per_page=10`), cursor-based pagination uses object IDs as cursors. You request objects that come after or before a specific object in the sorted list. This approach is more efficient for large datasets and avoids the performance issues and inconsistencies that offset-based pagination can cause when data changes between requests.

Stripe returns results sorted by creation date, with the most recently created objects appearing first (descending order).

## Pagination Parameters

Every list endpoint supports these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer (1-100) | The number of objects to return. Default is 10. Maximum is 100. |
| `starting_after` | string | A cursor for forward pagination. Provide the ID of the last object from the previous page to fetch the next page. |
| `ending_before` | string | A cursor for backward pagination. Provide the ID of the first object from the current page to fetch the previous page. |

### `starting_after` and `ending_before` are mutually exclusive. You can only use one per request.

## Response Format

Every list endpoint returns a response with this structure:

```json
{
  "object": "list",
  "url": "/v1/customers",
  "has_more": true,
  "data": [
    {
      "id": "cus_Z99",
      "object": "customer",
      "created": 1706745600,
      ...
    },
    {
      "id": "cus_Z98",
      "object": "customer",
      "created": 1706745500,
      ...
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `object` | Always `"list"`. |
| `url` | The URL for this list endpoint. |
| `has_more` | `true` if there are more results beyond this page. `false` if this is the last page. |
| `data` | An array of Stripe objects (up to `limit` items). |

## Forward Pagination (Most Common)

To paginate forward through results (from newest to oldest), use `starting_after` with the ID of the last object on the current page.

```python
import stripe

# Fetch the first page
page1 = stripe.Customer.list(limit=10)

# Check if there are more results
if page1.has_more:
    # Get the ID of the last customer on this page
    last_id = page1.data[-1].id

    # Fetch the next page
    page2 = stripe.Customer.list(limit=10, starting_after=last_id)
```

### Full Forward Pagination Example

```python
import stripe

def get_all_customers():
    """Retrieve all customers using manual pagination."""
    all_customers = []
    has_more = True
    starting_after = None

    while has_more:
        params = {"limit": 100}
        if starting_after:
            params["starting_after"] = starting_after

        response = stripe.Customer.list(**params)
        all_customers.extend(response.data)

        has_more = response.has_more
        if response.data:
            starting_after = response.data[-1].id

    return all_customers
```

## Backward Pagination

To paginate backward (from older to newer), use `ending_before` with the ID of the first object on the current page.

```python
# If you have page 2 and want to go back to page 1
first_id_on_page2 = page2.data[0].id
page1 = stripe.Customer.list(limit=10, ending_before=first_id_on_page2)
```

Backward pagination is less common. It's mainly useful for building "Previous" page navigation in UIs.

## Auto-Pagination in Libraries

Stripe's official client libraries provide auto-pagination helpers that handle the cursor logic automatically. This is the recommended approach for iterating over large datasets.

### Python Auto-Pagination

```python
import stripe

# auto_paging_iter() handles all pagination automatically
for customer in stripe.Customer.list(limit=100).auto_paging_iter():
    process_customer(customer)

# With filters
for charge in stripe.Charge.list(
    limit=100,
    created={"gte": 1704067200},  # Created after Jan 1, 2024
).auto_paging_iter():
    process_charge(charge)
```

The `auto_paging_iter()` method:
- Fetches pages automatically as you iterate.
- Uses `limit=100` per request (regardless of what you pass, though you should pass 100 for clarity).
- Handles the `starting_after` cursor internally.
- Stops when `has_more` is `false`.

### Converting to a List

```python
# Fetch all objects as a list (careful with large datasets - loads everything into memory)
all_customers = list(stripe.Customer.list(limit=100).auto_paging_iter())

# Better: process in batches
batch = []
for customer in stripe.Customer.list(limit=100).auto_paging_iter():
    batch.append(customer)
    if len(batch) >= 500:
        process_batch(batch)
        batch = []

if batch:
    process_batch(batch)
```

## Filtering and Pagination

List endpoints support various filter parameters alongside pagination. Filters narrow the result set before pagination is applied.

### Common Filter Parameters

```python
# Filter by creation date
invoices = stripe.Invoice.list(
    limit=100,
    created={
        "gte": 1704067200,  # After Jan 1, 2024
        "lt": 1706745600,   # Before Feb 1, 2024
    },
)

# Filter by status
subscriptions = stripe.Subscription.list(
    limit=100,
    status="active",
)

# Filter by customer
charges = stripe.Charge.list(
    limit=100,
    customer="cus_ABC123",
)

# Combine filters with auto-pagination
for invoice in stripe.Invoice.list(
    limit=100,
    customer="cus_ABC123",
    status="paid",
    created={"gte": 1704067200},
).auto_paging_iter():
    process_invoice(invoice)
```

### The `created` Filter

Most list endpoints support filtering by `created` timestamp:

| Operator | Description |
|----------|-------------|
| `created[gt]` | Created after this timestamp (exclusive). |
| `created[gte]` | Created at or after this timestamp (inclusive). |
| `created[lt]` | Created before this timestamp (exclusive). |
| `created[lte]` | Created at or before this timestamp (inclusive). |

## Search vs List

For some object types, Stripe provides a Search API that supports more flexible queries. Search endpoints use a different pagination mechanism (using `next_page` tokens rather than `starting_after`).

```python
# Search API (different pagination model)
result = stripe.Customer.search(
    query="email:'test@example.com'",
)

# Search pagination uses next_page
if result.has_more:
    next_result = stripe.Customer.search(
        query="email:'test@example.com'",
        page=result.next_page,
    )
```

Search and List are different APIs. Don't mix their pagination parameters.

## Performance Best Practices

### Use the Maximum Limit

Always set `limit=100` to minimize the number of API requests. Each request counts toward your rate limit.

```python
# Good: fewer API calls
stripe.Customer.list(limit=100)

# Avoid: 10x more API calls for the same data
stripe.Customer.list(limit=10)
```

### Use Filters to Narrow Results

Rather than fetching everything and filtering client-side, use Stripe's filter parameters to reduce the result set.

```python
# Good: let Stripe filter server-side
paid_invoices = stripe.Invoice.list(
    limit=100,
    status="paid",
    customer="cus_ABC123",
)

# Avoid: fetching all invoices and filtering client-side
all_invoices = stripe.Invoice.list(limit=100)
paid_invoices = [inv for inv in all_invoices if inv.status == "paid"]
```

### Don't Fetch Everything Into Memory

For large datasets, process objects as you iterate rather than loading them all into a list.

```python
# Good: streaming processing
for sub in stripe.Subscription.list(limit=100).auto_paging_iter():
    update_record(sub)

# Avoid with large datasets: loading everything into memory
all_subs = list(stripe.Subscription.list(limit=100).auto_paging_iter())
```

### Avoid Parallel Pagination

Don't paginate the same list from multiple threads simultaneously, as new objects created between requests can cause items to be skipped or duplicated.

## Common Support Scenarios

**Missing objects in pagination**: If objects are created or deleted while you're paginating, you might see duplicates or miss items. For critical data processing, use date-range filters (`created[gte]` and `created[lt]`) to page over a fixed window of data.

**Pagination seems to loop forever**: Check that you're updating the `starting_after` cursor correctly on each iteration. If you always pass the same cursor, you'll fetch the same page repeatedly.

**Results not in expected order**: List endpoints return results in reverse chronological order (newest first). If you need oldest-first, collect all results and reverse them, or use `ending_before` pagination.

**Rate limit errors during pagination**: You're making too many requests too quickly. Add a small delay between pages, or increase your `limit` to 100 to reduce the total number of requests.

**`has_more` is `true` but next page is empty**: This is rare but can happen if objects are deleted between requests. Check for an empty `data` array and stop iterating.

**Auto-pagination not available**: Make sure you're using a recent version of the Stripe library. Auto-pagination was added in `stripe-python` 2.x. Upgrade with `pip install --upgrade stripe`.
