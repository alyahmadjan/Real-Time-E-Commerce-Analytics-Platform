#!/usr/bin/env python3

"""
shopify_sync.py

- Loads credentials from .env located in parent directory (Real-Time-E-Commerce-Analytics-Platform)
- Fetches products, orders, customers from Shopify Admin REST API
- Stores/updates them in a local SQLite DB (shopify_data.db) inside data folder
- Tracks last sync times to perform incremental updates
- Provides basic analytics reports (CSV + printed summary)
- Creates normalized CSV files with proper foreign keys for Power BI:
- customers.csv (Customer dimension)
- orders.csv (Order facts with customer_id FK)
- line_items.csv (Order line items with order_id and product_id FKs)
- product_variants.csv (Product variants with product_id FK)
- products.csv (Product dimension)
- Pushes data to Google Sheets automatically
- Optionally runs as a scheduled job using APScheduler
- Scheduler runs every 10 minutes
- Includes schema migration for backward compatibility
"""

import os
import time
import json
import sqlite3
import logging
import argparse
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs, urljoin
from pathlib import Path
import requests
import pandas as pd
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
import gspread
from google.oauth2.service_account import Credentials

# -------------- Config & Logging --------------

# Get the parent directory (Real-Time-E-Commerce-Analytics-Platform)
SCRIPT_DIR = Path(__file__).parent # scripts folder
PROJECT_DIR = SCRIPT_DIR.parent # Real-Time-E-Commerce-Analytics-Platform
DATA_DIR = PROJECT_DIR / "data"
ENV_FILE = PROJECT_DIR / ".env"
GSPREAD_CREDENTIALS_FILE = PROJECT_DIR / "gspread_credentials.json"

# Create data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)

# Load environment variables from parent directory
load_dotenv(ENV_FILE)

SHOPIFY_STORE = os.getenv("SHOPIFY_STORE") # e.g., "quantum-spectra-store"
SHOPIFY_API_TOKEN = os.getenv("SHOPIFY_API_TOKEN")
API_VERSION = "2024-10"
BASE_URL = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/{API_VERSION}/"
DB_FILE = DATA_DIR / "shopify_data.db"
CSV_CUSTOMERS = DATA_DIR / "customers.csv"
CSV_ORDERS = DATA_DIR / "orders.csv"
CSV_LINE_ITEMS = DATA_DIR / "line_items.csv"
CSV_PRODUCT_VARIANTS = DATA_DIR / "product_variants.csv"
CSV_PRODUCTS = DATA_DIR / "products.csv"
REQUESTS_SESSION = requests.Session()

REQUESTS_SESSION.headers.update({
    "X-Shopify-Access-Token": SHOPIFY_API_TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json",
})

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# -------------- Google Sheets Config --------------

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID") # Load from .env

def init_google_sheets():
    """Initialize and return authorized gspread client"""
    try:
        if not GSPREAD_CREDENTIALS_FILE.exists():
            logging.error("Google credentials file not found at: %s", GSPREAD_CREDENTIALS_FILE)
            return None
        credentials = Credentials.from_service_account_file(
            GSPREAD_CREDENTIALS_FILE,
            scopes=SCOPES
        )
        gc = gspread.authorize(credentials)
        logging.info("Google Sheets client initialized successfully")
        return gc
    except Exception as e:
        logging.exception("Failed to initialize Google Sheets client: %s", e)
        return None

def get_or_create_worksheet(gc, sheet_id, worksheet_name):
    """Get existing worksheet or create new one"""
    try:
        if not sheet_id:
            logging.error("GOOGLE_SHEET_ID not set in .env file")
            return None
        spreadsheet = gc.open_by_key(sheet_id)
        # Try to find existing worksheet
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            logging.info("Using existing worksheet: %s", worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Create new worksheet if it doesn't exist
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1, cols=1)
            logging.info("Created new worksheet: %s", worksheet_name)
        return worksheet
    except Exception as e:
        logging.exception("Error accessing/creating worksheet '%s': %s", worksheet_name, e)
        return None

