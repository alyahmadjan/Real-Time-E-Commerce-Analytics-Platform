# Shopify Sync Pipeline - Complete Architecture Guide

## Overview

This is a **complete real-time e-commerce analytics platform** that syncs Shopify data to SQLite, exports to CSV, pushes to Google Sheets, and connects to Power BI dashboards for comprehensive business intelligence and monitoring.

The entire pipeline is modularized into specialized components with centralized orchestration, automated scheduling, and comprehensive logging.

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
│   ├── shopify_data.db                  # SQLite database (normalized schema)
│   ├── customers.csv                    # Customer dimension (exported)
│   ├── orders.csv                       # Order facts (exported)
│   ├── line_items.csv                   # Order line items (exported)
│   ├── product_variants.csv             # Product variants (exported)
│   ├── products.csv                     # Product dimension (exported)
│   └── analytics_summary.json           # Key metrics summary (JSON)
│
├── logs/
│   └── shopify_sync_*.log               # Timestamped log files (project root)
│
├── dashboards/
│   ├── shopify_analytics.pbix           # Power BI dashboard file
│   ├── screenshots/
│   │   ├── overview_preview.jpg         # Overview page preview
│   │   ├── geographic_overview.jpg      # Geographic overview page
│   │   ├── orders_customers.jpg         # Orders & Customers page
│   │   └── coherent_analysis.jpg        # Coherent Analysis page
│   └── README.md                        # Dashboard documentation
│
├── .env                                 # Environment variables
├── gspread_credentials.json             # Google Sheets service account
└── ...
```

---

## System Architecture

### Data Flow Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│         Shopify Admin REST API (Products/Orders/Customers)  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │  scripts/shopify_api.py           │
        │  (API Client with Rate Limiting) │
        └──────────────┬───────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌───────────────────┐      ┌──────────────────┐
│   sync.py         │      │  config.py       │
│   (Fetch & Store) │◄─────│  (Configuration) │
└────────┬──────────┘      └──────────────────┘
         │
         ▼
┌───────────────────────────────────┐
│   SQLite Database                 │
│   (Normalized Schema with FKs)    │
│   • products                      │
│   • product_variants              │
│   • customers                     │
│   • orders                        │
│   • line_items                    │
│   • metadata                      │
└───────────┬───────────────────────┘
            │
        ┌───┴─────────────────────────┬──────────────┐
        │                             │              │
        ▼                             ▼              ▼
┌──────────────────┐    ┌──────────────────┐  ┌────────────────┐
│ csv_export.py    │    │ analytics.py     │  │ main.py        │
│ (CSV Export)     │    │ (Metrics & Stats)│  │ (Orchestration)│
└────────┬─────────┘    └────────┬─────────┘  └────────────────┘
         │                       │
    CSV Files               JSON Summary
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌──────────────────────────┐
         │   google_sheets.py       │
         │   (Push to Google Sheets)│
         └──────────┬───────────────┘
                    │
                    ▼
         ┌──────────────────────────────┐
         │  Google Sheets Workbook      │
         │  • Products (Auto-refresh)   │
         │  • Customers                 │
         │  • Orders                    │
         │  • Line Items                │
         │  • Variants                  │
         └──────────┬───────────────────┘
                    │
                    ▼
         ┌──────────────────────────────┐
         │   Power BI Dashboard         │
         │   (Connected to Google Sheet)│
         │   • Overview Page            │
         │   • Geographic Overview      │
         │   • Orders & Customers       │
         │   • Coherent Analysis        │
         └──────────────────────────────┘
```

---

## Module Descriptions

### 1. **config.py**
**Purpose:** Centralized configuration management

**Responsibilities:**
- Load environment variables from `.env` file in project root
- Define file paths (data, logs, credentials)
- Setup Shopify API constants and headers
- Initialize directory structure

