# Shopify Sync Pipeline - Modularized Architecture

## Overview

The Shopify sync pipeline has been refactored into multiple specialized modules for better maintainability, testability, and scalability. The complete system connects Shopify → SQLite → Google Sheets → Power BI dashboards for real-time e-commerce analytics.

## Project Structure

```
Real-Time-E-Commerce-Analytics-Platform/
├── scripts/
│   ├── __init__.py                      # Python package marker
│   ├── main.py                          # Main orchestration module
│   ├── config.py                        # Configuration and environment setup
│   ├── database.py                      # Database initialization and schema management
│   ├── shopify_api.py                   # Shopify REST API wrapper and pagination
│   ├── sync.py                          # Data fetching and storage functions
│   ├── csv_export.py                    # CSV export functionality
│   ├── analytics.py                     # Analytics report generation
│   ├── google_sheets.py                 # Google Sheets integration
│   └── logger_config.py                 # Logging configuration
│
├── data/
│   ├── shopify_data.db                  # SQLite database (normalized)
│   ├── customers.csv                    # Exported customer dimension
│   ├── orders.csv                       # Exported order facts
│   ├── line_items.csv                   # Exported order details
│   ├── product_variants.csv             # Exported product variants
│   ├── products.csv                     # Exported product dimension
│   └── analytics_summary.json           # Analytics metrics (JSON)
│
├── logs/
│   └── shopify_sync_*.log               # Timestamped log files
│
├── dashboards/
│   ├── shopify_analytics.pbix           # Power BI workbook
│   ├── screenshots/
│   │   ├── overview_preview.jpg         # Overview dashboard page
│   │   ├── geographic_overview.jpg      # Geographic analysis page
│   │   ├── orders_customers.jpg         # Orders & Customers page
│   │   └── coherent_analysis.jpg        # Coherent Analysis page
│   └── README.md                        # Dashboard documentation
│
├── .env                                 # Environment variables
├── gspread_credentials.json             # Google Sheets authentication
└── ...
```

## Module Descriptions

### 1. **config.py**
**Purpose:** Centralized configuration management

**Responsibilities:**
- Load environment variables from .env located in parent directory
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
**Purpose:** Logging configuration with timestamped rotating file handler

**Responsibilities:**
- Setup logger with rotating file handler
- Create timestamped log files in project root `logs/` directory
- Configure both file and console output
- Ensure logs directory exists

**Key Exports:**
- `logger` - Configured logger instance (import throughout codebase)
- `TimestampRotatingFileHandler` - Custom handler class

**Log Location:** `Real-Time-E-Commerce-Analytics-Platform/logs/shopify_sync_*.log`

**Usage:**
```python
from logger_config import logger
logger.info("Process started")
logger.warning("Rate limit warning")
logger.error("Error occurred")
```

---

### 3. **database.py**
**Purpose:** Database initialization, schema management, and metadata operations

**Responsibilities:**
- Initialize SQLite database with normalized schema
- Handle schema migrations for backward compatibility
- Manage metadata key-value store for tracking sync state
- Check and add columns dynamically

**Database Tables:**

| Table | Purpose | Foreign Keys |
|-------|---------|--------------|
| metadata | Sync tracking (timestamps, state) | - |
| products | Product dimension | - |
| product_variants | Product variant details | product_id → products |
| customers | Customer dimension | - |
| orders | Order facts/transactions | customer_id → customers |
| line_items | Order line items | order_id → orders, product_id → products |

**Key Functions:**
- `init_db()` - Create/initialize all tables
- `migrate_schema(conn)` - Add missing columns
- `db_set_metadata(key, value)` - Store metadata
- `db_get_metadata(key)` - Retrieve metadata

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
- `request_with_retries(url, params, method, max_retries=5)` - HTTP request with backoff
- `fetch_all_rest(endpoint, params, item_key)` - Fetch all paginated results
- `parse_link_header(header)` - Parse RFC 5988 Link headers