def push_dataframe_to_sheet(gc, sheet_id, dataframe, worksheet_name):
    """Push a pandas DataFrame to a Google Sheet"""
    try:
        if dataframe.empty:
            logging.warning("DataFrame is empty, skipping push to %s", worksheet_name)
            return False
        worksheet = get_or_create_worksheet(gc, sheet_id, worksheet_name)
        if not worksheet:
            return False
        # Clear existing data
        worksheet.clear()
        # Replace NaN values with empty strings
        dataframe = dataframe.fillna("")
        # Prepare data: headers + rows
        data_to_push = [dataframe.columns.tolist()] + dataframe.values.tolist()
        # Update worksheet with new data
        worksheet.update(data_to_push)
        logging.info("Successfully pushed %s rows to Google Sheet '%s'", len(dataframe), worksheet_name)
        return True
    except Exception as e:
        logging.exception("Error pushing data to Google Sheet '%s': %s", worksheet_name, e)
        return False

def sync_all_data_to_sheets(gc, sheet_id):
    """Sync all CSV data to Google Sheets"""
    if not gc or not sheet_id:
        logging.warning("Google Sheets client or Sheet ID not available, skipping sync")
        return False
    all_successful = True
    # Sync products
    if CSV_PRODUCTS.exists():
        try:
            products_df = pd.read_csv(CSV_PRODUCTS)
            if not push_dataframe_to_sheet(gc, sheet_id, products_df, "Products"):
                all_successful = False
        except Exception as e:
            logging.exception("Error reading/pushing products CSV: %s", e)
            all_successful = False
    # Sync product variants
    if CSV_PRODUCT_VARIANTS.exists():
        try:
            variants_df = pd.read_csv(CSV_PRODUCT_VARIANTS)
            if not push_dataframe_to_sheet(gc, sheet_id, variants_df, "ProductVariants"):
                all_successful = False
        except Exception as e:
            logging.exception("Error reading/pushing product variants CSV: %s", e)
            all_successful = False
    # Sync customers
    if CSV_CUSTOMERS.exists():
        try:
            customers_df = pd.read_csv(CSV_CUSTOMERS)
            if not push_dataframe_to_sheet(gc, sheet_id, customers_df, "Customers"):
                all_successful = False
        except Exception as e:
            logging.exception("Error reading/pushing customers CSV: %s", e)
            all_successful = False
    # Sync orders
    if CSV_ORDERS.exists():
        try:
            orders_df = pd.read_csv(CSV_ORDERS)
            if not push_dataframe_to_sheet(gc, sheet_id, orders_df, "Orders"):
                all_successful = False
        except Exception as e:
            logging.exception("Error reading/pushing orders CSV: %s", e)
            all_successful = False
    # Sync line items
    if CSV_LINE_ITEMS.exists():
        try:
            line_items_df = pd.read_csv(CSV_LINE_ITEMS)
            if not push_dataframe_to_sheet(gc, sheet_id, line_items_df, "LineItems"):
                all_successful = False
        except Exception as e:
            logging.exception("Error reading/pushing line items CSV: %s", e)
            all_successful = False
    return all_successful

# -------------- DB helpers with schema migration --------------

def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns
    except Exception:
        return False

def add_column_if_missing(conn, table_name, column_name, column_definition):
    """Add a column to a table if it doesn't exist"""
    if not column_exists(conn, table_name, column_name):
        try:
            cursor = conn.cursor()
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
            conn.commit()
            logging.info("Added column %s to table %s", column_name, table_name)
            return True
        except Exception as e:
            logging.warning("Could not add column %s to %s: %s", column_name, table_name, e)
            return False
    return True