**Key Exports:**
- `SHOPIFY_STORE`, `SHOPIFY_API_TOKEN` - Shopify authentication
- `BASE_URL`, `API_VERSION` - Shopify API endpoints
- `DB_FILE`, `CSV_*` paths - Data file locations
- `GOOGLE_SHEET_ID`, `SCOPES` - Google Sheets configuration
- `REQUESTS_HEADERS` - API request headers

**Usage:**
```python
from config import DB_FILE, BASE_URL, SHOPIFY_API_TOKEN, GOOGLE_SHEET_ID
```

---

### 2. **logger_config.py**
**Purpose:** Logging configuration with timestamped file rotation

**Responsibilities:**
- Setup logger with rotating file handler
- Create timestamped log files in project root `logs/` directory
- Configure both file and console output
- Ensure logs directory exists with proper permissions

**Key Exports:**
- `logger` - Configured logger instance (use throughout codebase)
- `TimestampRotatingFileHandler` - Custom handler class

**Features:**
- Logs stored in: `Real-Time-E-Commerce-Analytics-Platform/logs/shopify_sync_*.log`
- File and console output simultaneously
- UTF-8 encoding for international characters
- 1 MB file rotation threshold

**Usage:**
```python
from logger_config import logger
logger.info("Starting sync process")
logger.warning("Rate limit reached")
logger.error("Database connection failed")
```

---

### 3. **database.py**
**Purpose:** SQLite database initialization and schema management

**Responsibilities:**
- Initialize normalized schema designed for Power BI relationships
- Handle schema migrations for backward compatibility
- Manage metadata key-value store
- Check and add columns dynamically

**Database Schema:**

| Table | Purpose | Relationships |
|-------|---------|---------------|
| metadata | Key-value store for sync tracking | - |
| products | Product dimension | 1:N with product_variants, 1:N with line_items |
| product_variants | Product variant details | N:1 with products |
| customers | Customer dimension | 1:N with orders |
| orders | Order facts/transactions | N:1 with customers, 1:N with line_items |
| line_items | Order line items | N:1 with orders, N:1 with products |

**Foreign Key Relationships:**
```
products (PK: id)
    ├─── product_variants (FK: product_id)
    └─── line_items (FK: product_id)

customers (PK: id)
    └─── orders (FK: customer_id)
         └─── line_items (FK: order_id)
```

**Key Functions:**
- `init_db()` - Create/initialize all tables
- `migrate_schema(conn)` - Add missing columns for backward compatibility
- `db_set_metadata(key, value)` - Store metadata
- `db_get_metadata(key)` - Retrieve metadata (used for tracking last sync)

**Usage:**
```python
from database import init_db, db_get_metadata, db_set_metadata

# Initialize database
init_db()

# Track last sync time
last_sync = db_get_metadata("products_last_sync")
db_set_metadata("products_last_sync", "2025-11-18T15:30:00")
```

---

### 4. **shopify_api.py**
**Purpose:** Shopify REST API wrapper with rate limiting and pagination

**Responsibilities:**
- Handle REST API requests with automatic retry logic
- Parse RFC 5988 Link headers for pagination
- Manage Shopify API rate limiting (429 responses)
- Create and maintain persistent HTTP session

**Key Functions:**
- `request_with_retries(url, params, method, max_retries=5)` - HTTP request with exponential backoff
- `fetch_all_rest(endpoint, params, item_key)` - Fetch all paginated results
- `parse_link_header(header)` - Parse Link headers for next page

**Features:**
- Exponential backoff (1s, 2s, 4s, 8s, 16s)
- Automatic pagination handling
- 30-second timeout per request
- Session reuse for connection pooling
- Handles 429 (Too Many Requests) responses
- UTF-8 encoding support

**Usage:**
```python
from shopify_api import fetch_all_rest

# Fetch all products with pagination
products = fetch_all_rest(
    "products.json",
    params={"updated_at_min": "2025-11-17T00:00:00Z"},
    item_key="products"
)
```

