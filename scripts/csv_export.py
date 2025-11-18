"""
csv_export.py

CSV export module that handles exporting data from SQLite to normalized CSV files
for Power BI integration.
"""

import sqlite3
import logging
import pandas as pd
from config import DB_FILE, CSV_CUSTOMERS, CSV_ORDERS, CSV_LINE_ITEMS, CSV_PRODUCT_VARIANTS, CSV_PRODUCTS

logger = logging.getLogger("update_shopify_history_database_logger")


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
            logger.info(f"Products exported to {CSV_PRODUCTS} ({len(products_df)} rows)")
        else:
            logger.info("No products to export")

    except Exception as e:
        logger.exception(f"Error exporting products to CSV: {e}")


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
            logger.info(f"Product variants exported to {CSV_PRODUCT_VARIANTS} ({len(variants_df)} rows)")
        else:
            logger.info("No product variants to export")

    except Exception as e:
        logger.exception(f"Error exporting product variants to CSV: {e}")


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
            logger.info(f"Customers exported to {CSV_CUSTOMERS} ({len(customers_df)} rows)")
        else:
            logger.info("No customers to export")

    except Exception as e:
        logger.exception(f"Error exporting customers to CSV: {e}")


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
            logger.info(f"Orders exported to {CSV_ORDERS} ({len(orders_df)} rows)")
        else:
            logger.info("No orders to export")

    except Exception as e:
        logger.exception(f"Error exporting orders to CSV: {e}")


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
            logger.info(f"Line items exported to {CSV_LINE_ITEMS} ({len(line_items_df)} rows)")
        else:
            logger.info("No line items to export")

    except Exception as e:
        logger.exception(f"Error exporting line items to CSV: {e}")


def export_all_to_csv():
    """Export all data to CSV files"""
    logger.info("Starting CSV export process...")
    export_products_to_csv()
    export_product_variants_to_csv()
    export_customers_to_csv()
    export_orders_to_csv()
    export_line_items_to_csv()
    logger.info("CSV export process complete")
