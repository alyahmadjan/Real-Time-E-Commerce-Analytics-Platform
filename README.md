# Real-Time E-Commerce Analytics Platform - Complete Documentation

## 📊 System Overview

A **complete, modularized real-time e-commerce analytics platform** that automatically syncs Shopify data, processes it through a normalized SQLite database, exports to Google Sheets, and visualizes it in Power BI dashboards.

**Architecture:** Shopify API → SQLite → CSV → Google Sheets → Power BI

---

## 📁 Project Structure

```
Real-Time-E-Commerce-Analytics-Platform/
│
├── 📂 scripts/                          # Python pipeline modules
│   ├── main.py                          # Orchestration & CLI entry point
│   ├── config.py                        # Configuration management
│   ├── database.py                      # SQLite initialization & schema
│   ├── shopify_api.py                   # Shopify REST API wrapper
│   ├── sync.py                          # Data fetching & storage
│   ├── csv_export.py                    # Normalized CSV export
│   ├── analytics.py                     # Metrics & reports generation
│   ├── google_sheets.py                 # Google Sheets integration
│   ├── logger_config.py                 # Logging configuration
│   └── __init__.py                      # Package initialization
│
├── 📂 data/                             # Data storage
│   ├── shopify_data.db                  # SQLite database (normalized)
│   ├── customers.csv                    # Customer dimension
│   ├── orders.csv                       # Order facts
│   ├── line_items.csv                   # Order line items
│   ├── product_variants.csv             # Product variants
│   ├── products.csv                     # Product dimension
│   └── analytics_summary.json           # Key metrics (JSON)
│
├── 📂 logs/                             # Execution logs
│   └── shopify_sync_*.log               # Timestamped log files
│
├── 📂 dashboards/                       # Power BI dashboards
│   ├── shopify_analytics.pbix           # Main Power BI workbook
│   ├── screenshots/
│   │   ├── overview_preview.jpg         # Overview page
│   │   ├── geographic_overview.jpg      # Geographic page
│   │   ├── orders_customers.jpg         # Orders & Customers page
│   │   └── coherent_analysis.jpg        # Coherent Analysis page
│   └── README.md                        # Dashboard documentation
│
├── .env                                 # Environment variables
├── gspread_credentials.json             # Google Sheets auth
└── ...
```

---

## 🔄 Data Pipeline Flow

### Complete Data Journey

```
┌─────────────────────────────────────────────┐
│        Shopify Admin REST API               │
│  (Products, Orders, Customers, Variants)    │
└────────────────────┬────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   shopify_api.py     │
          │  (API Client)        │
          │  • Pagination        │
          │  • Rate Limiting     │
          │  • Retries           │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │    sync.py           │
          │  (Fetch & Store)     │
          │  • Extract nested    │
          │  • Incremental sync  │
          │  • Timestamp track   │
          └──────────┬───────────┘
                     │
                     ▼
     ┌───────────────────────────────┐
     │   SQLite Database             │
     │   (Normalized Schema)         │
     │   • products                  │
     │   • product_variants          │
     │   • customers                 │
     │   • orders                    │
     │   • line_items                │
     │   • metadata                  │
     └───────┬───────────┬──────┬────┘
             │           │      │
             ▼           ▼      ▼
    ┌──────────────┐ ┌────────────┐ ┌──────────┐
    │ csv_export   │ │ analytics  │ │ logger   │
    │ (Normalized) │ │ (Reports)  │ │ (Logs)   │
    └──────┬───────┘ └────┬───────┘ └──────────┘
           │               │
      CSV Files       JSON Summary
           │               │
           └───────┬───────┘
                   │
                   ▼
         ┌──────────────────────┐
         │ google_sheets.py     │
         │ (Push to Sheets)     │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Google Sheets       │
         │  (Auto-Updated)      │
         │  • Products          │
         │  • Customers         │
         │  • Orders            │
         │  • LineItems         │
         │  • Variants          │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Power BI Service    │
         │  (Dashboards)        │
         │  • Overview          │
         │  • Geographic        │
         │  • Orders & Cust.    │
         │  • Coherent Analysis │
         └──────────────────────┘
```

---

## 📋 Module Functions

### scripts/config.py
Centralized configuration, environment variables, file paths

**Key Exports:**
- `SHOPIFY_STORE`, `SHOPIFY_API_TOKEN`
- `BASE_URL`, `DB_FILE`, `CSV_*` paths
- `GOOGLE_SHEET_ID`, `GSPREAD_CREDENTIALS_FILE`

### scripts/logger_config.py
Logging configuration with timestamped file rotation

**Output:** `Real-Time-E-Commerce-Analytics-Platform/logs/shopify_sync_*.log`

### scripts/database.py
SQLite schema initialization and management

**Tables:**
- metadata, products, product_variants, customers, orders, line_items