**Features:**
- Exponential backoff for rate limiting
- Automatic pagination handling
- 30-second timeout per request
- Session reuse for connection pooling
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
- Fetch products with variants from Shopify
- Fetch customers from Shopify
- Fetch orders with line items from Shopify
- Store data in normalized schema
- Track last sync times for incremental updates
- Extract and preserve nested relationships

**Key Functions:**
- `fetch_and_store_products(incremental=True)` - Sync products and variants
- `fetch_and_store_customers(incremental=True)` - Sync customers
- `fetch_and_store_orders(incremental=True, status="any")` - Sync orders and line items
- `isoformat_for_api(dt)` - Convert datetime to Shopify API format

**Features:**
- Incremental sync support (only fetch updated items)
- Automatic timestamp tracking
- Nested data extraction (variants from products, line_items from orders)
- Foreign key relationship preservation
- 60-second buffer for incremental timestamps

**Usage:**
```python
from sync import fetch_and_store_products, fetch_and_store_customers, fetch_and_store_orders
fetch_and_store_products(incremental=True)
fetch_and_store_customers(incremental=True)
fetch_and_store_orders(incremental=True)
```

---

### 6. **csv_export.py**
**Purpose:** Export normalized CSV files for Power BI integration

**Responsibilities:**
- Export products to CSV
- Export product variants to CSV with FK
- Export customers to CSV
- Export orders to CSV with FK
- Export line items to CSV with FKs
- Handle missing values and encoding

**CSV Output Files:**

| File | Records | Foreign Keys | Power BI Use |
|------|---------|--------------|-------------|
| products.csv | Product SKUs | - | Product dimension |
| product_variants.csv | Variant details | product_id | Product hierarchy |
| customers.csv | Customer records | - | Customer dimension |
| orders.csv | Order transactions | customer_id | Order facts |
| line_items.csv | Order line details | order_id, product_id | Item granularity |

**Key Functions:**
- `export_products_to_csv()` - Products dimension
- `export_product_variants_to_csv()` - Variants with product_id FK
- `export_customers_to_csv()` - Customer dimension
- `export_orders_to_csv()` - Order facts with customer_id FK
- `export_line_items_to_csv()` - Line items with order_id and product_id FKs
- `export_all_to_csv()` - Export all data files

**Features:**
- Normalized schema with proper foreign keys for Power BI
- NaN values replaced with empty strings
- UTF-8 encoding with proper escaping
- Logging for each export operation

**Usage:**
```python
from csv_export import export_all_to_csv
export_all_to_csv()
```

---

### 7. **google_sheets.py**
**Purpose:** Google Sheets authentication and data synchronization

**Responsibilities:**
- Initialize gspread client with service account
- Create/manage worksheets
- Push DataFrames to Google Sheets
- Sync all CSV data to sheets

**Key Functions:**
- `init_google_sheets()` - Authenticate and return client
- `get_or_create_worksheet(gc, sheet_id, worksheet_name)` - Manage worksheets
- `push_dataframe_to_sheet(gc, sheet_id, dataframe, worksheet_name)` - Push data
- `sync_all_data_to_sheets(gc, sheet_id)` - Sync all CSV files

**Worksheets Created:**
- Products - Product dimension
- ProductVariants - Variants with relationships
- Customers - Customer dimension
- Orders - Order facts with customer references
- LineItems - Line items with order/product references

**Features:**
- Service account authentication (no user login needed)
- Automatic worksheet creation
- Clear and replace strategy (full refresh)
- Error handling and recovery

**Usage:**
```python
from google_sheets import init_google_sheets, sync_all_data_to_sheets
gc = init_google_sheets()
sync_all_data_to_sheets(gc, GOOGLE_SHEET_ID)
```

---

### 8. **analytics.py**
**Purpose:** Generate analytics reports and summaries from synced data

**Responsibilities:**
- Calculate business metrics (total orders, sales, AOV)
- Identify customer behavior (repeat rate, frequency)
- Generate product performance insights
- Create summary JSON reports