def migrate_schema(conn):
    """Migrate database schema for backward compatibility"""
    logging.info("Running schema migration checks...")
    # Products table
    add_column_if_missing(conn, "products", "id", "INTEGER PRIMARY KEY")
    add_column_if_missing(conn, "products", "title", "TEXT")
    add_column_if_missing(conn, "products", "vendor", "TEXT")
    add_column_if_missing(conn, "products", "product_type", "TEXT")
    add_column_if_missing(conn, "products", "created_at", "TEXT")
    add_column_if_missing(conn, "products", "updated_at", "TEXT")
    add_column_if_missing(conn, "products", "raw_json", "TEXT")
    # Customers table
    add_column_if_missing(conn, "customers", "id", "INTEGER PRIMARY KEY")
    add_column_if_missing(conn, "customers", "first_name", "TEXT")
    add_column_if_missing(conn, "customers", "last_name", "TEXT")
    add_column_if_missing(conn, "customers", "email", "TEXT")
    add_column_if_missing(conn, "customers", "phone", "TEXT")
    add_column_if_missing(conn, "customers", "created_at", "TEXT")
    add_column_if_missing(conn, "customers", "updated_at", "TEXT")
    add_column_if_missing(conn, "customers", "raw_json", "TEXT")
    # Orders table
    add_column_if_missing(conn, "orders", "id", "INTEGER PRIMARY KEY")
    add_column_if_missing(conn, "orders", "order_number", "TEXT")
    add_column_if_missing(conn, "orders", "customer_id", "INTEGER")
    add_column_if_missing(conn, "orders", "email", "TEXT")
    add_column_if_missing(conn, "orders", "total_price", "REAL")
    add_column_if_missing(conn, "orders", "currency", "TEXT")
    add_column_if_missing(conn, "orders", "created_at", "TEXT")
    add_column_if_missing(conn, "orders", "updated_at", "TEXT")
    add_column_if_missing(conn, "orders", "financial_status", "TEXT")
    add_column_if_missing(conn, "orders", "fulfillment_status", "TEXT")
    add_column_if_missing(conn, "orders", "raw_json", "TEXT")
    logging.info("Schema migration complete")

