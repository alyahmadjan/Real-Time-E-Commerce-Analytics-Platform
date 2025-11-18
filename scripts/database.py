"""
database.py

Database module that handles SQLite initialization, schema management,
and metadata operations.
"""

import sqlite3
import json
import logging
from config import DB_FILE

logger = logging.getLogger("update_shopify_history_database_logger")


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
            logger.info(f"Added column {column_name} to table {table_name}")
            return True
        except Exception as e:
            logger.warning(f"Could not add column {column_name} to {table_name}: {e}")
            return False
    return True


def migrate_schema(conn):
    """Migrate database schema for backward compatibility"""
    logger.info("Running schema migration checks...")

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

    logger.info("Schema migration complete")


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
