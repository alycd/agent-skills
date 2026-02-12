# Custom Attributes System Design

**Date:** 2026-02-08
**Status:** Draft

## Overview

Add support for custom attributes to the customer database, allowing users to upload CSV files with arbitrary columns that get stored alongside standard customer fields. Primary use case is mail merge for email templates using merge tags like `{{last_purchase_date}}`.

## Requirements

### Functional Requirements
- Users upload CSV files with standard + custom columns
- Standard columns (email, first_name, etc.) map to existing customer table columns
- Additional columns become custom attributes stored per customer
- Maximum 10 custom attributes per customer
- Support simple types: text, numbers, dates (no nested structures)
- Upsert behavior: update existing customers by email within account
- Custom attributes merge/update (don't completely replace existing)
- Show available merge tags to users when creating email templates
- Mail merge: replace tags like `{{custom_field}}` with customer values

### Non-Functional Requirements
- Scale to 1M+ customers per account
- Fast mail merge reads (fetching customer data for email generation)
- Fast lookup of available merge tags across all customers
- Read-heavy workload (more email sends than CSV uploads)

## Current State

### Existing Schema

```sql
CREATE TABLE customer.customer (
    id uuid NOT NULL,
    account_id uuid NOT NULL,
    email text NOT NULL,
    first_name text NULL,
    last_name text NULL,
    "version" int4 DEFAULT 0 NOT NULL,
    created_at timestamp NULL,
    updated_at timestamp NULL,
    "source" text NULL,
    status text NOT NULL,
    status_reason text NULL,
    "open" int4 DEFAULT 0 NOT NULL,
    clicked int4 DEFAULT 0 NOT NULL,
    unsubscribed int4 DEFAULT 0 NOT NULL,
    birthday timestamp NULL,
    tags _text NULL,
    currency text NULL,
    country text NULL,
    province text NULL,
    city text NULL,
    address1 text NULL,
    address2 text NULL,
    phone text NULL,
    postal_code text NULL,
    company text NULL,
    timezone text NULL,
    accepts_marketing text NULL,
    orders_count int4 NULL,
    total_spent float4 NULL,
    last_order_id text NULL,
    last_order_name text NULL,
    last_order_date timestamp NULL,
    last_order_price float4 NULL,
    source_id text NULL,
    action_status text NULL,
    unique_opens int4 DEFAULT 0 NOT NULL,
    unique_clicks int4 DEFAULT 0 NOT NULL,
    delivered_count int4 DEFAULT 0 NOT NULL,
    last_open timestamp NULL,
    last_click timestamp NULL,
    last_delivered timestamp NULL,
    entity_id bigserial NOT NULL,
    domain_name varchar(255) NULL,
    last_open_epoch int8 NULL,
    last_click_epoch int8 NULL,
    last_delivered_epoch int8 NULL,
    CONSTRAINT customer_un UNIQUE (account_id, email),
    CONSTRAINT new_customer_pkey PRIMARY KEY (id)
);
```

## Proposed Solution

### Architecture Choice: JSONB + Metadata Table

**Selected approach:** Store custom attributes in a JSONB column on the customers table, with a separate metadata table tracking available attribute names per account.

**Why JSONB + Metadata:**
- ✅ Fast mail merge: single customer fetch, no joins required
- ✅ Fast merge tag lookup: small metadata table, not scanning 1M rows
- ✅ Flexible: handles different attributes per customer
- ✅ PostgreSQL JSONB is highly performant and indexable
- ✅ Simple implementation: one column addition, one new table

**Rejected alternatives:**
- ❌ EAV table: requires joins for mail merge, slow reads
- ❌ JSONB without metadata: slow to find available merge tags at scale
- ❌ Fixed columns: can't handle different attributes per customer

### Database Schema Changes

**1. Add JSONB column to customer table:**

```sql
ALTER TABLE customer.customer
ADD COLUMN custom_attributes JSONB DEFAULT '{}'::jsonb;

-- Index for efficient JSONB operations
CREATE INDEX customer_custom_attributes_idx
ON customer.customer USING gin (custom_attributes);
```

**2. Create metadata tracking table:**

```sql
CREATE TABLE customer.custom_attribute_definition (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL,
    attribute_name TEXT NOT NULL,
    last_seen_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT custom_attribute_definition_un
        UNIQUE (account_id, attribute_name)
);

CREATE INDEX custom_attribute_definition_account_idx
ON customer.custom_attribute_definition(account_id);
```

### CSV Upload Workflow

**High-level process:**

1. **Parse CSV file**
   - Read CSV headers (column names)
   - Validate file format, size limits

2. **Column mapping**
   - Match CSV columns to existing customer table columns (case-insensitive)
   - Remaining columns become custom attributes
   - Known columns: email, first_name, last_name, phone, company, etc.

3. **Process each row**
   - Extract standard fields (matched columns)
   - Extract custom fields (unmatched columns)
   - Build custom_attributes JSON object

4. **Upsert customer**
   - Match by: account_id + email (unique constraint)
   - If exists: UPDATE standard fields + MERGE custom_attributes
   - If new: INSERT with all fields
   - Use PostgreSQL `jsonb_set()` or `||` operator for merge

5. **Update attribute definitions**
   - For each custom attribute name in the CSV
   - Upsert into custom_attribute_definition table
   - Update last_seen_at timestamp

**Example upsert query:**

```sql
INSERT INTO customer.customer (
    id, account_id, email, first_name, last_name,
    custom_attributes, created_at, updated_at
)
VALUES (
    gen_random_uuid(), $1, $2, $3, $4,
    $5::jsonb, NOW(), NOW()
)
ON CONFLICT (account_id, email)
DO UPDATE SET
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    -- Merge JSONB: existing || new (new values override)
    custom_attributes = customer.customer.custom_attributes || EXCLUDED.custom_attributes,
    updated_at = NOW();
```

**Example CSV:**
```csv
email,first_name,last_name,loyalty_tier,last_purchase_date
john@example.com,John,Doe,gold,2024-01-15
jane@example.com,Jane,Smith,silver,2024-02-20
```

**Result in database:**
- email → customer.email
- first_name → customer.first_name
- last_name → customer.last_name
- loyalty_tier, last_purchase_date → customer.custom_attributes JSONB

### Query Patterns

**1. Get available merge tags for an account:**

```sql
SELECT attribute_name
FROM customer.custom_attribute_definition
WHERE account_id = $1
ORDER BY attribute_name;
```

Returns: `['last_purchase_date', 'loyalty_tier', 'vip_status', ...]`

**2. Fetch customer for mail merge:**

```sql
SELECT
    id, email, first_name, last_name,
    custom_attributes
FROM customer.customer
WHERE account_id = $1 AND email = $2;
```

**3. Replace merge tags in email template:**

```javascript
// Example in application code
const customer = fetchCustomer(accountId, email);
let emailBody = template.body; // "Hi {{first_name}}, your tier is {{loyalty_tier}}"

// Replace standard fields
emailBody = emailBody.replace('{{first_name}}', customer.first_name);

// Replace custom attributes
for (const [key, value] of Object.entries(customer.custom_attributes)) {
    emailBody = emailBody.replace(`{{${key}}}`, value);
}
```

**4. Batch fetch for bulk email send:**

```sql
SELECT
    id, email, first_name, last_name,
    custom_attributes
FROM customer.customer
WHERE account_id = $1
    AND email = ANY($2::text[])
ORDER BY email;
```

### Edge Cases & Considerations

**1. Merge behavior for custom attributes**
- Use JSONB `||` operator to merge
- New values override existing values for same key
- Existing keys not in CSV are preserved
- Example: existing `{a: 1, b: 2}` + new `{b: 3, c: 4}` = `{a: 1, b: 3, c: 4}`

**2. Type handling**
- All custom attribute values stored as JSON strings, numbers, or booleans
- Dates stored as ISO 8601 strings: "2024-01-15T00:00:00Z"
- Application layer handles type conversion/formatting

**3. Attribute name normalization**
- Store attribute names as lowercase? Or preserve case?
- **Recommendation:** Preserve case from CSV, match case-insensitive for merge tags
- Store original case in `custom_attribute_definition.attribute_name`

**4. Maximum attributes limit**
- Enforce 10 custom attributes per customer
- Validate during CSV upload
- Reject or warn if row has >10 custom columns

**5. Missing/empty values**
- Empty CSV cells: store as `null` or omit from JSONB?
- **Recommendation:** Omit from JSONB (don't store null values)
- Cleaner JSONB objects, easier to check existence

**6. Attribute cleanup**
- If an attribute hasn't been seen in X months, remove from definitions?
- **Recommendation:** Keep all historical attributes, let users manually delete
- Or add "archived" flag to definitions table

**7. Performance considerations**
- GIN index on JSONB supports key existence and value queries
- For 1M+ customers, fetching one customer by email is fast (indexed)
- Bulk email sends: batch fetch customers to minimize round trips
- Attribute definitions table stays small (max ~100-1000 unique attributes per account)

**8. Migration strategy**
- Zero downtime: column addition with default value
- No data migration needed for existing customers (default `{}`)
- Backward compatible: application handles null/missing custom_attributes

## Future Enhancements (Out of Scope)

- Custom attribute data types/validation (enforce date format, number ranges)
- Per-attribute metadata (display name, description, data type)
- Attribute groups/categories for organization
- Audit log of custom attribute changes
- API endpoints for managing custom attributes directly (not via CSV)
- Conditional merge tags (e.g., `{{loyalty_tier | default: 'bronze'}}`)

## Success Metrics

- CSV upload processing time: < 5 seconds for 10k rows
- Mail merge customer fetch: < 50ms per customer
- Available merge tags query: < 100ms for 1M customers
- Zero data loss during upsert operations
- Support 10 custom attributes per customer

## Open Questions

- [ ] Should we validate attribute names (no spaces, special chars)?
- [ ] Size limits on custom attribute values? (e.g., max 1KB per value)
- [ ] Rate limiting on CSV uploads?
- [ ] Should we support deleting custom attributes (not just updating)?
- [ ] UI for manually adding/editing custom attributes per customer?