def init_db():
    """Initialize database with normalized schema for Power BI relationships"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # Metadata table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    # Products table (dimension)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        title TEXT,
        vendor TEXT,
        product_type TEXT,
        created_at TEXT,
        updated_at TEXT,
        raw_json TEXT
    )
    """)
    # Product Variants table (links to products via product_id)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS product_variants (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        title TEXT,
        sku TEXT,
        price REAL,
        compare_at_price REAL,
        position INTEGER,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        created_at TEXT,
        updated_at TEXT,
        raw_json TEXT,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
    # Customers table (dimension)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        phone TEXT,
        created_at TEXT,
        updated_at TEXT,
        raw_json TEXT
    )
    """)
    # Orders table (facts with customer_id FK)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        order_number TEXT,
        customer_id INTEGER,
        email TEXT,
        total_price REAL,
        currency TEXT,
        created_at TEXT,
        updated_at TEXT,
        financial_status TEXT,
        fulfillment_status TEXT,
        raw_json TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )
    """)
    # Line Items table (links orders to products via order_id and product_id)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS line_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER,
        variant_id INTEGER,
        title TEXT,
        quantity INTEGER,
        price REAL,
        sku TEXT,
        raw_json TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (variant_id) REFERENCES product_variants(id)
    )
    """)
    conn.commit()
    # Run schema migration for backward compatibility
    migrate_schema(conn)
    conn.close()

def db_set_metadata(key: str, value: str):
    """Set metadata value"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def db_get_metadata(key: str):
    """Get metadata value"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT value FROM metadata WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

# -------------- Shopify HTTP + Pagination helpers --------------

def parse_link_header(header: str):
    """Parse Link header and return a dict of rel->url"""
    links = {}
    if not header:
        return links
    parts = header.split(",")
    for p in parts:
        section = p.strip().split(";")
        if len(section) < 2:
            continue
        url_part = section[0].strip()
        rel_part = section[1].strip()
        url = url_part[url_part.find("<")+1:url_part.find(">")]
        rel = rel_part.split("=")[1].strip('"')
        links[rel] = url
    return links

def request_with_retries(url, params=None, method="GET", max_retries=5):
    """Fetch URL with retry logic for rate limiting"""
    sleep_seconds = 1
    for attempt in range(max_retries):
        try:
            if method == "GET":
                resp = REQUESTS_SESSION.get(url, params=params, timeout=30)
            else:
                resp = REQUESTS_SESSION.request(method, url, params=params, timeout=30)
            if resp.status_code == 429:
                # Rate limited - wait and retry
                retry_after = int(resp.headers.get("Retry-After", sleep_seconds))
                logging.warning("Rate limited by Shopify. Sleeping %s seconds.", retry_after)
                time.sleep(retry_after)
                sleep_seconds *= 2
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            logging.exception("Request failed (attempt %s/%s): %s", attempt+1, max_retries, e)
            time.sleep(sleep_seconds)
            sleep_seconds *= 2
    raise RuntimeError(f"Failed to fetch url after {max_retries} attempts: {url}")

def fetch_all_rest(endpoint: str, params: dict = None, item_key: str = None):
    """Fetch all pages for a REST endpoint using pagination"""
    url = urljoin(BASE_URL, endpoint)
    params = params or {}
    params.setdefault("limit", 250)
    all_items = []
    page_count = 0
    resp = request_with_retries(url, params=params)
    page_count += 1
    data = resp.json()
    if item_key:
        items = data.get(item_key, [])
        all_items.extend(items)
    else:
        all_items.append(data)
    links = parse_link_header(resp.headers.get("Link", ""))
    while links.get("next"):
        next_url = links["next"]
        resp = request_with_retries(next_url)
        page_count += 1
        data = resp.json()
        if item_key:
            all_items.extend(data.get(item_key, []))
        else:
            all_items.append(data)
        links = parse_link_header(resp.headers.get("Link", ""))
    logging.info("Fetched %s pages from %s (total items: %s)", page_count, endpoint, len(all_items))
    return all_items

# -------------- Sync functions --------------

def isoformat_for_api(dt: datetime):
    """Convert datetime to Shopify API ISO 8601 format"""
    return dt.astimezone(timezone.utc).replace(tzinfo=None).isoformat() + "Z"

def fetch_and_store_products(incremental=True):
    """Fetch products and product variants from Shopify"""
    logging.info("Starting products sync (incremental=%s)", incremental)
    last_sync = db_get_metadata("products_last_sync")
    params = {"limit": 250}
    if incremental and last_sync:
        last_dt = datetime.fromisoformat(last_sync)
        last_dt = last_dt - timedelta(seconds=60)
        params["updated_at_min"] = isoformat_for_api(last_dt)
    items = fetch_all_rest("products.json", params=params, item_key="products")
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    saved_products = 0
    saved_variants = 0
    max_updated = None
    for p in items:
        saved_products += 1
        pid = p["id"]
        updated_at = p.get("updated_at")
        # Store product
        cur.execute("""
        INSERT OR REPLACE INTO products (id, title, vendor, product_type, created_at, updated_at, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            pid,
            p.get("title"),
            p.get("vendor"),
            p.get("product_type"),
            p.get("created_at"),
            updated_at,
            json.dumps(p)
        ))
        # Store variants (each product has variants array)
        variants = p.get("variants", [])
        for v in variants:
            saved_variants += 1
            vid = v["id"]
            cur.execute("""
            INSERT OR REPLACE INTO product_variants
            (id, product_id, title, sku, price, compare_at_price, position, option1, option2, option3, created_at, updated_at, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vid,
                pid,
                v.get("title"),
                v.get("sku"),
                v.get("price"),
                v.get("compare_at_price"),
                v.get("position"),
                v.get("option1"),
                v.get("option2"),
                v.get("option3"),
                v.get("created_at"),
                v.get("updated_at"),
                json.dumps(v)
            ))
        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                if not max_updated or dt > max_updated:
                    max_updated = dt
            except Exception:
                pass
    conn.commit()
    conn.close()
    if max_updated:
        db_set_metadata("products_last_sync", max_updated.isoformat())
    logging.info("Products sync complete: %s products and %s variants saved/updated.", saved_products, saved_variants)
    return saved_products

def fetch_and_store_customers(incremental=True):
    """Fetch customers from Shopify"""
    logging.info("Starting customers sync (incremental=%s)", incremental)
    last_sync = db_get_metadata("customers_last_sync")
    params = {"limit": 250}
    if incremental and last_sync:
        last_dt = datetime.fromisoformat(last_sync)
        last_dt = last_dt - timedelta(seconds=60)
        params["updated_at_min"] = isoformat_for_api(last_dt)
    items = fetch_all_rest("customers.json", params=params, item_key="customers")
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    saved = 0
    max_updated = None
    for c in items:
        saved += 1
        cid = c["id"]
        updated_at = c.get("updated_at")
        cur.execute("""
        INSERT OR REPLACE INTO customers (id, first_name, last_name, email, phone, created_at, updated_at, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cid,
            c.get("first_name"),
            c.get("last_name"),
            c.get("email"),
            c.get("phone"),
            c.get("created_at"),
            updated_at,
            json.dumps(c)
        ))
        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                if not max_updated or dt > max_updated:
                    max_updated = dt
            except Exception:
                pass
    conn.commit()
    conn.close()
    if max_updated:
        db_set_metadata("customers_last_sync", max_updated.isoformat())
    logging.info("Customers sync complete: %s items saved/updated.", saved)
    return saved