---

### 5. **sync.py**
**Purpose:** Fetch and store Shopify data into normalized SQLite schema

**Responsibilities:**
- Fetch products with variants from Shopify API
- Fetch customers from Shopify API
- Fetch orders with line items from Shopify API
- Store data in normalized SQLite database
- Track last sync times for incremental updates
- Extract and preserve nested relationships

**Key Functions:**
- `fetch_and_store_products(incremental=True)` - Sync products and variants
- `fetch_and_store_customers(incremental=True)` - Sync customers
- `fetch_and_store_orders(incremental=True, status="any")` - Sync orders and line items
- `isoformat_for_api(dt)` - Convert datetime to Shopify API ISO 8601 format

**Features:**
- **Incremental Sync:** Only fetch items updated since last sync
- **Timestamp Tracking:** Stores last sync time for each entity type
- **Nested Data Extraction:**
  - Products → Product Variants
  - Orders → Line Items
  - Customers → Customer ID in Orders
- **Foreign Key Preservation:** Maintains relationships during insert
- **Error Handling:** Continues on errors, logs exceptions

**Sync Strategy:**
```
First Run:
  ├─ Fetch all products (10k+ items possible)
  ├─ Fetch all customers
  └─ Fetch all orders (full history)

Subsequent Runs (incremental):
  ├─ Fetch only updated products (since last_sync - 60s buffer)
  ├─ Fetch only updated customers
  └─ Fetch only updated orders
```

**Usage:**
```python
from sync import (
    fetch_and_store_products,
    fetch_and_store_customers,
    fetch_and_store_orders
)

# Incremental sync (default)
fetch_and_store_products(incremental=True)
fetch_and_store_customers(incremental=True)
fetch_and_store_orders(incremental=True)

# Full sync (force refresh all data)
fetch_and_store_products(incremental=False)
```

---

### 6. **csv_export.py**
**Purpose:** Export normalized CSV files for Power BI integration

**Responsibilities:**
- Export tables to CSV with proper normalization
- Maintain foreign key relationships in CSV structure
- Handle missing values and data types
- Create files compatible with Power BI relationships

**CSV Output Files:**

| File | Purpose | Rows | Foreign Keys |
|------|---------|------|--------------|
| products.csv | Product dimension | Variable | - |
| product_variants.csv | Product variants | Variable | product_id → products |
| customers.csv | Customer dimension | Variable | - |
| orders.csv | Order facts | Variable | customer_id → customers |
| line_items.csv | Order line items | Variable | order_id → orders, product_id → products |

**Key Functions:**
- `export_products_to_csv()` - Export products
- `export_product_variants_to_csv()` - Export variants with product_id FK
- `export_customers_to_csv()` - Export customers
- `export_orders_to_csv()` - Export orders with customer_id FK
- `export_line_items_to_csv()` - Export line items with order_id and product_id FKs
- `export_all_to_csv()` - Export all data files

**Features:**
- Normalized schema with proper column naming
- Foreign key columns included for Power BI relationships
- NaN values replaced with empty strings
- UTF-8 encoding with proper escaping
- Logging for each export operation
- Handles empty tables gracefully

**Usage:**
```python
from csv_export import export_all_to_csv

# Export all CSV files to data/ folder
export_all_to_csv()
```

---

### 7. **google_sheets.py**
**Purpose:** Google Sheets integration and data synchronization

**Responsibilities:**
- Initialize gspread client with service account authentication
- Create/manage worksheets in Google Sheets
- Push DataFrames to Google Sheets
- Sync all CSV data to corresponding sheets
- Handle authentication errors gracefully

**Key Functions:**
- `init_google_sheets()` - Initialize authenticated gspread client
- `get_or_create_worksheet(gc, sheet_id, worksheet_name)` - Manage worksheet lifecycle
- `push_dataframe_to_sheet(gc, sheet_id, dataframe, worksheet_name)` - Push data
- `sync_all_data_to_sheets(gc, sheet_id)` - Sync all CSV files

