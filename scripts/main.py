"""
main.py

Main module that orchestrates the entire Shopify sync pipeline.
Handles full sync execution and scheduling using APScheduler.

Usage:
    python main.py --once                    # Run one sync and exit (default)
    python main.py --daemon                  # Run scheduler daemon (every 10 minutes)
    python main.py --full                    # Force full (non-incremental) sync
    python main.py --no-sheets               # Disable Google Sheets sync
    python main.py --daemon --full           # Daemon mode with full sync each time
"""

import argparse
import logging
from apscheduler.schedulers.blocking import BlockingScheduler

# Import logger configuration
from logger_config import logger

# Import all modules
from config import SHOPIFY_STORE, SHOPIFY_API_TOKEN, GOOGLE_SHEET_ID, ENV_FILE, DB_FILE, DATA_DIR
from database import init_db
from sync import fetch_and_store_products, fetch_and_store_customers, fetch_and_store_orders
from csv_export import export_all_to_csv
from analytics import analytics_reports
from google_sheets import init_google_sheets, sync_all_data_to_sheets


def run_full_sync(incremental=True, push_to_sheets=True):
    """
    Run complete sync: fetch data, store in DB, export to CSV, push to sheets
    
    Args:
        incremental (bool): If True, only fetch updated data since last sync
        push_to_sheets (bool): If True, push data to Google Sheets
    """
    logger.info("=" * 80)
    logger.info("STARTING FULL SYNC PIPELINE")
    logger.info("=" * 80)
    
    try:
        # Initialize database
        logger.info("Step 1/6: Initializing database...")
        init_db()
        logger.info("✓ Database initialized")

        # Fetch and store data
        logger.info("Step 2/6: Fetching and storing products...")
        products_count = fetch_and_store_products(incremental=incremental)
        logger.info(f"✓ Products fetched: {products_count}")

        logger.info("Step 3/6: Fetching and storing customers...")
        customers_count = fetch_and_store_customers(incremental=incremental)
        logger.info(f"✓ Customers fetched: {customers_count}")

        logger.info("Step 4/6: Fetching and storing orders...")
        orders_count = fetch_and_store_orders(incremental=incremental)
        logger.info(f"✓ Orders fetched: {orders_count}")

        # Export to CSV files (normalized)
        logger.info("Step 5/6: Exporting data to CSV files...")
        export_all_to_csv()
        logger.info("✓ CSV export complete")

        # Generate analytics
        logger.info("Step 6/6: Generating analytics reports...")
        analytics_reports()
        logger.info("✓ Analytics reports generated")

        # Push to Google Sheets
        if push_to_sheets:
            logger.info("Pushing data to Google Sheets...")
            gc = init_google_sheets()
            if gc:
                sync_all_data_to_sheets(gc, GOOGLE_SHEET_ID)
                logger.info("✓ Google Sheets sync complete")
            else:
                logger.warning("⚠ Google Sheets sync skipped - client initialization failed")
        else:
            logger.info("⊘ Google Sheets sync disabled")

        logger.info("=" * 80)
        logger.info(f"FULL SYNC COMPLETE - Products: {products_count}, Customers: {customers_count}, Orders: {orders_count}")
        logger.info("=" * 80)

    except Exception as e:
        logger.exception(f"ERROR during full sync: {e}")
        raise


def validate_configuration():
    """Validate that all required environment variables are set"""
    logger.info("Validating configuration...")
    
    if not SHOPIFY_STORE or not SHOPIFY_API_TOKEN:
        logger.error(f"ERROR: Please set SHOPIFY_STORE and SHOPIFY_API_TOKEN in your .env file at {ENV_FILE}")
        return False

    logger.info(f"✓ Shopify configuration valid")
    logger.info(f"  - Using .env file from: {ENV_FILE}")
    logger.info(f"  - Using database at: {DB_FILE}")
    logger.info(f"  - Using data directory: {DATA_DIR}")

    if not GOOGLE_SHEET_ID:
        logger.warning(f"⚠ GOOGLE_SHEET_ID not set in .env file. Google Sheets sync will be disabled.")

    return True


def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Shopify Sync Pipeline - Fetch, store, and export Shopify data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py --once                    # Run one sync and exit (default)
    python main.py --daemon                  # Run scheduler daemon (every 10 minutes)
    python main.py --full                    # Force full (non-incremental) sync
    python main.py --no-sheets               # Disable Google Sheets sync
    python main.py --daemon --full           # Daemon mode with full sync each time
        """
    )

    parser.add_argument("--daemon", action="store_true", help="Run scheduler daemon (every 10 minutes)")
    parser.add_argument("--full", action="store_true", help="Force full (non-incremental) sync")
    parser.add_argument("--once", action="store_true", help="Run one sync and exit (default)")
    parser.add_argument("--no-sheets", action="store_true", help="Disable Google Sheets sync")

    args = parser.parse_args()

    # Validate configuration
    if not validate_configuration():
        return

    # Determine mode
    incremental = not args.full
    push_to_sheets = not args.no_sheets

    if args.daemon:
        logger.info("Starting scheduler in DAEMON mode...")
        logger.info("Running sync every 10 minutes. Press Ctrl+C to stop.")
        
        scheduler = BlockingScheduler()
        scheduler.add_job(
            lambda: run_full_sync(incremental=incremental, push_to_sheets=push_to_sheets),
            "interval",
            minutes=10
        )

        logger.info("First sync run starting now...")
        run_full_sync(incremental=incremental, push_to_sheets=push_to_sheets)

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped by user.")

    else:
        # Single run mode (default)
        logger.info("Running in SINGLE RUN mode...")
        run_full_sync(incremental=incremental, push_to_sheets=push_to_sheets)
        logger.info("Single run complete. Exiting.")


if __name__ == "__main__":
    main()