**Key Metrics:**
- Total orders
- Total sales (sum of order values)
- Average Order Value (AOV)
- Repeat customer rate (%)
- Sales by day breakdown
- Top 10 products by quantity

**Key Functions:**
- `analytics_reports()` - Generate all analytics

**Output:**
- Console/log: Detailed metrics
- `data/analytics_summary.json` - Summary data
- Database queries for custom analysis

**Usage:**
```python
from analytics import analytics_reports
analytics_reports()
```

---

### 9. **main.py**
**Purpose:** Orchestration and CLI entry point for entire pipeline

**Responsibilities:**
- Orchestrate all modules in proper sequence
- Parse command-line arguments
- Validate configuration
- Support daemon mode with APScheduler
- Coordinate full sync execution

**CLI Options:**

```bash
python main.py --once                    # Run once and exit (default)
python main.py --daemon                  # Run every 10 minutes
python main.py --full                    # Force full (non-incremental) sync
python main.py --no-sheets               # Disable Google Sheets sync
python main.py --daemon --full           # Daemon with full sync each time
```

**Pipeline Execution Steps:**
1. Validate configuration (SHOPIFY_STORE, SHOPIFY_API_TOKEN)
2. Initialize database
3. Fetch and store products
4. Fetch and store customers
5. Fetch and store orders
6. Export to CSV files
7. Generate analytics reports
8. Push to Google Sheets (optional)

**Key Functions:**
- `run_full_sync(incremental, push_to_sheets)` - Execute complete pipeline
- `validate_configuration()` - Verify environment setup
- `main()` - CLI argument parsing

**Usage:**
```bash
cd scripts/
python main.py --once
python main.py --daemon
```

---

## Data Flow Architecture

### Complete Pipeline Flow

```
Real-Time Shopify Data
        ↓
   shopify_api.py
   (API Client)
        ↓
   sync.py
   (Fetch & Store)
        ↓
SQLite Database (shopify_data.db)
   ├─ products
   ├─ product_variants
   ├─ customers
   ├─ orders
   ├─ line_items
   └─ metadata
        ↓
   ┌────┴──────────┬──────────┐
   │               │          │
   ▼               ▼          ▼
csv_export     analytics   logger_config
(CSV Files)    (JSON)      (Logs)
   │
   └──►google_sheets.py
       (Push to Sheets)
           ↓
    Google Sheets
    (Auto-Refresh)
           ↓
    Power BI Dashboard
    ├─ Overview
    ├─ Geographic
    ├─ Orders & Customers
    └─ Coherent Analysis
```

## Database Schema with Power BI Relationships

### Foreign Key Structure (Normalized)

```
products (1)
    ├───(1:N)─── product_variants (N)
    │
    └───(1:N)─── line_items (N)

customers (1)
    └───(1:N)─── orders (N)
        └───(1:N)─── line_items (N)
```

### CSV Files for Power BI

| CSV File | Dimension/Fact | Relationship | Power BI Role |
|----------|---|---|---|
| products.csv | Dimension | PK: id | Product lookup |
| product_variants.csv | Dimension | FK: product_id | Variant details |
| customers.csv | Dimension | PK: id | Customer lookup |
| orders.csv | Fact | FK: customer_id | Main transaction |
| line_items.csv | Fact | FK: order_id, product_id | Item granularity |

## Power BI Dashboard Integration

### Dashboard Location
```
dashboards/
├── shopify_analytics.pbix               # Main Power BI file
├── screenshots/
│   ├── overview_preview.jpg             # Dashboard preview
│   ├── geographic_overview.jpg
│   ├── orders_customers.jpg
│   └── coherent_analysis.jpg
└── README.md
```

### Dashboard Pages

**1. Overview Page**
- Total Orders: 120
- Total Customers: 38
- Average Order Value: $340.95
- Processing Time: 0.99 days
- Total Sales: $40.91K
- Total Discounts: $3.26K
- Sales & Order Value Chart (Jun 2024 - Nov 2024)
- Customer & Orders Chart