**Functions:**
- `init_db()`, `db_set_metadata()`, `db_get_metadata()`

### scripts/shopify_api.py
Shopify REST API wrapper with pagination and rate limiting

**Functions:**
- `fetch_all_rest()`, `request_with_retries()`, `parse_link_header()`

**Features:**
- Exponential backoff, automatic pagination, 30s timeout

### scripts/sync.py
Fetch and store Shopify data in normalized schema

**Functions:**
- `fetch_and_store_products()`
- `fetch_and_store_customers()`
- `fetch_and_store_orders()`

**Feature:** Incremental sync (default) vs Full sync

### scripts/csv_export.py
Export normalized CSV files with proper foreign keys

**Outputs:**
- products.csv, product_variants.csv, customers.csv, orders.csv, line_items.csv

**Format:** Power BI optimized with FK columns

### scripts/analytics.py
Generate analytics reports and key metrics

**Metrics:**
- Total orders, sales, AOV, repeat rate, top products

**Output:** `data/analytics_summary.json` + console logs

### scripts/google_sheets.py
Google Sheets integration and data synchronization

**Functions:**
- `init_google_sheets()`, `sync_all_data_to_sheets()`

**Creates Worksheets:** Products, Customers, Orders, LineItems, Variants

### scripts/main.py
Orchestration and CLI entry point

**CLI:**
```bash
python main.py --once                  # Single run (default)
python main.py --daemon                # Every 10 minutes
python main.py --full                  # Force full sync
python main.py --no-sheets             # Skip Google Sheets
python main.py --daemon --full         # Daemon with full sync
```

---

## 📊 Database Schema (Normalized for Power BI)

### Tables & Relationships

```
products (PK: id)
    ├─ 1:N ─→ product_variants (FK: product_id)
    └─ 1:N ─→ line_items (FK: product_id)

customers (PK: id)
    └─ 1:N ─→ orders (FK: customer_id)
         └─ 1:N ─→ line_items (FK: order_id)

metadata (KV store for sync tracking)
```

### CSV Files for Power BI

| File | Role | Records | FKs |
|------|------|---------|-----|
| products.csv | Dimension | Variable | - |
| product_variants.csv | Dimension | Variable | product_id |
| customers.csv | Dimension | Variable | - |
| orders.csv | Fact | Variable | customer_id |
| line_items.csv | Fact | Variable | order_id, product_id |

---

## 📈 Power BI Dashboard

### Dashboard Pages

#### 1. **Overview Page**
KPIs: Total Orders (120), Customers (38), AOV ($340.95), Processing Time (0.99 days)

Financial: Total Sales ($40.91K), Discounts ($3.26K), Tax ($3.72K), Outstanding ($25.94K)

Visualizations:
- Sales & Order Value (Jun 2024 - Nov 2024)
- Customer & Orders trends

#### 2. **Geographic Overview Page**
- Order distribution by location
- Sales by region
- Customer distribution map
- Regional performance comparison

#### 3. **Orders & Customers Page**
- Order timeline and status breakdown
- Customer segmentation
- Customer lifetime value
- Repeat purchase analysis
- Customer acquisition trends

#### 4. **Coherent Analysis Page**
- Integrated KPI scorecards
- Correlation analysis
- Trend comparisons
- Performance metrics
- Year-over-year analysis

---

## 🚀 Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Create .env file
echo "SHOPIFY_STORE=your-store" > .env
echo "SHOPIFY_API_TOKEN=your-token" >> .env
echo "GOOGLE_SHEET_ID=your-sheet-id" >> .env
```

### 3. Setup Google Sheets (Optional)
1. Create Google Cloud service account
2. Download credentials JSON
3. Save as `gspread_credentials.json` (project root)
4. Share Google Sheet with service account email

### 4. Run Pipeline
```bash
cd scripts/
python main.py --once        # Single run
python main.py --daemon      # Daemon mode
```

### 5. Setup Power BI (Optional)
1. Open `dashboards/shopify_analytics.pbix`
2. Connect to Google Sheets data source
3. Configure refresh schedule
4. Publish to Power BI Service

---

## 📝 Execution Flow

### Pipeline Execution (Every 10 minutes in daemon mode)

```
Step 1: Validate Configuration
        ├─ SHOPIFY_STORE set
        └─ SHOPIFY_API_TOKEN set

Step 2: Initialize Database
        └─ Create/migrate schema

Step 3: Fetch & Store Data
        ├─ Fetch products (+ variants)
        ├─ Fetch customers
        └─ Fetch orders (+ line items)

Step 4: Export to CSV
        └─ Normalize data for Power BI

Step 5: Generate Analytics
        └─ Calculate metrics, save JSON

Step 6: Push to Google Sheets (Optional)
        └─ Sync CSVs to worksheets

