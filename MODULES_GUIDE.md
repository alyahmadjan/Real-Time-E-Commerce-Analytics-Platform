# Shopify Sync Pipeline - Modularized Architecture

## Overview

The Shopify sync pipeline has been refactored into multiple specialized modules for better maintainability, testability, and scalability. Each module handles a specific responsibility within the data pipeline.

## Project Structure

```
Real-Time-E-Commerce-Analytics-Platform/
├── scripts/
│   ├── __init__.py                  # Python package marker
│   ├── main.py                      # Main orchestration module
│   ├── config.py                    # Configuration and environment setup
│   ├── database.py                  # Database initialization and schema management
│   ├── shopify_api.py               # Shopify REST API wrapper and pagination
│   ├── sync.py                      # Data fetching and storage functions
│   ├── csv_export.py                # CSV export functionality
│   ├── analytics.py                 # Analytics report generation
│   ├── google_sheets.py             # Google Sheets integration
│   └── logger_config.py             # Logging configuration
├── data/
│   ├── shopify_data.db              # SQLite database
│   ├── customers.csv
│   ├── orders.csv
│   ├── line_items.csv
│   ├── product_variants.csv
│   ├── products.csv
│   └── analytics_summary.json
├── logs/
│   └── shopify_sync_*.log          # Timestamped log files
├── .env                             # Environment variables
├── gspread_credentials.json         # Google Sheets credentials
└── ...
```

## Module Descriptions

### 1. **config.py**
**Purpose:** Centralized configuration management

**Responsibilities:**
- Load environment variables from .env file
- Define file paths (data, logs, credentials)
- Setup API constants and headers
- Initialize directory structure

**Key Exports:**
- `SHOPIFY_STORE`, `SHOPIFY_API_TOKEN`
- `BASE_URL`, `API_VERSION`
- `DB_FILE`, `CSV_*` paths
- `GOOGLE_SHEET_ID`, `SCOPES`
- `REQUESTS_HEADERS`

**Usage:**
```python
from config import DB_FILE, BASE_URL, SHOPIFY_API_TOKEN
```

---

### 2. **logger_config.py**
**Purpose:** Logging configuration with timestamped file rotation

**Responsibilities:**
- Setup logger with rotating file handler
- Create timestamped log files
- Configure both file and console output
- Ensure logs directory exists

**Key Exports:**
- `logger` - Configured logger instance
- `TimestampRotatingFileHandler` - Custom handler class

**Usage:**
```python
from logger_config import logger
logger.info("Starting sync process")
```

---

### 3. **database.py**
**Purpose:** SQLite database initialization and schema management

**Responsibilities:**
- Initialize normalized schema for Power BI
- Handle schema migrations for backward compatibility
- Manage metadata (last sync timestamps)
- Check and add columns dynamically

**Key Functions:**
- `init_db()` - Create tables if they don't exist
- `migrate_schema(conn)` - Add missing columns
- `db_set_metadata(key, value)` - Store metadata
- `db_get_metadata(key)` - Retrieve metadata

**Schema:**
- **metadata** - Key-value store for sync tracking
- **products** - Product dimension table
- **product_variants** - Product variant details
- **customers** - Customer dimension table
- **orders** - Order facts with customer FK
- **line_items** - Line items with order/product FKs

**Usage:**
```python
from database import init_db, db_get_metadata, db_set_metadata
init_db()
last_sync = db_get_metadata("products_last_sync")
```

---

### 4. **shopify_api.py**
**Purpose:** Shopify REST API wrapper with rate limiting and pagination

**Responsibilities:**
- Handle REST API requests with retry logic
- Parse Link headers for pagination
- Manage rate limiting (429 responses)
- Create and manage persistent session

**Key Functions:**
- `request_with_retries(url, params, method, max_retries)` - HTTP request with backoff
- `fetch_all_rest(endpoint, params, item_key)` - Fetch all paginated results
- `parse_link_header(header)` - Parse RFC 5988 Link headers

