import sqlite3
import pandas as pd

DB_FILE = "shopify_data.db"

# Connect to the database
conn = sqlite3.connect(DB_FILE)

# Example: list all tables
tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
print("Tables in DB:")
print(tables)

# Example: peek at first 5 products
products = pd.read_sql_query("SELECT * FROM products LIMIT 5;", conn)
print("\nFirst 5 products:")
print(products)

# Example: peek at first 5 orders
orders = pd.read_sql_query("SELECT * FROM orders LIMIT 5;", conn)
print("\nFirst 5 orders:")
print(orders)

# Example: peek at first 5 customers
customers = pd.read_sql_query("SELECT * FROM customers LIMIT 5;", conn)
print("\nFirst 5 customers:")
print(customers)

conn.close()
