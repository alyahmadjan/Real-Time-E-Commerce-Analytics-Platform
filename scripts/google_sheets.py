"""
google_sheets.py

Google Sheets module that handles authentication and pushing data to Google Sheets.
"""

import logging
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from config import SCOPES, GSPREAD_CREDENTIALS_FILE, GOOGLE_SHEET_ID, CSV_PRODUCTS, CSV_PRODUCT_VARIANTS, CSV_CUSTOMERS, CSV_ORDERS, CSV_LINE_ITEMS

logger = logging.getLogger("update_shopify_history_database_logger")


def init_google_sheets():
    """Initialize and return authorized gspread client"""
    try:
        if not GSPREAD_CREDENTIALS_FILE.exists():
            logger.error(f"Google credentials file not found at: {GSPREAD_CREDENTIALS_FILE}")
            return None

        credentials = Credentials.from_service_account_file(
            GSPREAD_CREDENTIALS_FILE,
            scopes=SCOPES
        )

        gc = gspread.authorize(credentials)
        logger.info("Google Sheets client initialized successfully")
        return gc

    except Exception as e:
        logger.exception(f"Failed to initialize Google Sheets client: {e}")
        return None


def get_or_create_worksheet(gc, sheet_id, worksheet_name):
    """Get existing worksheet or create new one"""
    try:
        if not sheet_id:
            logger.error("GOOGLE_SHEET_ID not set in .env file")
            return None

        spreadsheet = gc.open_by_key(sheet_id)

        # Try to find existing worksheet
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            logger.info(f"Using existing worksheet: {worksheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            # Create new worksheet if it doesn't exist
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1, cols=1)
            logger.info(f"Created new worksheet: {worksheet_name}")

        return worksheet

    except Exception as e:
        logger.exception(f"Error accessing/creating worksheet '{worksheet_name}': {e}")
        return None


def push_dataframe_to_sheet(gc, sheet_id, dataframe, worksheet_name):
    """Push a pandas DataFrame to a Google Sheet"""
    try:
        if dataframe.empty:
            logger.warning(f"DataFrame is empty, skipping push to {worksheet_name}")
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

        logger.info(f"Successfully pushed {len(dataframe)} rows to Google Sheet '{worksheet_name}'")
        return True

    except Exception as e:
        logger.exception(f"Error pushing data to Google Sheet '{worksheet_name}': {e}")
        return False


def sync_all_data_to_sheets(gc, sheet_id):
    """Sync all CSV data to Google Sheets"""
    if not gc or not sheet_id:
        logger.warning("Google Sheets client or Sheet ID not available, skipping sync")
        return False

    all_successful = True

    # Sync products
    if CSV_PRODUCTS.exists():
        try:
            products_df = pd.read_csv(CSV_PRODUCTS)
            if not push_dataframe_to_sheet(gc, sheet_id, products_df, "Products"):
                all_successful = False
        except Exception as e:
            logger.exception(f"Error reading/pushing products CSV: {e}")
            all_successful = False

    # Sync product variants
    if CSV_PRODUCT_VARIANTS.exists():
        try:
            variants_df = pd.read_csv(CSV_PRODUCT_VARIANTS)
            if not push_dataframe_to_sheet(gc, sheet_id, variants_df, "ProductVariants"):
                all_successful = False
        except Exception as e:
            logger.exception(f"Error reading/pushing product variants CSV: {e}")
            all_successful = False

    # Sync customers
    if CSV_CUSTOMERS.exists():
        try:
            customers_df = pd.read_csv(CSV_CUSTOMERS)
            if not push_dataframe_to_sheet(gc, sheet_id, customers_df, "Customers"):
                all_successful = False
        except Exception as e:
            logger.exception(f"Error reading/pushing customers CSV: {e}")
            all_successful = False

    # Sync orders
    if CSV_ORDERS.exists():
        try:
            orders_df = pd.read_csv(CSV_ORDERS)
            if not push_dataframe_to_sheet(gc, sheet_id, orders_df, "Orders"):
                all_successful = False
        except Exception as e:
            logger.exception(f"Error reading/pushing orders CSV: {e}")
            all_successful = False

    # Sync line items
    if CSV_LINE_ITEMS.exists():
        try:
            line_items_df = pd.read_csv(CSV_LINE_ITEMS)
            if not push_dataframe_to_sheet(gc, sheet_id, line_items_df, "LineItems"):
                all_successful = False
        except Exception as e:
            logger.exception(f"Error reading/pushing line items CSV: {e}")
            all_successful = False

    return all_successful
