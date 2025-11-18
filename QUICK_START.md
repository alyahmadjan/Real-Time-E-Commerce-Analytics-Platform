# Quick Reference - Shopify Sync Pipeline Modules

## File Organization

Place all these files in your `scripts/` folder:

```
scripts/
├── __init__.py                  # Package initialization
├── main.py                      # Entry point - Run this!
├── config.py                    # Configuration
├── database.py                  # Database management
├── shopify_api.py               # API wrapper
├── sync.py                      # Data fetching
├── csv_export.py                # CSV export
├── analytics.py                 # Analytics reports
├── google_sheets.py             # Google Sheets sync
└── logger_config.py             # Logging setup
```

## Quick Start

### 1. Setup
```bash
# Navigate to scripts folder
cd scripts/

# Install dependencies (if not already done)
pip install -r requirements.txt
```

### 2. Configure
Edit `.env` in the parent directory:
```env
SHOPIFY_STORE=your-store-name
SHOPIFY_API_TOKEN=your-access-token
GOOGLE_SHEET_ID=your-sheet-id (optional)
```

### 3. Run

**One-time sync:**
```bash
python main.py --once
```

**Daemon mode (every 10 minutes):**
```bash
python main.py --daemon
```

**Force full sync:**
```bash
python main.py --full
```

**Daemon with full sync:**
```bash
python main.py --daemon --full
```

**No Google Sheets:**
```bash
python main.py --once --no-sheets
```

## Module Functions Quick Reference

### config.py
```python
from config import (
    SHOPIFY_STORE,           # Store name from .env
    SHOPIFY_API_TOKEN,       # API token from .env
    BASE_URL,                # API base URL
    DB_FILE,                 # Database file path
    CSV_PRODUCTS,            # Products CSV path
    GOOGLE_SHEET_ID          # Sheet ID from .env
)
```

### database.py
```python
from database import (
    init_db(),                           # Initialize database
    db_set_metadata(key, value),        # Store metadata
    db_get_metadata(key)                # Retrieve metadata
)
```

### shopify_api.py
```python
from shopify_api import (
    fetch_all_rest(endpoint, params, item_key),  # Fetch with pagination
    request_with_retries(url, params, method)    # HTTP request with retry
)
```

### sync.py
```python
from sync import (
    fetch_and_store_products(incremental=True),    # Sync products
    fetch_and_store_customers(incremental=True),   # Sync customers
    fetch_and_store_orders(incremental=True)       # Sync orders
)
```

### csv_export.py
```python
from csv_export import (
    export_all_to_csv(),                # Export all CSV files
    export_products_to_csv(),           # Export products only
    export_customers_to_csv()           # Export customers only
    # ... individual export functions
)
```

### analytics.py
```python
from analytics import (
    analytics_reports()  # Generate and save reports
)
```

### google_sheets.py
```python
from google_sheets import (
    init_google_sheets(),                          # Authenticate
    sync_all_data_to_sheets(gc, sheet_id)         # Push all data
)
```

### logger_config.py
```python
from logger_config import logger

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
```

### main.py
```python
from main import run_full_sync

# Run complete pipeline
run_full_sync(incremental=True, push_to_sheets=True)
```

## Pipeline Flow

1. **main.py** validates config
2. **database.py** initializes/migrates schema
3. **sync.py** fetches from Shopify via **shopify_api.py**
4. Data stored in SQLite database
5. **csv_export.py** exports to CSV files
6. **analytics.py** generates reports
7. **google_sheets.py** pushes to Google Sheets (optional)
8. **logger_config.py** logs everything

## Database Tables

| Table | Purpose | Foreign Keys |
|-------|---------|--------------|
| metadata | Track last sync times | - |
| products | Product dimension | - |
| product_variants | Variant details | product_id → products |
| customers | Customer dimension | - |
| orders | Order facts | customer_id → customers |
| line_items | Order line items | order_id → orders, product_id → products |

## CSV Output Files

All exported to `data/` folder:

- `products.csv` - Product dimension
- `product_variants.csv` - Variants with product_id FK
- `customers.csv` - Customer dimension
- `orders.csv` - Orders with customer_id FK
- `line_items.csv` - Line items with order_id and product_id FKs
- `analytics_summary.json` - Metrics summary

## Logging

Logs are saved to `logs/shopify_sync_YYYYMMDD_HHMMSS.log`

Real-time output shows to console as INFO level and above.

## Common Issues

### "SHOPIFY_STORE not set"
→ Add to `.env`: `SHOPIFY_STORE=your-store-name`

### "SHOPIFY_API_TOKEN not found"
→ Add to `.env`: `SHOPIFY_API_TOKEN=your-token`

### "Rate limited by Shopify"
→ Normal - the pipeline will automatically retry with backoff

### "Database locked"
→ Another instance is running, or database file is corrupted

### "Google Sheets not syncing"
→ Check `gspread_credentials.json` exists and `GOOGLE_SHEET_ID` is set

## Performance Tips

- **Incremental sync** (default): Only fetches changed data since last sync
- **Full sync** (`--full`): Fetches all data, slower but comprehensive
- First run will take longer as all data is fetched
- Subsequent runs are faster due to incremental updates
- API rate limit: 2 requests/second (handled automatically)

## File Size Notes

- SQLite database: Grows with data (~5-50MB typical)
- CSV files: Much larger than database (text format)
- Log files: ~1MB per day (configurable)
- Consider archiving old logs periodically

## Next Steps

1. ✅ Place all files in `scripts/` folder
2. ✅ Setup `.env` file
3. ✅ Run: `python main.py --once`
4. ✅ Check `logs/` for execution details
5. ✅ Verify CSV files in `data/` folder
6. ✅ Setup daemon: `python main.py --daemon`

---

**Document Version:** 2.0  
**Last Updated:** 2025-11-18
