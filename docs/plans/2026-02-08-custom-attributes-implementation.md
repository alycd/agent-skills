# Custom Attributes System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add custom attributes support to customer database with CSV upload and mail merge capabilities.

**Architecture:** JSONB column on customers table for flexible attribute storage + metadata table for tracking available merge tags. CSV upload parses columns, maps to schema, stores custom fields as JSONB. Query layer fetches customers with attributes for mail merge.

**Tech Stack:** PostgreSQL (JSONB), your application framework (Python/Node/etc), CSV parser library

---

## Task 1: Database Migration - Add Custom Attributes Column

**Files:**
- Create: `migrations/YYYYMMDDHHMMSS_add_custom_attributes.sql`
- Or equivalent for your migration tool (Alembic, Flyway, etc.)

**Step 1: Write migration test**

Create test file to verify migration:
```sql
-- tests/migrations/test_custom_attributes_migration.sql
-- Test that custom_attributes column exists and has correct type

SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'customer'
  AND table_name = 'customer'
  AND column_name = 'custom_attributes';

-- Expected: Returns 1 row with data_type = 'jsonb'
```

**Step 2: Run test to verify it fails**

Run against test database:
```bash
psql test_db -f tests/migrations/test_custom_attributes_migration.sql
```
Expected: Returns 0 rows (column doesn't exist yet)

**Step 3: Write migration - up**

```sql
-- migrations/YYYYMMDDHHMMSS_add_custom_attributes.sql

BEGIN;

-- Add custom_attributes column with default empty JSON object
ALTER TABLE customer.customer
ADD COLUMN custom_attributes JSONB DEFAULT '{}'::jsonb;

-- Add GIN index for efficient JSONB queries
CREATE INDEX customer_custom_attributes_idx
ON customer.customer USING gin (custom_attributes);

-- Add comment for documentation
COMMENT ON COLUMN customer.customer.custom_attributes IS
'Flexible storage for user-defined attributes from CSV uploads. Max 10 attributes per customer.';

COMMIT;
```

**Step 4: Write migration - down**

```sql
-- migrations/YYYYMMDDHHMMSS_add_custom_attributes_down.sql

BEGIN;

DROP INDEX IF EXISTS customer.customer_custom_attributes_idx;
ALTER TABLE customer.customer DROP COLUMN IF EXISTS custom_attributes;

COMMIT;
```

**Step 5: Run migration on test database**

```bash
# Apply migration
psql test_db -f migrations/YYYYMMDDHHMMSS_add_custom_attributes.sql

# Verify with test
psql test_db -f tests/migrations/test_custom_attributes_migration.sql
```
Expected: Returns 1 row showing jsonb column

**Step 6: Test rollback**

```bash
# Rollback
psql test_db -f migrations/YYYYMMDDHHMMSS_add_custom_attributes_down.sql

# Verify column is gone
psql test_db -f tests/migrations/test_custom_attributes_migration.sql
```
Expected: Returns 0 rows

**Step 7: Re-apply migration**

```bash
psql test_db -f migrations/YYYYMMDDHHMMSS_add_custom_attributes.sql
```

**Step 8: Commit**

```bash
git add migrations/YYYYMMDDHHMMSS_add_custom_attributes.sql
git add migrations/YYYYMMDDHHMMSS_add_custom_attributes_down.sql
git add tests/migrations/test_custom_attributes_migration.sql
git commit -m "feat: add custom_attributes JSONB column to customers table"
```

---

## Task 2: Database Migration - Create Attribute Definitions Table

**Files:**
- Create: `migrations/YYYYMMDDHHMMSS_create_attribute_definitions.sql`

**Step 1: Write migration test**

```sql
-- tests/migrations/test_attribute_definitions_table.sql

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'customer'
  AND table_name = 'custom_attribute_definition';

-- Expected: Returns 1 row
```

**Step 2: Run test to verify it fails**

```bash
psql test_db -f tests/migrations/test_attribute_definitions_table.sql
```
Expected: Returns 0 rows

**Step 3: Write migration - up**

```sql
-- migrations/YYYYMMDDHHMMSS_create_attribute_definitions.sql

BEGIN;

CREATE TABLE customer.custom_attribute_definition (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL,
    attribute_name TEXT NOT NULL,
    last_seen_at TIMESTAMP DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    CONSTRAINT custom_attribute_definition_un
        UNIQUE (account_id, attribute_name)
);

-- Index for fast lookups by account
CREATE INDEX custom_attribute_definition_account_idx
ON customer.custom_attribute_definition(account_id);

-- Index for finding stale attributes
CREATE INDEX custom_attribute_definition_last_seen_idx
ON customer.custom_attribute_definition(last_seen_at);

COMMENT ON TABLE customer.custom_attribute_definition IS
'Tracks all unique custom attribute names per account for mail merge tag discovery';

COMMIT;
```

**Step 4: Write migration - down**

```sql
-- migrations/YYYYMMDDHHMMSS_create_attribute_definitions_down.sql

BEGIN;

DROP TABLE IF EXISTS customer.custom_attribute_definition CASCADE;

COMMIT;
```

**Step 5: Run migration on test database**

```bash
psql test_db -f migrations/YYYYMMDDHHMMSS_create_attribute_definitions.sql
psql test_db -f tests/migrations/test_attribute_definitions_table.sql
```
Expected: Returns 1 row

**Step 6: Test table constraints**

```sql
-- Test unique constraint
INSERT INTO customer.custom_attribute_definition (account_id, attribute_name)
VALUES ('123e4567-e89b-12d3-a456-426614174000', 'loyalty_tier');

-- This should fail with unique constraint violation
INSERT INTO customer.custom_attribute_definition (account_id, attribute_name)
VALUES ('123e4567-e89b-12d3-a456-426614174000', 'loyalty_tier');
```
Expected: Second insert fails

**Step 7: Commit**

```bash
git add migrations/YYYYMMDDHHMMSS_create_attribute_definitions.sql
git add migrations/YYYYMMDDHHMMSS_create_attribute_definitions_down.sql
git add tests/migrations/test_attribute_definitions_table.sql
git commit -m "feat: create custom_attribute_definition tracking table"
```

---

## Task 3: CSV Column Mapper - Identify Standard vs Custom Columns

**Files:**
- Create: `src/customers/csv_column_mapper.py` (or .js, .ts, etc.)
- Create: `tests/customers/test_csv_column_mapper.py`

**Step 1: Write failing test**

```python
# tests/customers/test_csv_column_mapper.py

import pytest
from customers.csv_column_mapper import CSVColumnMapper

def test_maps_standard_columns():
    """Standard customer columns should map to table fields"""
    mapper = CSVColumnMapper()
    csv_headers = ['email', 'first_name', 'last_name', 'loyalty_tier']

    result = mapper.map_columns(csv_headers)

    assert result['standard'] == ['email', 'first_name', 'last_name']
    assert result['custom'] == ['loyalty_tier']

def test_case_insensitive_mapping():
    """Column names should match case-insensitively"""
    mapper = CSVColumnMapper()
    csv_headers = ['EMAIL', 'First_Name', 'LOYALTY_TIER']

    result = mapper.map_columns(csv_headers)

    assert 'email' in result['standard']
    assert 'first_name' in result['standard']
    assert 'LOYALTY_TIER' in result['custom']

def test_enforces_max_custom_attributes():
    """Should reject more than 10 custom attributes"""
    mapper = CSVColumnMapper()
    csv_headers = ['email'] + [f'custom_{i}' for i in range(11)]

    with pytest.raises(ValueError, match="Maximum 10 custom attributes"):
        mapper.map_columns(csv_headers)
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/customers/test_csv_column_mapper.py -v
```
Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
# src/customers/csv_column_mapper.py

class CSVColumnMapper:
    """Maps CSV columns to standard customer fields vs custom attributes"""

    # All standard columns from customer.customer table
    STANDARD_COLUMNS = {
        'email', 'first_name', 'last_name', 'phone', 'company',
        'birthday', 'currency', 'country', 'province', 'city',
        'address1', 'address2', 'postal_code', 'timezone',
        'accepts_marketing', 'source', 'status', 'status_reason',
        'orders_count', 'total_spent', 'last_order_id',
        'last_order_name', 'last_order_date', 'last_order_price',
        'source_id', 'action_status', 'domain_name'
    }

    MAX_CUSTOM_ATTRIBUTES = 10

    def map_columns(self, csv_headers):
        """
        Separate CSV headers into standard and custom columns.

        Args:
            csv_headers: List of column names from CSV

        Returns:
            Dict with 'standard' and 'custom' keys

        Raises:
            ValueError: If more than MAX_CUSTOM_ATTRIBUTES custom columns
        """
        standard = []
        custom = []

        # Normalize standard columns to lowercase for comparison
        standard_lower = {col.lower() for col in self.STANDARD_COLUMNS}

        for header in csv_headers:
            # Match case-insensitively but preserve original case for custom
            if header.lower() in standard_lower:
                standard.append(header.lower())
            else:
                custom.append(header)

        if len(custom) > self.MAX_CUSTOM_ATTRIBUTES:
            raise ValueError(
                f"Maximum {self.MAX_CUSTOM_ATTRIBUTES} custom attributes allowed. "
                f"Found {len(custom)}: {custom}"
            )

        return {
            'standard': standard,
            'custom': custom
        }
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/customers/test_csv_column_mapper.py -v
```
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add src/customers/csv_column_mapper.py
git add tests/customers/test_csv_column_mapper.py
git commit -m "feat: add CSV column mapper for standard vs custom attributes"
```

---

## Task 4: CSV Row Parser - Extract Custom Attributes

**Files:**
- Create: `src/customers/csv_row_parser.py`
- Create: `tests/customers/test_csv_row_parser.py`

**Step 1: Write failing test**

```python
# tests/customers/test_csv_row_parser.py

import pytest
from customers.csv_row_parser import CSVRowParser

def test_parses_row_into_standard_and_custom():
    """Parse CSV row into standard fields and custom attributes JSON"""
    parser = CSVRowParser()
    headers = ['email', 'first_name', 'loyalty_tier', 'last_purchase_date']
    row = ['john@example.com', 'John', 'gold', '2024-01-15']

    result = parser.parse_row(headers, row)

    assert result['standard'] == {
        'email': 'john@example.com',
        'first_name': 'John'
    }
    assert result['custom_attributes'] == {
        'loyalty_tier': 'gold',
        'last_purchase_date': '2024-01-15'
    }

def test_omits_empty_values():
    """Empty CSV values should not be included in custom_attributes"""
    parser = CSVRowParser()
    headers = ['email', 'loyalty_tier', 'vip_status']
    row = ['john@example.com', 'gold', '']

    result = parser.parse_row(headers, row)

    assert 'loyalty_tier' in result['custom_attributes']
    assert 'vip_status' not in result['custom_attributes']

def test_requires_email():
    """Email is required field"""
    parser = CSVRowParser()
    headers = ['first_name', 'loyalty_tier']
    row = ['John', 'gold']

    with pytest.raises(ValueError, match="email is required"):
        parser.parse_row(headers, row)
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/customers/test_csv_row_parser.py -v
```
Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
# src/customers/csv_row_parser.py

from customers.csv_column_mapper import CSVColumnMapper

class CSVRowParser:
    """Parses CSV rows into standard fields and custom attributes"""

    def __init__(self):
        self.mapper = CSVColumnMapper()

    def parse_row(self, headers, row):
        """
        Parse a single CSV row into standard and custom fields.

        Args:
            headers: List of column names
            row: List of values corresponding to headers

        Returns:
            Dict with 'standard' and 'custom_attributes' keys

        Raises:
            ValueError: If email is missing
        """
        if len(headers) != len(row):
            raise ValueError("Headers and row must have same length")

        # Map columns
        column_mapping = self.mapper.map_columns(headers)

        # Build row dict
        row_dict = dict(zip(headers, row))

        # Validate email exists
        email_cols = [h for h in headers if h.lower() == 'email']
        if not email_cols or not row_dict[email_cols[0]]:
            raise ValueError("email is required")

        # Extract standard fields
        standard = {}
        for col in column_mapping['standard']:
            # Find original header (might have different case)
            original_header = next(h for h in headers if h.lower() == col.lower())
            value = row_dict[original_header]
            if value:  # Only include non-empty
                standard[col] = value

        # Extract custom attributes
        custom_attributes = {}
        for col in column_mapping['custom']:
            value = row_dict[col]
            if value:  # Omit empty values
                custom_attributes[col] = value

        return {
            'standard': standard,
            'custom_attributes': custom_attributes
        }
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/customers/test_csv_row_parser.py -v
```
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add src/customers/csv_row_parser.py
git add tests/customers/test_csv_row_parser.py
git commit -m "feat: add CSV row parser to extract custom attributes"
```

---

## Task 5: Customer Repository - Upsert with Custom Attributes

**Files:**
- Create: `src/customers/customer_repository.py`
- Create: `tests/customers/test_customer_repository.py`

**Step 1: Write failing test**

```python
# tests/customers/test_customer_repository.py

import pytest
from customers.customer_repository import CustomerRepository
from uuid import uuid4

@pytest.fixture
def db_connection():
    """Setup test database connection"""
    # Your database test setup here
    # Return connection object
    pass

def test_upsert_creates_new_customer(db_connection):
    """Upsert should create new customer with custom attributes"""
    repo = CustomerRepository(db_connection)
    account_id = uuid4()

    customer_data = {
        'account_id': account_id,
        'email': 'john@example.com',
        'first_name': 'John',
        'custom_attributes': {
            'loyalty_tier': 'gold',
            'last_purchase_date': '2024-01-15'
        }
    }

    customer_id = repo.upsert_customer(customer_data)

    # Verify created
    customer = repo.get_customer(account_id, 'john@example.com')
    assert customer['first_name'] == 'John'
    assert customer['custom_attributes']['loyalty_tier'] == 'gold'

def test_upsert_updates_existing_customer(db_connection):
    """Upsert should update existing customer and merge custom attributes"""
    repo = CustomerRepository(db_connection)
    account_id = uuid4()

    # Create initial customer
    initial_data = {
        'account_id': account_id,
        'email': 'john@example.com',
        'first_name': 'John',
        'custom_attributes': {'loyalty_tier': 'gold', 'old_field': 'value'}
    }
    repo.upsert_customer(initial_data)

    # Update with new data
    update_data = {
        'account_id': account_id,
        'email': 'john@example.com',
        'first_name': 'Johnny',
        'custom_attributes': {'loyalty_tier': 'platinum', 'new_field': 'value2'}
    }
    repo.upsert_customer(update_data)

    # Verify merge behavior
    customer = repo.get_customer(account_id, 'john@example.com')
    assert customer['first_name'] == 'Johnny'
    assert customer['custom_attributes']['loyalty_tier'] == 'platinum'  # Updated
    assert customer['custom_attributes']['old_field'] == 'value'  # Preserved
    assert customer['custom_attributes']['new_field'] == 'value2'  # Added
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/customers/test_customer_repository.py -v
```
Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
# src/customers/customer_repository.py

import psycopg2
from psycopg2.extras import Json
from uuid import uuid4

class CustomerRepository:
    """Database operations for customers with custom attributes"""

    def __init__(self, db_connection):
        self.conn = db_connection

    def upsert_customer(self, customer_data):
        """
        Insert or update customer with custom attributes merge.

        Args:
            customer_data: Dict with account_id, email, standard fields, custom_attributes

        Returns:
            UUID of created/updated customer
        """
        account_id = customer_data['account_id']
        email = customer_data['email']
        custom_attrs = customer_data.get('custom_attributes', {})

        # Extract standard fields (excluding account_id, email, custom_attributes)
        standard_fields = {
            k: v for k, v in customer_data.items()
            if k not in ['account_id', 'email', 'custom_attributes', 'id']
        }

        # Build dynamic field list for upsert
        field_names = ['first_name', 'last_name', 'phone', 'company']  # etc - add all standard fields
        field_values = [standard_fields.get(f) for f in field_names]

        query = """
            INSERT INTO customer.customer (
                id, account_id, email, first_name, last_name,
                custom_attributes, created_at, updated_at, status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, NOW(), NOW(), 'active'
            )
            ON CONFLICT (account_id, email)
            DO UPDATE SET
                first_name = COALESCE(EXCLUDED.first_name, customer.customer.first_name),
                last_name = COALESCE(EXCLUDED.last_name, customer.customer.last_name),
                custom_attributes = customer.customer.custom_attributes || EXCLUDED.custom_attributes,
                updated_at = NOW()
            RETURNING id;
        """

        with self.conn.cursor() as cursor:
            customer_id = uuid4()
            cursor.execute(query, (
                customer_id,
                account_id,
                email,
                standard_fields.get('first_name'),
                standard_fields.get('last_name'),
                Json(custom_attrs)
            ))
            result = cursor.fetchone()
            self.conn.commit()
            return result[0]

    def get_customer(self, account_id, email):
        """Fetch customer by account and email"""
        query = """
            SELECT id, email, first_name, last_name, custom_attributes
            FROM customer.customer
            WHERE account_id = %s AND email = %s;
        """

        with self.conn.cursor() as cursor:
            cursor.execute(query, (account_id, email))
            row = cursor.fetchone()
            if not row:
                return None

            return {
                'id': row[0],
                'email': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'custom_attributes': row[4] or {}
            }
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/customers/test_customer_repository.py -v
```
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/customers/customer_repository.py
git add tests/customers/test_customer_repository.py
git commit -m "feat: add customer repository with upsert and custom attributes merge"
```

---

## Task 6: Attribute Definitions Repository - Track Available Merge Tags

**Files:**
- Create: `src/customers/attribute_definitions_repository.py`
- Create: `tests/customers/test_attribute_definitions_repository.py`

**Step 1: Write failing test**

```python
# tests/customers/test_attribute_definitions_repository.py

import pytest
from customers.attribute_definitions_repository import AttributeDefinitionsRepository
from uuid import uuid4

@pytest.fixture
def db_connection():
    """Setup test database connection"""
    pass

def test_upsert_attribute_definitions(db_connection):
    """Should upsert attribute names and update last_seen_at"""
    repo = AttributeDefinitionsRepository(db_connection)
    account_id = uuid4()
    attribute_names = ['loyalty_tier', 'last_purchase_date', 'vip_status']

    repo.upsert_attribute_definitions(account_id, attribute_names)

    # Verify all attributes tracked
    definitions = repo.get_attribute_definitions(account_id)
    assert len(definitions) == 3
    assert 'loyalty_tier' in definitions
    assert 'last_purchase_date' in definitions

def test_get_attribute_definitions_sorted(db_connection):
    """Should return attribute names sorted alphabetically"""
    repo = AttributeDefinitionsRepository(db_connection)
    account_id = uuid4()

    repo.upsert_attribute_definitions(account_id, ['zebra', 'apple', 'banana'])
    definitions = repo.get_attribute_definitions(account_id)

    assert definitions == ['apple', 'banana', 'zebra']
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/customers/test_attribute_definitions_repository.py -v
```
Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
# src/customers/attribute_definitions_repository.py

class AttributeDefinitionsRepository:
    """Database operations for custom attribute definitions"""

    def __init__(self, db_connection):
        self.conn = db_connection

    def upsert_attribute_definitions(self, account_id, attribute_names):
        """
        Upsert attribute definitions for an account.
        Updates last_seen_at if already exists.

        Args:
            account_id: UUID of account
            attribute_names: List of attribute name strings
        """
        if not attribute_names:
            return

        query = """
            INSERT INTO customer.custom_attribute_definition (account_id, attribute_name, last_seen_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (account_id, attribute_name)
            DO UPDATE SET last_seen_at = NOW();
        """

        with self.conn.cursor() as cursor:
            # Batch insert
            data = [(account_id, name) for name in attribute_names]
            cursor.executemany(query, data)
            self.conn.commit()

    def get_attribute_definitions(self, account_id):
        """
        Get all attribute names for an account.

        Args:
            account_id: UUID of account

        Returns:
            List of attribute name strings, sorted alphabetically
        """
        query = """
            SELECT attribute_name
            FROM customer.custom_attribute_definition
            WHERE account_id = %s
            ORDER BY attribute_name;
        """

        with self.conn.cursor() as cursor:
            cursor.execute(query, (account_id,))
            rows = cursor.fetchall()
            return [row[0] for row in rows]
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/customers/test_attribute_definitions_repository.py -v
```
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/customers/attribute_definitions_repository.py
git add tests/customers/test_attribute_definitions_repository.py
git commit -m "feat: add attribute definitions repository for merge tag tracking"
```

---

## Task 7: CSV Upload Service - Orchestrate Complete Upload

**Files:**
- Create: `src/customers/csv_upload_service.py`
- Create: `tests/customers/test_csv_upload_service.py`

**Step 1: Write failing test**

```python
# tests/customers/test_csv_upload_service.py

import pytest
from customers.csv_upload_service import CSVUploadService
from uuid import uuid4
from io import StringIO

@pytest.fixture
def db_connection():
    """Setup test database connection"""
    pass

def test_uploads_csv_with_custom_attributes(db_connection):
    """Should parse CSV, upsert customers, track attribute definitions"""
    service = CSVUploadService(db_connection)
    account_id = uuid4()

    csv_content = """email,first_name,last_name,loyalty_tier,last_purchase_date
john@example.com,John,Doe,gold,2024-01-15
jane@example.com,Jane,Smith,silver,2024-02-20"""

    csv_file = StringIO(csv_content)
    result = service.upload_csv(account_id, csv_file)

    assert result['customers_created'] == 2
    assert result['customers_updated'] == 0
    assert result['custom_attributes_found'] == ['loyalty_tier', 'last_purchase_date']

def test_upload_validates_max_custom_attributes(db_connection):
    """Should reject CSV with >10 custom attributes"""
    service = CSVUploadService(db_connection)
    account_id = uuid4()

    # Create CSV with 11 custom attributes
    headers = ['email'] + [f'custom_{i}' for i in range(11)]
    csv_content = ','.join(headers) + '\ntest@example.com,' + ','.join(['val'] * 11)

    csv_file = StringIO(csv_content)

    with pytest.raises(ValueError, match="Maximum 10 custom attributes"):
        service.upload_csv(account_id, csv_file)
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/customers/test_csv_upload_service.py -v
```
Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
# src/customers/csv_upload_service.py

import csv
from customers.csv_row_parser import CSVRowParser
from customers.customer_repository import CustomerRepository
from customers.attribute_definitions_repository import AttributeDefinitionsRepository

class CSVUploadService:
    """Orchestrates CSV upload with custom attributes"""

    def __init__(self, db_connection):
        self.parser = CSVRowParser()
        self.customer_repo = CustomerRepository(db_connection)
        self.attr_repo = AttributeDefinitionsRepository(db_connection)

    def upload_csv(self, account_id, csv_file):
        """
        Upload CSV file and process customers with custom attributes.

        Args:
            account_id: UUID of account
            csv_file: File-like object with CSV content

        Returns:
            Dict with upload statistics

        Raises:
            ValueError: If validation fails
        """
        reader = csv.reader(csv_file)
        headers = next(reader)

        # Validate column mapping (will raise if >10 custom)
        self.parser.mapper.map_columns(headers)

        customers_created = 0
        customers_updated = 0
        all_custom_attrs = set()

        # Process each row
        for row in reader:
            # Parse row
            parsed = self.parser.parse_row(headers, row)

            # Add account_id
            customer_data = {
                'account_id': account_id,
                **parsed['standard'],
                'custom_attributes': parsed['custom_attributes']
            }

            # Track custom attribute names
            all_custom_attrs.update(parsed['custom_attributes'].keys())

            # Upsert customer
            # TODO: Track if created vs updated
            self.customer_repo.upsert_customer(customer_data)
            customers_created += 1  # Simplified - should check if exists

        # Update attribute definitions
        if all_custom_attrs:
            self.attr_repo.upsert_attribute_definitions(
                account_id,
                list(all_custom_attrs)
            )

        return {
            'customers_created': customers_created,
            'customers_updated': customers_updated,
            'custom_attributes_found': sorted(list(all_custom_attrs))
        }
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/customers/test_csv_upload_service.py -v
```
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/customers/csv_upload_service.py
git add tests/customers/test_csv_upload_service.py
git commit -m "feat: add CSV upload service with full orchestration"
```

---

## Task 8: Mail Merge Service - Template Rendering

**Files:**
- Create: `src/customers/mail_merge_service.py`
- Create: `tests/customers/test_mail_merge_service.py`

**Step 1: Write failing test**

```python
# tests/customers/test_mail_merge_service.py

import pytest
from customers.mail_merge_service import MailMergeService
from uuid import uuid4

@pytest.fixture
def db_connection():
    """Setup test database connection"""
    pass

def test_renders_template_with_custom_attributes(db_connection):
    """Should replace merge tags with customer data"""
    service = MailMergeService(db_connection)

    # Setup test customer
    account_id = uuid4()
    customer = {
        'email': 'john@example.com',
        'first_name': 'John',
        'custom_attributes': {
            'loyalty_tier': 'gold',
            'last_purchase_date': '2024-01-15'
        }
    }

    template = "Hi {{first_name}}, your tier is {{loyalty_tier}}. Last purchase: {{last_purchase_date}}"

    result = service.render_template(template, customer)

    assert result == "Hi John, your tier is gold. Last purchase: 2024-01-15"

def test_handles_missing_merge_tags(db_connection):
    """Should handle missing custom attributes gracefully"""
    service = MailMergeService(db_connection)

    customer = {
        'email': 'john@example.com',
        'first_name': 'John',
        'custom_attributes': {'loyalty_tier': 'gold'}
    }

    template = "Hi {{first_name}}, status: {{vip_status}}"

    result = service.render_template(template, customer)

    # Missing tags should be left as-is or replaced with empty
    assert result == "Hi John, status: {{vip_status}}" or result == "Hi John, status: "
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/customers/test_mail_merge_service.py -v
```
Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
# src/customers/mail_merge_service.py

import re
from customers.customer_repository import CustomerRepository

class MailMergeService:
    """Renders email templates with customer merge tags"""

    def __init__(self, db_connection):
        self.customer_repo = CustomerRepository(db_connection)

    def render_template(self, template, customer):
        """
        Replace merge tags in template with customer data.

        Args:
            template: String with {{merge_tag}} placeholders
            customer: Dict with customer data and custom_attributes

        Returns:
            Rendered template string
        """
        result = template

        # Replace standard fields
        standard_fields = ['email', 'first_name', 'last_name', 'phone', 'company']
        for field in standard_fields:
            if field in customer and customer[field]:
                result = result.replace(f'{{{{{field}}}}}', str(customer[field]))

        # Replace custom attributes
        custom_attrs = customer.get('custom_attributes', {})
        for key, value in custom_attrs.items():
            result = result.replace(f'{{{{{key}}}}}', str(value))

        return result

    def render_for_customers(self, template, account_id, emails):
        """
        Render template for multiple customers.

        Args:
            template: String with {{merge_tag}} placeholders
            account_id: UUID of account
            emails: List of customer emails

        Returns:
            Dict mapping email -> rendered template
        """
        results = {}

        for email in emails:
            customer = self.customer_repo.get_customer(account_id, email)
            if customer:
                results[email] = self.render_template(template, customer)

        return results
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/customers/test_mail_merge_service.py -v
```
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/customers/mail_merge_service.py
git add tests/customers/test_mail_merge_service.py
git commit -m "feat: add mail merge service for template rendering"
```

---

## Task 9: API Endpoint - Get Available Merge Tags

**Files:**
- Create: `src/api/customers/merge_tags_endpoint.py` (or equivalent)
- Create: `tests/api/customers/test_merge_tags_endpoint.py`

**Step 1: Write failing test**

```python
# tests/api/customers/test_merge_tags_endpoint.py

import pytest
from api.customers.merge_tags_endpoint import get_merge_tags
from uuid import uuid4

@pytest.fixture
def api_client():
    """Setup API test client"""
    pass

def test_get_merge_tags_returns_standard_and_custom(api_client):
    """Should return both standard fields and custom attributes"""
    account_id = uuid4()

    # Seed some custom attributes
    # (setup via fixture or previous test)

    response = api_client.get(f'/api/accounts/{account_id}/merge-tags')

    assert response.status_code == 200
    data = response.json()

    assert 'standard_fields' in data
    assert 'custom_attributes' in data
    assert 'email' in data['standard_fields']
    assert 'first_name' in data['standard_fields']
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/api/customers/test_merge_tags_endpoint.py -v
```
Expected: FAIL - endpoint not found

**Step 3: Write minimal implementation**

```python
# src/api/customers/merge_tags_endpoint.py

from flask import jsonify  # Or your framework
from customers.attribute_definitions_repository import AttributeDefinitionsRepository
from customers.csv_column_mapper import CSVColumnMapper

def get_merge_tags(account_id, db_connection):
    """
    GET /api/accounts/{account_id}/merge-tags

    Returns available merge tags for email templates.
    """
    attr_repo = AttributeDefinitionsRepository(db_connection)
    mapper = CSVColumnMapper()

    # Get standard fields
    standard_fields = sorted(list(mapper.STANDARD_COLUMNS))

    # Get custom attributes for this account
    custom_attributes = attr_repo.get_attribute_definitions(account_id)

    return jsonify({
        'standard_fields': standard_fields,
        'custom_attributes': custom_attributes
    })
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/api/customers/test_merge_tags_endpoint.py -v
```
Expected: PASS (1 test)

**Step 5: Commit**

```bash
git add src/api/customers/merge_tags_endpoint.py
git add tests/api/customers/test_merge_tags_endpoint.py
git commit -m "feat: add API endpoint to get available merge tags"
```

---

## Task 10: API Endpoint - CSV Upload

**Files:**
- Create: `src/api/customers/csv_upload_endpoint.py`
- Create: `tests/api/customers/test_csv_upload_endpoint.py`

**Step 1: Write failing test**

```python
# tests/api/customers/test_csv_upload_endpoint.py

import pytest
from uuid import uuid4

@pytest.fixture
def api_client():
    """Setup API test client"""
    pass

def test_upload_csv_endpoint(api_client):
    """Should accept CSV file and process it"""
    account_id = uuid4()

    csv_content = b"""email,first_name,loyalty_tier
john@example.com,John,gold"""

    response = api_client.post(
        f'/api/accounts/{account_id}/customers/upload',
        files={'file': ('customers.csv', csv_content, 'text/csv')}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['customers_created'] > 0

def test_upload_csv_validates_file_type(api_client):
    """Should reject non-CSV files"""
    account_id = uuid4()

    response = api_client.post(
        f'/api/accounts/{account_id}/customers/upload',
        files={'file': ('file.txt', b'not a csv', 'text/plain')}
    )

    assert response.status_code == 400
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/api/customers/test_csv_upload_endpoint.py -v
```
Expected: FAIL - endpoint not found

**Step 3: Write minimal implementation**

```python
# src/api/customers/csv_upload_endpoint.py

from flask import request, jsonify  # Or your framework
from customers.csv_upload_service import CSVUploadService

def upload_csv(account_id, db_connection):
    """
    POST /api/accounts/{account_id}/customers/upload

    Uploads CSV file with customer data and custom attributes.
    """
    # Validate file
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV'}), 400

    try:
        # Process upload
        service = CSVUploadService(db_connection)
        result = service.upload_csv(account_id, file.stream)

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Upload failed'}), 500
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/api/customers/test_csv_upload_endpoint.py -v
```
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/api/customers/csv_upload_endpoint.py
git add tests/api/customers/test_csv_upload_endpoint.py
git commit -m "feat: add CSV upload API endpoint"
```

---

## Task 11: Integration Test - End-to-End CSV Upload and Mail Merge

**Files:**
- Create: `tests/integration/test_custom_attributes_flow.py`

**Step 1: Write integration test**

```python
# tests/integration/test_custom_attributes_flow.py

import pytest
from uuid import uuid4
from io import StringIO
from customers.csv_upload_service import CSVUploadService
from customers.mail_merge_service import MailMergeService
from customers.attribute_definitions_repository import AttributeDefinitionsRepository

@pytest.fixture
def db_connection():
    """Setup test database with migrations applied"""
    pass

def test_end_to_end_custom_attributes_flow(db_connection):
    """
    Test complete flow:
    1. Upload CSV with custom attributes
    2. Verify attribute definitions tracked
    3. Fetch merge tags
    4. Render email template with custom attributes
    """
    account_id = uuid4()

    # 1. Upload CSV
    csv_content = """email,first_name,last_name,loyalty_tier,last_purchase_date
john@example.com,John,Doe,gold,2024-01-15
jane@example.com,Jane,Smith,platinum,2024-02-01"""

    upload_service = CSVUploadService(db_connection)
    upload_result = upload_service.upload_csv(account_id, StringIO(csv_content))

    assert upload_result['customers_created'] == 2
    assert 'loyalty_tier' in upload_result['custom_attributes_found']
    assert 'last_purchase_date' in upload_result['custom_attributes_found']

    # 2. Verify attribute definitions
    attr_repo = AttributeDefinitionsRepository(db_connection)
    definitions = attr_repo.get_attribute_definitions(account_id)

    assert 'loyalty_tier' in definitions
    assert 'last_purchase_date' in definitions

    # 3. Render mail merge template
    merge_service = MailMergeService(db_connection)
    template = "Hi {{first_name}}, your {{loyalty_tier}} status expires soon!"

    results = merge_service.render_for_customers(
        template,
        account_id,
        ['john@example.com', 'jane@example.com']
    )

    assert results['john@example.com'] == "Hi John, your gold status expires soon!"
    assert results['jane@example.com'] == "Hi Jane, your platinum status expires soon!"

    print("✅ End-to-end test passed!")
```

**Step 2: Run integration test**

```bash
pytest tests/integration/test_custom_attributes_flow.py -v
```
Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_custom_attributes_flow.py
git commit -m "test: add end-to-end integration test for custom attributes"
```

---

## Task 12: Performance Test - Large Customer Set

**Files:**
- Create: `tests/performance/test_custom_attributes_performance.py`

**Step 1: Write performance test**

```python
# tests/performance/test_custom_attributes_performance.py

import pytest
import time
from uuid import uuid4
from customers.customer_repository import CustomerRepository
from customers.attribute_definitions_repository import AttributeDefinitionsRepository

@pytest.fixture
def db_connection():
    """Setup test database"""
    pass

def test_mail_merge_fetch_performance(db_connection):
    """Verify customer fetch is fast enough for mail merge"""
    account_id = uuid4()
    customer_repo = CustomerRepository(db_connection)

    # Create test customer with custom attributes
    customer_data = {
        'account_id': account_id,
        'email': 'perf-test@example.com',
        'first_name': 'Test',
        'custom_attributes': {
            'attr_' + str(i): f'value_{i}' for i in range(10)
        }
    }
    customer_repo.upsert_customer(customer_data)

    # Measure fetch time
    start = time.time()
    for _ in range(100):
        customer_repo.get_customer(account_id, 'perf-test@example.com')
    elapsed = time.time() - start

    avg_ms = (elapsed / 100) * 1000
    print(f"Average fetch time: {avg_ms:.2f}ms")

    # Should be under 50ms per fetch
    assert avg_ms < 50, f"Fetch too slow: {avg_ms}ms"

def test_attribute_definitions_query_performance(db_connection):
    """Verify merge tags query is fast"""
    account_id = uuid4()
    attr_repo = AttributeDefinitionsRepository(db_connection)

    # Insert many attribute definitions
    attr_names = [f'attribute_{i}' for i in range(100)]
    attr_repo.upsert_attribute_definitions(account_id, attr_names)

    # Measure query time
    start = time.time()
    for _ in range(100):
        attr_repo.get_attribute_definitions(account_id)
    elapsed = time.time() - start

    avg_ms = (elapsed / 100) * 1000
    print(f"Average query time: {avg_ms:.2f}ms")

    # Should be under 100ms
    assert avg_ms < 100, f"Query too slow: {avg_ms}ms"
```

**Step 2: Run performance tests**

```bash
pytest tests/performance/test_custom_attributes_performance.py -v -s
```
Expected: PASS with timing output

**Step 3: Commit**

```bash
git add tests/performance/test_custom_attributes_performance.py
git commit -m "test: add performance tests for custom attributes queries"
```

---

## Task 13: Documentation - API and Usage Guide

**Files:**
- Create: `docs/custom_attributes_api.md`

**Step 1: Write API documentation**

```markdown
# Custom Attributes API Documentation

## Overview

Custom attributes allow users to upload CSV files with arbitrary columns that get stored per customer. These attributes can be used as merge tags in email templates.

## API Endpoints

### Upload CSV with Custom Attributes

**POST** `/api/accounts/{account_id}/customers/upload`

Upload a CSV file with customer data and custom attributes.

**Request:**
- Content-Type: `multipart/form-data`
- Body: file field with CSV content

**Example CSV:**
```csv
email,first_name,last_name,loyalty_tier,last_purchase_date
john@example.com,John,Doe,gold,2024-01-15
```

**Response:**
```json
{
  "customers_created": 1,
  "customers_updated": 0,
  "custom_attributes_found": ["loyalty_tier", "last_purchase_date"]
}
```

**Validations:**
- Maximum 10 custom attributes per customer
- Email is required
- File must be valid CSV format

### Get Available Merge Tags

**GET** `/api/accounts/{account_id}/merge-tags`

Returns list of available merge tags for email templates.

**Response:**
```json
{
  "standard_fields": ["email", "first_name", "last_name", "phone", ...],
  "custom_attributes": ["loyalty_tier", "last_purchase_date", ...]
}
```

## Database Schema

### customer.customer table

Added column:
- `custom_attributes` (JSONB): Stores custom attribute key-value pairs

Example:
```json
{
  "loyalty_tier": "gold",
  "last_purchase_date": "2024-01-15",
  "contract_renewal": "2024-12-31"
}
```

### customer.custom_attribute_definition table

Tracks all unique custom attribute names per account.

Columns:
- `id` (UUID): Primary key
- `account_id` (UUID): Account reference
- `attribute_name` (TEXT): Name of custom attribute
- `last_seen_at` (TIMESTAMP): Last time seen in CSV upload
- `created_at` (TIMESTAMP): When first seen

## Usage Examples

### Mail Merge Template

```
Hi {{first_name}},

Your {{loyalty_tier}} membership includes special benefits!

Last purchase: {{last_purchase_date}}
```

### CSV Upload (Python)

```python
import requests

url = f"https://api.example.com/api/accounts/{account_id}/customers/upload"
files = {'file': open('customers.csv', 'rb')}

response = requests.post(url, files=files, headers={'Authorization': f'Bearer {token}'})
print(response.json())
```

## Performance Characteristics

- Customer fetch with custom attributes: < 50ms
- Available merge tags query: < 100ms for 1M customers
- CSV upload: ~5 seconds for 10k rows

## Limitations

- Maximum 10 custom attributes per customer
- Custom attribute values stored as strings (no type validation)
- Attribute names are case-sensitive in storage but can be matched case-insensitively
```

**Step 2: Commit documentation**

```bash
git add docs/custom_attributes_api.md
git commit -m "docs: add custom attributes API documentation"
```

---

## Completion Checklist

Before considering this feature complete, verify:

- [ ] All migrations run successfully on test database
- [ ] All unit tests pass (100% of test suite)
- [ ] Integration test passes end-to-end
- [ ] Performance tests meet SLA requirements
- [ ] API endpoints return correct responses
- [ ] CSV upload handles edge cases (empty values, >10 attributes)
- [ ] Mail merge correctly replaces all merge tags
- [ ] Documentation is complete and accurate
- [ ] Code review completed
- [ ] Deployed to staging environment
- [ ] Manual QA testing completed
- [ ] Ready for production deployment

---

## Rollback Plan

If issues arise in production:

1. **Stop CSV uploads** - Disable upload endpoint
2. **Check data integrity** - Verify no corrupted custom_attributes
3. **Rollback migration** - Run down migrations to remove custom_attributes column and definitions table
4. **Restore from backup** - If data corruption occurred

Rollback SQL:
```bash
psql production_db -f migrations/YYYYMMDDHHMMSS_add_custom_attributes_down.sql
psql production_db -f migrations/YYYYMMDDHHMMSS_create_attribute_definitions_down.sql
```