**Google Sheets Workflow:**

```
Pipeline Execution
       │
       ├─► CSV Export (to data/ folder)
       │
       ├─► Google Sheets Sync
       │   ├─ Authenticate via gspread_credentials.json
       │   ├─ Read CSVs into DataFrames
       │   ├─ For each DataFrame:
       │   │   ├─ Open or create worksheet
       │   │   ├─ Clear existing data
       │   │   └─ Write new data (headers + rows)
       │   │
       │   └─ Worksheets created:
       │       ├─ Products
       │       ├─ ProductVariants
       │       ├─ Customers
       │       ├─ Orders
       │       └─ LineItems
       │
       └─► Power BI Connected Service
           ├─ Detects Google Sheets updates
           ├─ Auto-refresh (on schedule)
           └─ Update dashboards
```

**Features:**
- Service account authentication (no user login needed)
- Automatic worksheet creation if missing
- Clear and replace strategy (full refresh each sync)
- Empty DataFrame handling
- Error logging and recovery

**Google Sheets Setup:**
1. Create Google Cloud Service Account
2. Download credentials JSON → `gspread_credentials.json`
3. Share Google Sheet with service account email
4. Add sheet ID to `.env` file: `GOOGLE_SHEET_ID=xxx`

**Usage:**
```python
from google_sheets import init_google_sheets, sync_all_data_to_sheets

gc = init_google_sheets()
if gc:
    sync_all_data_to_sheets(gc, GOOGLE_SHEET_ID)
```

---

### 8. **analytics.py**
**Purpose:** Generate analytics reports and key metrics from synced data

**Responsibilities:**
- Calculate business metrics (total orders, sales, AOV)
- Identify customer behavior patterns (repeat rate)
- Generate product performance insights
- Create summary JSON reports

**Key Metrics Calculated:**
- **Total Orders:** Count of all orders
- **Total Sales:** Sum of all order values
- **Average Order Value (AOV):** Mean order value
- **Repeat Customer Rate (%):** Percentage of customers with 2+ orders
- **Sales by Day:** Daily sales breakdown
- **Top 10 Products:** Best-selling products by quantity

**Key Functions:**
- `analytics_reports()` - Generate all analytics and save summary

**Output:**
- **Console/Log:** Detailed metrics output
- **File:** `data/analytics_summary.json` with summary data

**Usage:**
```python
from analytics import analytics_reports

# Generate all analytics reports
analytics_reports()
```

---

### 9. **main.py**
**Purpose:** Orchestration and CLI entry point for entire pipeline

**Responsibilities:**
- Coordinate all modules in proper sequence
- Parse command-line arguments
- Validate configuration before execution
- Support daemon mode with APScheduler
- Provide execution summaries and error handling

**CLI Interface:**

```bash
# Run once and exit (default)
python main.py --once

# Run scheduler daemon (every 10 minutes)
python main.py --daemon

# Force full (non-incremental) sync
python main.py --full

# Disable Google Sheets sync
python main.py --no-sheets

# Daemon with full sync
python main.py --daemon --full
```

**Pipeline Steps:**
```
1. ✓ Validate configuration
   └─ Check SHOPIFY_STORE, SHOPIFY_API_TOKEN

2. ✓ Initialize database
   └─ Create/migrate schema

3. ✓ Fetch and store products
   └─ Products + variants

4. ✓ Fetch and store customers
   └─ Customer records

5. ✓ Fetch and store orders
   └─ Orders + line items

6. ✓ Export to CSV
   └─ Normalized CSV files

7. ✓ Generate analytics
   └─ JSON summary + logging

8. ✓ Push to Google Sheets (optional)
   └─ Sync CSVs to sheets

Daemon Mode:
  └─ Repeat every 10 minutes (APScheduler)
```