**Features:**
- Exponential backoff for rate limiting
- Automatic pagination handling
- 30-second timeout per request
- UTF-8 encoding support

**Usage:**
```python
from shopify_api import fetch_all_rest
products = fetch_all_rest("products.json", item_key="products")
```

---

### 5. **sync.py**
**Purpose:** Fetch and store Shopify data into SQLite

**Responsibilities:**
- Fetch products with variants
- Fetch customers
- Fetch orders with line items
- Store data in normalized schema
- Track last sync times for incremental updates
- Extract and store nested relationships

**Key Functions:**
- `fetch_and_store_products(incremental)` - Sync products and variants
- `fetch_and_store_customers(incremental)` - Sync customers
- `fetch_and_store_orders(incremental, status)` - Sync orders and line items
- `isoformat_for_api(dt)` - Convert datetime to Shopify API format

**Features:**
- Incremental sync support (only fetch updated items)
- Automatic timestamp tracking
- Nested data extraction (variants from products, line_items from orders)
- Foreign key relationship preservation

**Usage:**
```python
from sync import fetch_and_store_products, fetch_and_store_customers, fetch_and_store_orders
fetch_and_store_products(incremental=True)
fetch_and_store_customers(incremental=True)
fetch_and_store_orders(incremental=True)
```

---

### 6. **csv_export.py**
**Purpose:** Export normalized CSV files for Power BI

**Responsibilities:**
- Export products to CSV
- Export product variants to CSV
- Export customers to CSV
- Export orders to CSV
- Export line items to CSV
- Handle missing values and formatting

**Key Functions:**
- `export_products_to_csv()` - Products dimension
- `export_product_variants_to_csv()` - Product variants with FK
- `export_customers_to_csv()` - Customer dimension
- `export_orders_to_csv()` - Order facts with customer FK
- `export_line_items_to_csv()` - Line items with order/product FKs
- `export_all_to_csv()` - Export all data files

**Features:**
- Normalized schema with proper foreign keys
- NaN value handling (replaced with empty strings)
- UTF-8 encoding
- Logging for each export operation

**Usage:**
```python
from csv_export import export_all_to_csv
export_all_to_csv()
```

---

### 7. **google_sheets.py**
**Purpose:** Google Sheets integration and data synchronization

**Responsibilities:**
- Initialize gspread client with service account
- Create/manage worksheets
- Push DataFrames to Google Sheets
- Sync all CSV data to sheets

**Key Functions:**
- `init_google_sheets()` - Initialize authorized client
- `get_or_create_worksheet(gc, sheet_id, worksheet_name)` - Manage worksheets
- `push_dataframe_to_sheet(gc, sheet_id, dataframe, worksheet_name)` - Push data
- `sync_all_data_to_sheets(gc, sheet_id)` - Sync all CSV files

**Features:**
- Service account authentication
- Automatic worksheet creation
- Clear and replace strategy
- Error handling and logging

**Usage:**
```python
from google_sheets import init_google_sheets, sync_all_data_to_sheets
gc = init_google_sheets()
sync_all_data_to_sheets(gc, GOOGLE_SHEET_ID)
```

---

### 8. **analytics.py**
**Purpose:** Generate analytics reports from synced data

**Responsibilities:**
- Calculate total orders and sales
- Compute average order value (AOV)
- Identify top products
- Calculate repeat customer rate
- Generate and save summary JSON

**Key Functions:**
- `analytics_reports()` - Generate all analytics

**Metrics Calculated:**
- Total orders
- Total sales (sum of order values)
- Average Order Value (AOV)
- Repeat customer rate (%)
- Sales by day
- Top 10 products by quantity

**Output:**
- `analytics_summary.json` - Summary metrics
- Console/log output - Detailed report

**Usage:**
```python
from analytics import analytics_reports
analytics_reports()
```

---

### 9. **main.py**
**Purpose:** Orchestration and CLI entry point

