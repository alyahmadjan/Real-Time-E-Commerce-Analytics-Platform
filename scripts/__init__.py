"""
__init__.py

Package initialization file for the scripts module.
Makes the scripts folder a Python package and allows imports from other modules.
"""

# Version
__version__ = "2.0"
__author__ = "Your Name"
__description__ = "Shopify Real-Time E-Commerce Analytics Pipeline"

# Import main components for easier access
try:
    from .logger_config import logger
    from .config import (
        SHOPIFY_STORE,
        SHOPIFY_API_TOKEN,
        BASE_URL,
        DB_FILE,
        DATA_DIR
    )
    from .database import init_db, db_get_metadata, db_set_metadata
    from .sync import (
        fetch_and_store_products,
        fetch_and_store_customers,
        fetch_and_store_orders
    )
    from .csv_export import export_all_to_csv
    from .analytics import analytics_reports
    from .google_sheets import init_google_sheets, sync_all_data_to_sheets
    from .shopify_api import fetch_all_rest, request_with_retries

    __all__ = [
        'logger',
        'SHOPIFY_STORE',
        'SHOPIFY_API_TOKEN',
        'BASE_URL',
        'DB_FILE',
        'DATA_DIR',
        'init_db',
        'db_get_metadata',
        'db_set_metadata',
        'fetch_and_store_products',
        'fetch_and_store_customers',
        'fetch_and_store_orders',
        'export_all_to_csv',
        'analytics_reports',
        'init_google_sheets',
        'sync_all_data_to_sheets',
        'fetch_all_rest',
        'request_with_retries'
    ]

except ImportError as e:
    print(f"Warning: Could not import all modules: {e}")