**Key Functions:**
- `run_full_sync(incremental, push_to_sheets)` - Execute complete pipeline
- `validate_configuration()` - Verify environment setup
- `main()` - CLI argument parsing and mode selection

**Usage:**
```bash
cd scripts/
python main.py --daemon
```

---

## Power BI Integration

### Dashboard Architecture

The **Shopify Order Dashboard** is a comprehensive Power BI workbook with 4 main pages that visualizes data from Google Sheets in real-time.

**Connection Flow:**
```
SQLite (scripts) → Google Sheets → Power BI Desktop → Power Service → Dashboards
                                                              ↓
                                                        Scheduled Refresh
```

### Dashboard Pages

#### 1. **Overview Page**
**Metrics Displayed:**
- Total Orders: 120
- Total Customers: 38
- Average Order Value (AOV): $340.95
- Processing Time (Days): 0.99
- Total Sales: $40.91K
- Total Discounts: $3.26K
- Total Tax: $3.72K
- Outstanding Amount: $25.94K

**Visualizations:**
- Sales & Order Value (Combo Chart)
  - Yellow bars: Total sales per day
  - Purple line: Average order value trend
  - Time period: Jun 2024 - Nov 2024

- Customer & Orders (Stacked Column + Line Chart)
  - Blue bars: Number of orders per day
  - Green line: Number of customers

**Data Sources (from CSV):**
- `orders.csv` - Order values and dates
- `line_items.csv` - Order item breakdown
- `customers.csv` - Customer count

#### 2. **Geographic Overview Page**
**Purpose:** Analyze order distribution by location

**Key Metrics:**
- Orders by country/region
- Sales by location
- Customer distribution map
- Regional performance comparison

**Data Sources:**
- `orders.csv` - Geographic data (if available)
- `customers.csv` - Customer location info

#### 3. **Orders & Customers Page**
**Purpose:** Deep dive into order and customer analytics

**Visualizations:**
- Order timeline and trends
- Customer segmentation
- Order status breakdown
- Customer lifetime value
- Repeat purchase analysis

**Key Metrics:**
- Total orders by status
- Customer acquisition trend
- Repeat customer rate
- Order frequency distribution

**Data Sources:**
- `orders.csv` - Order details
- `customers.csv` - Customer data
- `line_items.csv` - Product-order relationships

#### 4. **Coherent Analysis Page**
**Purpose:** Integrated view of all key metrics

**Visualizations:**
- KPI scorecards
- Correlation analysis
- Trend analysis
- Year-over-year comparisons
- Performance metrics

**Key Insights:**
- Sales trends over time
- Customer behavior patterns
- Product performance
- Operational efficiency

**Data Sources:**
- All CSV files integrated

### Power BI Data Model

**Table Relationships:**

```
Products Table
    ├─ product_variants (FK: product_id)
    │
    └─ line_items (FK: product_id)
         │
         └─ orders (FK: order_id)
              │
              └─ customers (FK: customer_id)
```

**Refresh Strategy:**

| Component | Refresh Type | Frequency |
|-----------|--------------|-----------|
| Google Sheets | Manual push | Every 10 min (pipeline) |
| Power BI Desktop | Manual refresh | On demand |
| Power Service | Scheduled refresh | Configurable (e.g., hourly) |

### Dashboard File Location

```
dashboards/
├── shopify_analytics.pbix              # Power BI workbook
│   ├── Overview Page
│   ├── Geographic Overview Page
│   ├── Orders & Customers Page
│   └── Coherent Analysis Page
│
└── screenshots/
    ├── overview_preview.jpg            # Overview page snapshot
    ├── geographic_overview.jpg         # Geographic analysis snapshot
    ├── orders_customers.jpg            # Orders & Customers snapshot
    └── coherent_analysis.jpg           # Coherent Analysis snapshot
```

---

## Complete Data Flow

