"""
sync.py

Sync module that handles fetching and storing Shopify data (products, customers, orders)
into the SQLite database.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta, timezone
from config import DB_FILE
from database import db_set_metadata, db_get_metadata
from shopify_api import fetch_all_rest

logger = logging.getLogger("update_shopify_history_database_logger")


def isoformat_for_api(dt: datetime):
    """Convert datetime to Shopify API ISO 8601 format"""
    return dt.astimezone(timezone.utc).replace(tzinfo=None).isoformat() + "Z"


def fetch_and_store_products(incremental=True):
    """Fetch products and product variants from Shopify"""
    logger.info(f"Starting products sync (incremental={incremental})")

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

    logger.info(f"Products sync complete: {saved_products} products and {saved_variants} variants saved/updated.")
    return saved_products


def fetch_and_store_customers(incremental=True):
    """Fetch customers from Shopify"""
    logger.info(f"Starting customers sync (incremental={incremental})")

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

    logger.info(f"Customers sync complete: {saved} items saved/updated.")
    return saved


def fetch_and_store_orders(incremental=True, status="any"):
    """Fetch orders from Shopify and extract line items"""
    logger.info(f"Starting orders sync (incremental={incremental})")

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

    logger.info(f"Orders sync complete: {saved_orders} orders and {saved_line_items} line items saved/updated.")
    return saved_orders