**2. Geographic Overview Page**
- Geographic distribution of orders
- Sales by location
- Customer distribution map
- Regional performance analysis

**3. Orders & Customers Page**
- Order timeline and trends
- Customer segmentation
- Order status breakdown
- Customer lifetime value
- Repeat purchase analysis

**4. Coherent Analysis Page**
- Integrated KPI scorecards
- Correlation analysis
- Trend comparisons
- Performance metrics

### Connection & Refresh Strategy

```
Pipeline (10 min interval)
    → SQLite Database
    → CSV Export
    → Google Sheets Sync
    → Power BI (Connected)
    → Dashboard Refresh
```

---

## Environment Configuration

**File:** `.env` (in project root)

**Required:**
```env
SHOPIFY_STORE=your-store-name
SHOPIFY_API_TOKEN=your-api-token
```

**Optional (for dashboards):**
```env
GOOGLE_SHEET_ID=your-sheet-id
```

**Credentials File:**
- `gspread_credentials.json` - Google Cloud service account (in project root)

---

## Installation & Setup

### 1. Setup Project
```bash
cd Real-Time-E-Commerce-Analytics-Platform
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Edit .env with your credentials
echo "SHOPIFY_STORE=your-store" > .env
echo "SHOPIFY_API_TOKEN=your-token" >> .env
```

### 3. Setup Google Sheets (Optional)
1. Create Google Cloud service account
2. Download JSON credentials
3. Save as `gspread_credentials.json` in project root
4. Share Google Sheet with service account email
5. Add `GOOGLE_SHEET_ID` to `.env`

### 4. Run Pipeline
```bash
cd scripts/
python main.py --once
```

### 5. Setup Power BI (Optional)
1. Open `dashboards/shopify_analytics.pbix` in Power BI Desktop
2. Configure Google Sheets data source
3. Setup refresh schedule in Power BI Service
4. Publish to Power BI Online

---

## Logging & Monitoring

### Log Files
**Location:** `Real-Time-E-Commerce-Analytics-Platform/logs/`

**Format:** `shopify_sync_YYYYMMDD_HHMMSS.log`

**Contents:**
- Sync start/end times
- Records fetched per entity
- CSV export status
- Analytics calculations
- Google Sheets push results
- Errors and warnings

### Monitoring Checklist
- Check `logs/` for execution details
- Verify CSV files in `data/` folder
- Monitor `data/analytics_summary.json` for metrics
- View Power BI dashboard for visual insights
- Track database size growth

---

## Module Dependencies

```
main.py
├── logger_config.py        (logging)
├── config.py               (configuration)
├── database.py             (DB init/management)
├── sync.py
│   ├── shopify_api.py      (API calls)
│   └── database.py
├── csv_export.py
│   └── database.py
├── analytics.py
│   └── database.py
└── google_sheets.py
    └── (pandas, gspread)
```

---

## Benefits of Modular Architecture

✅ **Separation of Concerns** - Each module has single responsibility  
✅ **Reusability** - Modules can be imported independently  
✅ **Testability** - Easier to unit test individual components  
✅ **Maintainability** - Clear structure and organization  
✅ **Scalability** - Easy to add features/data sources  
✅ **Debugging** - Isolated issues easier to track  
✅ **Monitoring** - Comprehensive logging throughout  
✅ **Integration** - Seamless Power BI connection  

---

## Quick Commands

```bash
# Navigate to scripts
cd scripts/

# Run once
python main.py --once

# Run as daemon (every 10 min)
python main.py --daemon

# Force full sync
python main.py --full --once

# Skip Google Sheets
python main.py --no-sheets --once

# Full sync as daemon
python main.py --daemon --full
```

---

**Version:** 2.1 (Integrated with Power BI Dashboards)  
**Last Updated:** 2025-11-18  
**Architecture Type:** Modular, Event-Driven, Cloud-Connected