```
Real-Time Data Pipeline:

Shopify API
    ↓ (fetch_and_store_* functions)
SQLite Database (shopify_data.db)
    ├─ products table
    ├─ product_variants table
    ├─ customers table
    ├─ orders table
    ├─ line_items table
    └─ metadata table
    ↓ (export_all_to_csv)
CSV Files (data/ folder)
    ├─ products.csv
    ├─ product_variants.csv
    ├─ customers.csv
    ├─ orders.csv
    └─ line_items.csv
    ↓ (sync_all_data_to_sheets)
Google Sheets Workbook
    ├─ Products sheet (auto-updated)
    ├─ ProductVariants sheet
    ├─ Customers sheet
    ├─ Orders sheet
    └─ LineItems sheet
    ↓ (Power BI Connection)
Power BI Service
    ├─ Data Model (relationships)
    ├─ Dashboards
    └─ Refresh Schedule
```

---

## Environment Configuration

**Required Variables (.env):**
```env
# Shopify API
SHOPIFY_STORE=your-store-name
SHOPIFY_API_TOKEN=your-api-token

# Google Sheets (optional but recommended for dashboards)
GOOGLE_SHEET_ID=your-google-sheet-id
```

**Credentials File:**
```
gspread_credentials.json    # Google Cloud service account JSON
                            # Required for Google Sheets integration
```

---

## Installation & Setup

### 1. Clone/Setup Project
```bash
git clone <repo-url>
cd Real-Time-E-Commerce-Analytics-Platform
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

**Required Packages:**
- requests
- pandas
- gspread
- google-auth
- python-dotenv
- apscheduler
- sqlite3 (built-in)

### 3. Configure Environment
```bash
# Create .env file in project root
cat > .env << EOF
SHOPIFY_STORE=your-store-name
SHOPIFY_API_TOKEN=your-api-token
GOOGLE_SHEET_ID=your-sheet-id
EOF
```

### 4. Setup Google Sheets (Optional)
1. Create Google Cloud Service Account
2. Download credentials JSON
3. Save as `gspread_credentials.json` in project root
4. Share Google Sheet with service account email

### 5. Setup Power BI
1. Open Power BI Desktop
2. Load workbook: `dashboards/shopify_analytics.pbix`
3. Connect to Google Sheets data source
4. Configure refresh schedule in Power BI Service
5. Publish to Power BI Service

### 6. Run Pipeline
```bash
cd scripts/

# Single run
python main.py --once

# Daemon mode
python main.py --daemon
```

---

## Monitoring & Logging

### Log Files
Located in: `Real-Time-E-Commerce-Analytics-Platform/logs/`

**Log File Format:**
```
shopify_sync_20251118_143012.log
└─ Contains all execution details
   ├─ Sync timestamps
   ├─ Records fetched
   ├─ CSV exports
   ├─ Analytics calculations
   ├─ Google Sheets pushes
   └─ Errors and warnings