def fetch_and_store_orders(incremental=True, status="any"):
    """Fetch orders from Shopify and extract line items"""
    logging.info("Starting orders sync (incremental=%s)", incremental)
    last_sync = db_get_metadata("orders_last_sync")
    params = {"limit": 250, "status": status}
    if incremental and last_sync:
        last_dt = datetime.fromisoformat(last_sync)
        last_dt = last_dt - timedelta(seconds=60)
        params["updated_at_min"] = isoformat_for_api(last_dt)
    items = fetch_all_rest("orders.json", params=params, item_key="orders")
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    saved_orders = 0
    saved_line_items = 0
    max_updated = None
    for o in items:
        saved_orders += 1
        oid = o["id"]
        updated_at = o.get("updated_at")
        # Extract customer_id if customer object exists
        customer_id = None
        customer = o.get("customer")
        if customer:
            customer_id = customer.get("id")
        total_price = None
        try:
            total_price = float(o.get("total_price", 0.0))
        except Exception:
            total_price = None
        # Store order with customer_id (FK)
        cur.execute("""
        INSERT OR REPLACE INTO orders
        (id, order_number, customer_id, email, total_price, currency, created_at, updated_at, financial_status, fulfillment_status, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            oid,
            o.get("order_number"),
            customer_id,
            o.get("email"),
            total_price,
            o.get("currency"),
            o.get("created_at"),
            updated_at,
            o.get("financial_status"),
            o.get("fulfillment_status"),
            json.dumps(o)
        ))
        # Extract and store line items (each line item has product_id and variant_id)
        line_items = o.get("line_items", [])
        for li in line_items:
            saved_line_items += 1
            li_id = li.get("id")
            product_id = li.get("product_id")
            variant_id = li.get("variant_id")
            quantity = li.get("quantity", 0)
            try:
                price = float(li.get("price", 0.0))
            except Exception:
                price = None
            cur.execute("""
            INSERT OR REPLACE INTO line_items
            (id, order_id, product_id, variant_id, title, quantity, price, sku, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                li_id,
                oid,
                product_id,
                variant_id,
                li.get("title"),
                quantity,
                price,
                li.get("sku"),
                json.dumps(li)
            ))
        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                if not max_updated or dt > max_updated:
                    max_updated = dt
            except Exception:
                pass
    conn.commit()
    conn.close()
    if max_updated:
        db_set_metadata("orders_last_sync", max_updated.isoformat())
    logging.info("Orders sync complete: %s orders and %s line items saved/updated.", saved_orders, saved_line_items)
    return saved_orders

# -------------- CSV Export functions (normalized for Power BI) --------------

def export_products_to_csv():
    """Export products from database to CSV"""
    try:
        conn = sqlite3.connect(DB_FILE)
        products_df = pd.read_sql_query(
            "SELECT id, title, vendor, product_type, created_at, updated_at FROM products",
            conn
        )
        conn.close()
        if not products_df.empty:
            products_df = products_df.fillna("")
            products_df.to_csv(CSV_PRODUCTS, index=False)
            logging.info("Products exported to %s (%s rows)", CSV_PRODUCTS, len(products_df))
        else:
            logging.info("No products to export")
    except Exception as e:
        logging.exception("Error exporting products to CSV: %s", e)