✅ COMPLETE
```

---

## 📋 Documentation Files

| File | Purpose |
|------|---------|
| MODULES_ARCHITECTURE.md | Complete system architecture |
| MODULES_GUIDE_UPDATED.md | Module descriptions & functions |
| POWER_BI_DASHBOARD_GUIDE.md | Dashboard pages & usage |
| QUICK_START.md | Quick reference commands |

---

## 🔍 Monitoring & Logging

### Log Files
Location: `Real-Time-E-Commerce-Analytics-Platform/logs/`

Format: `shopify_sync_YYYYMMDD_HHMMSS.log`

Contains:
- Sync start/end times
- Records fetched
- CSV exports
- Analytics calculations
- Google Sheets operations
- Errors and warnings

### Monitoring Checklist
- ✅ Check `logs/` for execution details
- ✅ Verify CSV files in `data/` folder
- ✅ Monitor `data/analytics_summary.json`
- ✅ View Power BI dashboard
- ✅ Track database size growth

---

## 🎯 Key Features

✅ **Modular Architecture** - 9 specialized Python modules
✅ **Automated Scheduling** - APScheduler (every 10 minutes)
✅ **Normalized Schema** - Power BI optimized database
✅ **Incremental Sync** - 80-90% faster updates
✅ **Rate Limiting** - Automatic retry with backoff
✅ **Real-time Logging** - Timestamped file + console
✅ **CSV Export** - Normalized with foreign keys
✅ **Google Sheets** - Auto-updated worksheets
✅ **Power BI Integration** - 4-page dashboard
✅ **CLI Interface** - Flexible command-line options

---

## ⚙️ Configuration

### Required Environment Variables
```env
SHOPIFY_STORE=your-store-name
SHOPIFY_API_TOKEN=your-api-token
```

### Optional
```env
GOOGLE_SHEET_ID=your-sheet-id
```

### Credentials
- `gspread_credentials.json` - Google Cloud service account

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| SHOPIFY_STORE not set | Add to .env |
| Rate limited by Shopify | Normal - auto-retry with backoff |
| Google Sheets not syncing | Verify credentials and sheet ID |
| Database locked | Kill other processes or delete DB |
| Power BI showing old data | Check refresh schedule |

---

## 📊 Performance

| Aspect | Value |
|--------|-------|
| Sync Frequency | 10 minutes (configurable) |
| First Run | 5-15 minutes (full data) |
| Subsequent Runs | 30-60 seconds (incremental) |
| API Rate Limit | 2 requests/second |
| Database Size | 5-50 MB typical |
| CSV Size | 10-100 MB typical |

---

## 📚 Next Steps

1. ✅ Install dependencies
2. ✅ Configure `.env` file
3. ✅ Setup Google Cloud (optional)
4. ✅ Run first sync: `python main.py --once`
5. ✅ Start daemon: `python main.py --daemon`
6. ✅ Setup Power BI connection (optional)
7. ✅ Monitor dashboard

---

## 📞 Support

**Documentation:**
- MODULES_ARCHITECTURE.md - System design
- MODULES_GUIDE_UPDATED.md - Module details
- POWER_BI_DASHBOARD_GUIDE.md - Dashboard help
- QUICK_START.md - Quick reference

**Source Code:**
- All Python files well-commented
- Docstrings for every function
- Comprehensive error handling

**Logs:**
- Real-time execution tracking
- Detailed error messages
- Performance metrics

---

## 📈 Architecture Summary

```
                    REAL-TIME DATA PLATFORM
    ┌──────────────────────────────────────────────────┐
    │                                                  │
    │  Shopify API                                     │
    │  ↓ (shopify_api.py)                             │
    │                                                  │
    │  SQLite Database (9 modules)                     │
    │  ├─ config, logger, database                     │
    │  ├─ shopify_api, sync                            │
    │  ├─ csv_export, analytics                        │
    │  ├─ google_sheets, main                          │
    │  └─ __init__.py                                  │
    │                                                  │
    │  Google Sheets ← Automatic Sync                  │
    │                                                  │
    │  Power BI Dashboard ← Scheduled Refresh          │
    │  ├─ Overview Page                                │
    │  ├─ Geographic Analysis                          │
    │  ├─ Orders & Customers                           │
    │  └─ Coherent Analysis                            │
    │                                                  │
    └──────────────────────────────────────────────────┘
    
    Real-Time: ✅ Shopify → SQLite (every 10 min)
    Auto-Updated: ✅ SQLite → Google Sheets (pipeline)
    BI Ready: ✅ Google Sheets → Power BI (scheduled)
```

---

**Version:** 2.1 (Integrated with Power BI)  
**Last Updated:** 2025-11-18  
**Status:** Production Ready  
**Architecture:** Modular, Cloud-Connected, Event-Driven