```

**Log Format:**
```
2025-11-18 15:30:12 - INFO - Starting products sync (incremental=True)
2025-11-18 15:30:15 - INFO - Fetched 2 pages from products.json (total items: 250)
2025-11-18 15:30:18 - INFO - Products sync complete: 125 products and 375 variants saved/updated.
```

### Monitoring Dashboard

Track pipeline execution:
1. Check logs in `logs/` folder
2. Monitor `data/analytics_summary.json` for latest metrics
3. View Power BI dashboard for visual insights
4. Verify CSV files updated in `data/` folder

---

## Troubleshooting

### Issue: "SHOPIFY_STORE not set"
**Solution:** Add to `.env`:
```env
SHOPIFY_STORE=your-store-name
```

### Issue: "Rate limited by Shopify"
**Solution:** Normal behavior - pipeline automatically retries with exponential backoff

### Issue: "Google Sheets not syncing"
**Solution:** Verify:
- `gspread_credentials.json` exists
- `GOOGLE_SHEET_ID` set in `.env`
- Service account has access to Google Sheet

### Issue: "Database locked"
**Solution:** Another instance is running or database file is corrupted
- Kill other Python processes
- Delete `shopify_data.db` to start fresh

### Issue: "Power BI not showing latest data"
**Solution:** 
- Manually refresh in Power BI Desktop
- Check Power Service refresh schedule
- Verify Google Sheets has latest data

---

## Performance Considerations

### Incremental Sync
- **Default:** Fetches only updated items since last sync
- **Benefit:** 80-90% faster than full sync
- **Data Loss Prevention:** 60-second buffer on timestamps

### Full Sync
- **Usage:** Force refresh all data
- **Command:** `python main.py --full`
- **Time:** 5-15 minutes depending on data volume

### API Rate Limiting
- **Limit:** 2 requests/second (Shopify)
- **Handling:** Automatic exponential backoff
- **Max Retries:** 5 attempts per request

### Database Optimization
- **Format:** SQLite (file-based, no server needed)
- **Size:** ~5-50MB for typical stores
- **Normalization:** Optimized for Power BI relationships

---

## Benefits of Modular Architecture

✅ **Separation of Concerns** - Each module has single responsibility  
✅ **Testability** - Easier to unit test individual components  
✅ **Reusability** - Modules can be imported and used independently  
✅ **Maintainability** - Clear structure with comprehensive documentation  
✅ **Scalability** - Easy to add new features or data sources  
✅ **Debugging** - Isolated issues are easier to track  
✅ **Deployment** - Simple to deploy and update  
✅ **Monitoring** - Comprehensive logging throughout pipeline  

---

## Advanced Usage

### Using Modules Independently

```python
# Use sync module standalone
from scripts.sync import fetch_and_store_products
from scripts.database import init_db

init_db()
fetch_and_store_products(incremental=False)

# Use analytics independently
from scripts.analytics import analytics_reports
analytics_reports()

# Use Google Sheets module
from scripts.google_sheets import init_google_sheets
gc = init_google_sheets()
```

### Custom Scheduling

```python
from apscheduler.schedulers.background import BackgroundScheduler
from scripts.main import run_full_sync

scheduler = BackgroundScheduler()

# Run every 5 minutes
scheduler.add_job(
    lambda: run_full_sync(incremental=True),
    'interval',
    minutes=5
)

scheduler.start()
```

---

## File Statistics

| Component | Files | Total Size |
|-----------|-------|-----------|
| Scripts | 10 Python modules | ~20KB |
| Data (initial) | SQLite DB | 1-50MB |
| CSV Exports | 5 CSV files | 10-100MB |
| Logs (daily) | Timestamped logs | 1-10MB |
| Dashboard | PBIX file | 5-20MB |
| Documentation | 3 MD files | ~200KB |

---

## Deployment Checklist

- [ ] Clone/download project
- [ ] Create `.env` with Shopify credentials
- [ ] Install Python dependencies
- [ ] Setup Google Cloud service account (optional)
- [ ] Configure Power BI connection (optional)
- [ ] Run first sync: `python main.py --once`
- [ ] Verify data in `data/` and `logs/` folders
- [ ] Setup daemon: `python main.py --daemon`
- [ ] Monitor dashboards and logs

---

## Support & Documentation

**Files Included:**
- `MODULES_GUIDE.md` - Detailed module documentation
- `QUICK_START.md` - Quick reference guide
- `MODULES_ARCHITECTURE.md` - This comprehensive guide
- `dashboards/README.md` - Power BI dashboard documentation
- `scripts/*.py` - Well-documented source code

**External Resources:**
- Shopify API Docs: https://shopify.dev/api
- Power BI Docs: https://docs.microsoft.com/power-bi/
- gspread Docs: https://docs.gspread.org/

---

**Version:** 2.1 (Integrated with Power BI)  
**Last Updated:** 2025-11-18  
**Architecture:** Modular, Event-Driven, Cloud-Connected
