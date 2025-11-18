"""
analytics.py

Analytics module that generates analytics reports and summaries from synced data.
"""

import sqlite3
import json
import logging
import pandas as pd
from config import DB_FILE, DATA_DIR

logger = logging.getLogger("update_shopify_history_database_logger")


def analytics_reports():
    """Generate analytics reports from synced data"""
    conn = sqlite3.connect(DB_FILE)

    # Fetch orders data
    orders_df = pd.read_sql_query(
        "SELECT id, order_number, customer_id, total_price, currency, created_at FROM orders",
        conn
    )

    if orders_df.empty:
        logger.info("No orders in DB to analyze.")
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
        top_products = line_items_df.groupby("product_id")["quantity"].sum().reset_index().sort_values(
            "quantity", ascending=False
        ).head(10)
    else:
        top_products = pd.DataFrame()

    # 4) Repeat customer rate
    cust_orders = orders_df.groupby("customer_id")["order_number"].nunique().reset_index()
    cust_orders.columns = ["customer_id", "num_orders"]
    repeat_customers = cust_orders[cust_orders["num_orders"] > 1].shape[0]
    total_customers = cust_orders.shape[0]
    repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0.0

    # Print summary
    logger.info("Analytics Summary:")
    logger.info(f"Total orders: {orders_df.shape[0]}")
    logger.info(f"Total sales (sum): {orders_df['total_price'].sum()}")
    logger.info(f"AOV: {round(aov, 2) if pd.notna(aov) else 0.0}")
    logger.info(f"Repeat customer rate: {round(repeat_rate, 2)}% ({repeat_customers}/{total_customers})")

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

    logger.info("Analytics reports saved")
