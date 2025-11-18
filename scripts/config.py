"""
config.py

Configuration module that loads environment variables and sets up paths,
database connections, and API constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Directory setup
SCRIPT_DIR = Path(__file__).parent  # scripts folder
PROJECT_DIR = SCRIPT_DIR.parent  # Real-Time-E-Commerce-Analytics-Platform
DATA_DIR = PROJECT_DIR / "data"
ENV_FILE = PROJECT_DIR / ".env"
GSPREAD_CREDENTIALS_FILE = PROJECT_DIR / "gspread_credentials.json"

# Create data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)

# Load environment variables from parent directory
load_dotenv(ENV_FILE)

# Shopify API Configuration
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")  # e.g., "quantum-spectra-store"
SHOPIFY_API_TOKEN = os.getenv("SHOPIFY_API_TOKEN")
API_VERSION = "2024-10"
BASE_URL = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/{API_VERSION}/"

# Database Configuration
DB_FILE = DATA_DIR / "shopify_data.db"

# CSV Export Paths
CSV_CUSTOMERS = DATA_DIR / "customers.csv"
CSV_ORDERS = DATA_DIR / "orders.csv"
CSV_LINE_ITEMS = DATA_DIR / "line_items.csv"
CSV_PRODUCT_VARIANTS = DATA_DIR / "product_variants.csv"
CSV_PRODUCTS = DATA_DIR / "products.csv"

# Google Sheets Configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")  # Load from .env

# Request Session Configuration
REQUESTS_HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_API_TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json",
}