def export_product_variants_to_csv():
    """Export product variants from database to CSV"""
    try:
        conn = sqlite3.connect(DB_FILE)
        variants_df = pd.read_sql_query(
            """SELECT id as variant_id, product_id, title, sku, price, compare_at_price,
            position, option1, option2, option3, created_at, updated_at
            FROM product_variants""",
            conn
        )
        conn.close()
        if not variants_df.empty:
            variants_df = variants_df.fillna("")
            variants_df.to_csv(CSV_PRODUCT_VARIANTS, index=False)
            logging.info("Product variants exported to %s (%s rows)", CSV_PRODUCT_VARIANTS, len(variants_df))
        else:
            logging.info("No product variants to export")
    except Exception as e:
        logging.exception("Error exporting product variants to CSV: %s", e)

def export_customers_to_csv():
    """Export customers from database to CSV"""
    try:
        conn = sqlite3.connect(DB_FILE)
        customers_df = pd.read_sql_query(
            "SELECT id as customer_id, first_name, last_name, email, phone, created_at, updated_at FROM customers",
            conn
        )
        conn.close()
        if not customers_df.empty:
            customers_df = customers_df.fillna("")
            customers_df.to_csv(CSV_CUSTOMERS, index=False)
            logging.info("Customers exported to %s (%s rows)", CSV_CUSTOMERS, len(customers_df))
        else:
            logging.info("No customers to export")
    except Exception as e:
        logging.exception("Error exporting customers to CSV: %s", e)

def export_orders_to_csv():
    """Export orders from database to CSV with customer_id FK"""
    try:
        conn = sqlite3.connect(DB_FILE)
        orders_df = pd.read_sql_query(
            """SELECT id as order_id, order_number, customer_id, email, total_price, currency,
            created_at, updated_at, financial_status, fulfillment_status
            FROM orders""",
            conn
        )
        conn.close()
        if not orders_df.empty:
            orders_df = orders_df.fillna("")
            orders_df.to_csv(CSV_ORDERS, index=False)
            logging.info("Orders exported to %s (%s rows)", CSV_ORDERS, len(orders_df))
        else:
            logging.info("No orders to export")
    except Exception as e:
        logging.exception("Error exporting orders to CSV: %s", e)

def export_line_items_to_csv():
    """Export line items from database to CSV with order_id and product_id FKs"""
    try:
        conn = sqlite3.connect(DB_FILE)
        line_items_df = pd.read_sql_query(
            """SELECT id as line_item_id, order_id, product_id, variant_id, title, quantity,
            price, sku FROM line_items""",
            conn
        )
        conn.close()
        if not line_items_df.empty:
            line_items_df = line_items_df.fillna("")
            line_items_df.to_csv(CSV_LINE_ITEMS, index=False)
            logging.info("Line items exported to %s (%s rows)", CSV_LINE_ITEMS, len(line_items_df))
        else:
            logging.info("No line items to export")
    except Exception as e:
        logging.exception("Error exporting line items to CSV: %s", e)

# -------------- Analytics functions --------------