**Responsibilities:**
- Orchestrate the entire sync pipeline
- Parse command-line arguments
- Validate configuration
- Support daemon mode with APScheduler
- Coordinate all modules

**Key Functions:**
- `run_full_sync(incremental, push_to_sheets)` - Execute complete pipeline
- `validate_configuration()` - Check required environment variables
- `main()` - CLI entry point

**CLI Options:**
```bash
python main.py --once                    # Run once and exit (default)
python main.py --daemon                  # Run every 10 minutes
python main.py --full                    # Force full (non-incremental) sync
python main.py --no-sheets               # Disable Google Sheets sync
python main.py --daemon --full           # Daemon with full sync
```

**Pipeline Steps:**
1. Validate configuration
2. Initialize database
3. Fetch and store products
4. Fetch and store customers
5. Fetch and store orders
6. Export to CSV
7. Generate analytics
8. Push to Google Sheets (optional)

**Usage:**
```bash
# Run once
python main.py --once

# Run as daemon
python main.py --daemon

# Run with full sync
python main.py --full --daemon
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     main.py (Orchestrator)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ config.py    │ │ database.py  │ │ logger_config│
│ (Config)     │ │ (Schema)     │ │ (Logging)    │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    ┌────────────────────────┐
    │   sync.py (Fetch)      │  ◄─── shopify_api.py
    │ • Products            │       (API Client)
    │ • Customers           │
    │ • Orders + Line Items │
    └────────────┬───────────┘
                 │
        SQLite Database (shopify_data.db)
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐    ┌──────────────┐
│ csv_export.py│    │ analytics.py │
│ (CSV Export) │    │ (Reports)    │
└────────┬─────┘    └──────┬───────┘
         │                  │
    CSV Files          JSON Report
         │                  │
         └──────────┬───────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ google_sheets.py     │
         │ (Push to Sheets)     │
         └──────────────────────┘
```

## Database Schema

### Foreign Key Relationships

```
products (PK: id)
    │
    ├─── product_variants (FK: product_id → products.id)
    │
    └─── line_items (FK: product_id → products.id)

customers (PK: id)
    │
    └─── orders (FK: customer_id → customers.id)
         │
         └─── line_items (FK: order_id → orders.id)
```

## Environment Variables

**Required:**
```env
SHOPIFY_STORE=your-store-name
SHOPIFY_API_TOKEN=your-api-token
```

**Optional:**
```env
GOOGLE_SHEET_ID=your-sheet-id
```

## Logging

All operations are logged to:
- **File:** `logs/shopify_sync_YYYYMMDD_HHMMSS.log`
- **Console:** Real-time output of INFO level and above

Log entries include:
- Timestamp
- Log level (DEBUG, INFO, WARNING, ERROR, EXCEPTION)
- Descriptive message

## Installation & Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Setup environment:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Place files:**
All modules should be in `scripts/` folder:
```bash
scripts/
├── config.py
├── database.py
├── shopify_api.py
├── sync.py
├── csv_export.py
├── analytics.py
├── google_sheets.py
├── logger_config.py
└── main.py
```

4. **Run:**
```bash
cd scripts/
python main.py --once
```

## Benefits of Modularization

1. **Separation of Concerns** - Each module has single responsibility
2. **Testability** - Easier to unit test individual components
3. **Reusability** - Modules can be imported and used independently
4. **Maintainability** - Clear structure and organization
5. **Scalability** - Easy to add new features or data sources
6. **Debugging** - Isolated issues are easier to track
7. **Documentation** - Each module is self-documented

## Error Handling

- All modules include try-except blocks with proper logging
- Exceptions are logged with full traceback
- Pipeline continues even if one step fails (graceful degradation)
- Validation checks in config and database initialization

## Performance Considerations

- Incremental sync reduces API calls and processing time
- Batch processing with SQLite transactions
- Pagination handles large datasets efficiently
- Rate limiting prevents API throttling
- CSV export uses pandas for optimized I/O

---

**Last Updated:** 2025-11-18  
**Version:** 2.0 (Modularized)