def analytics_reports():
    """Generate analytics reports from synced data"""
    conn = sqlite3.connect(DB_FILE)
    # Fetch orders data
    orders_df = pd.read_sql_query(
        "SELECT id, order_number, customer_id, total_price, currency, created_at FROM orders",
        conn
    )
    if orders_df.empty:
        logging.info("No orders in DB to analyze.")
        conn.close()
        return
    # Convert data types
    orders_df["created_at"] = pd.to_datetime(orders_df["created_at"])
    orders_df["total_price"] = pd.to_numeric(orders_df["total_price"], errors="coerce").fillna(0.0)
    # 1) Sales by day
    sales_by_day = orders_df.groupby(orders_df["created_at"].dt.date)["total_price"].sum().reset_index()
    sales_by_day.columns = ["date", "total_sales"]
    # 2) Average order value (AOV)
    aov = orders_df["total_price"].mean()
    # 3) Line items analysis
    line_items_df = pd.read_sql_query(
        "SELECT order_id, product_id, quantity, price FROM line_items",
        conn
    )
    if not line_items_df.empty:
        top_products = line_items_df.groupby("product_id")["quantity"].sum().reset_index().sort_values("quantity", ascending=False).head(10)
    else:
        top_products = pd.DataFrame()
    # 4) Repeat customer rate
    cust_orders = orders_df.groupby("customer_id")["order_number"].nunique().reset_index()
    cust_orders.columns = ["customer_id", "num_orders"]
    repeat_customers = cust_orders[cust_orders["num_orders"] > 1].shape[0]
    total_customers = cust_orders.shape[0]
    repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0.0
    # Print summary
    logging.info("Analytics Summary:")
    logging.info("Total orders: %s", orders_df.shape[0])
    logging.info("Total sales (sum): %s", orders_df["total_price"].sum())
    logging.info("AOV: %s", round(aov, 2) if pd.notna(aov) else 0.0)
    logging.info("Repeat customer rate: %s%% (%s/%s)", round(repeat_rate, 2), repeat_customers, total_customers)
    # Save summary
    summary = {
        "total_orders": int(orders_df.shape[0]),
        "total_sales": float(orders_df["total_price"].sum()),
        "aov": float(aov) if pd.notna(aov) else None,
        "repeat_rate_percent": float(round(repeat_rate, 4))
    }
    summary_file = DATA_DIR / "analytics_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    conn.close()
    logging.info("Analytics reports saved")

# -------------- Orchestration --------------

def run_full_sync(incremental=True, push_to_sheets=True):
    """Run complete sync: fetch data, store in DB, export to CSV, push to sheets"""
    init_db()
    # Fetch and store data
    p = fetch_and_store_products(incremental=incremental)
    c = fetch_and_store_customers(incremental=incremental)
    o = fetch_and_store_orders(incremental=incremental)
    # Export to CSV files (normalized)
    export_products_to_csv()
    export_product_variants_to_csv()
    export_customers_to_csv()
    export_orders_to_csv()
    export_line_items_to_csv()
    # Generate analytics
    analytics_reports()
    # Push to Google Sheets
    if push_to_sheets:
        gc = init_google_sheets()
        if gc:
            sync_all_data_to_sheets(gc, GOOGLE_SHEET_ID)
        else:
            logging.warning("Google Sheets sync skipped - client initialization failed")
    logging.info("Full sync finished. Products=%s, Customers=%s, Orders=%s", p, c, o)

# -------------- CLI and Scheduler --------------

def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true", help="Run scheduler daemon (every 10 minutes)")
    parser.add_argument("--full", action="store_true", help="Force full (non-incremental) sync")
    parser.add_argument("--once", action="store_true", help="Run one sync and exit (default)")
    parser.add_argument("--no-sheets", action="store_true", help="Disable Google Sheets sync")
    args = parser.parse_args()
    if not SHOPIFY_STORE or not SHOPIFY_API_TOKEN:
        logging.error("Please set SHOPIFY_STORE and SHOPIFY_API_TOKEN in your .env file at %s", ENV_FILE)
        return
    logging.info("Using .env file from: %s", ENV_FILE)
    logging.info("Using database at: %s", DB_FILE)
    logging.info("Using data directory: %s", DATA_DIR)
    if not GOOGLE_SHEET_ID:
        logging.warning("GOOGLE_SHEET_ID not set in .env file. Google Sheets sync will be disabled.")
    if args.daemon:
        scheduler = BlockingScheduler()
        scheduler.add_job(
            lambda: run_full_sync(incremental=not args.full, push_to_sheets=not args.no_sheets),
            "interval",
            minutes=10
        )
        logging.info("Starting scheduler. Running sync every 10 minutes. First run now.")
        run_full_sync(incremental=not args.full, push_to_sheets=not args.no_sheets)
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logging.info("Scheduler stopped by user.")
    else:
        # Single run
        run_full_sync(incremental=not args.full, push_to_sheets=not args.no_sheets)

if __name__ == "__main__":
    main()
