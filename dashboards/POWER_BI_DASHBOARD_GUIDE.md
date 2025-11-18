# Power BI Dashboard - Shopify Order Analytics

## Overview

The **Shopify Order Dashboard** is a comprehensive Power BI workbook that provides real-time insights into e-commerce order flow, sales patterns, customer behavior, and fulfillment metrics.

**Connection:** Google Sheets (Auto-Refreshed) ← SQLite ← Shopify API

## Dashboard Pages

### 1. Overview Page

**Purpose:** Executive summary of key business metrics and trends

**KPI Cards:**
- **Total Orders:** 120 orders
- **Total Customers:** 38 unique customers
- **Average Order Value (AOV):** $340.95
- **Processing Time (Days):** 0.99 days

**Financial Metrics:**
- **Total Sales:** $40.91K
- **Total Discounts:** $3.26K
- **Total Tax:** $3.72K
- **Outstanding Amount:** $25.94K

**Visualizations:**

**1. Sales & Order Value Chart (Combo Chart)**
- **Type:** Column + Line combination chart
- **Time Period:** June 2024 - November 2024 (~6 months)
- **Yellow Bars:** Total daily sales
  - Range: $0 - $1,000+ per day
  - Shows sales volatility and patterns
  - Peaks indicate high-sales days
- **Purple Line:** Average Order Value trend
  - Shows AOV trend over time
  - Helps identify pricing changes or customer segment shifts
  - Range: $0 - $600

**2. Customer & Orders Chart (Stacked + Line Chart)**
- **Type:** Stacked column + line combination
- **Blue Bars (Stacked):** Number of orders per day
  - Shows order frequency
  - Multiple orders per day visible
- **Green Line:** Number of customers per day
  - Shows customer acquisition/activity
  - Helps identify busy periods

**Insights Available:**
- Day-over-day sales variability
- Order value consistency
- Customer engagement patterns
- Peak sales periods
- Seasonal trends

---

### 2. Geographic Overview Page

**Purpose:** Analyze order distribution and sales performance by geographic location

**Potential Visualizations:**
- Map visualization showing order locations
- Sales by country/region breakdown
- Customer distribution by geography
- Top performing regions
- Regional average order value

**Data Sources:**
- `orders.csv` - Order location data (if available in Shopify)
- `customers.csv` - Customer geographic information

**Key Metrics:**
- Orders by location
- Sales per region
- Customer count by country
- Regional AOV comparison
- Geographic expansion trends

**Filtering:**
- Date range filter
- Region/country filter
- Customer segment filter

---

### 3. Orders & Customers Page

**Purpose:** Deep dive into order details and customer analytics

**Order Analysis Section:**
- Total orders by status (pending, processing, fulfilled, cancelled)
- Order trends over time
- Order value distribution (histogram)
- Top order values
- Average days to fulfillment

**Customer Analysis Section:**
- Total unique customers
- New vs. repeat customers breakdown
- Customer acquisition timeline
- Repeat purchase rate and frequency
- Customer lifecycle analysis
- Customer segmentation by spending

**Visualizations:**
- Order status breakdown (pie/donut chart)
- Customer lifetime value (histogram)
- Orders per customer (distribution)
- New customer acquisition trend (line chart)
- Repeat purchase cohort analysis (heat map)

**Key Metrics:**
- Total unique customers: 38
- Repeat customer percentage
- Average orders per customer
- Customer acquisition cost (if cost data available)
- Customer retention rate

**Filtering:**
- Date range
- Order status
- Customer type (new/repeat)
- Order value range

---

### 4. Coherent Analysis Page

**Purpose:** Integrated view of all key metrics and deeper business insights

**Dashboard Components:**

**A. KPI Summary Section**
- Total orders
- Total revenue
- Total customers
- AOV
- Processing time
- Repeat rate
- Fulfillment rate

**B. Trend Analysis**
- Sales trend (30/60/90 days)
- Customer acquisition trend
- Order frequency trend
- AOV trend over time

**C. Correlation Analysis**
- Order value vs. order quantity
- Customer lifetime value vs. purchase frequency
- Fulfillment time vs. customer retention (if available)
- Geographic location vs. AOV

**D. Product Performance**
- Top 10 products by quantity sold
- Top 10 products by revenue
- Product performance trend
- Product-customer affinity analysis

**E. Operational Metrics**
- Average fulfillment time
- Order processing efficiency
- Discount impact analysis
- Tax and shipping analysis

**F. Year-over-Year (if data available)**
- Monthly sales comparison
- Order volume comparison
- Customer metrics YoY

**Visualizations:**
- KPI cards (summary)
- Trend lines (multiple metrics)
- Scatter plots (correlation)
- Bar charts (performance)
- Heat maps (patterns)
- Gauge charts (efficiency)

**Advanced Features:**
- Drill-through capabilities
- Cross-filtering between visuals
- Bookmarks for saved views
- Custom filters and slicers

---

## Data Model

### Tables and Relationships

```
products (Product Dimension)
├─ product_id (PK)
├─ title
├─ vendor
├─ product_type
├─ created_at
└─ updated_at

    ↓ (1:N)

product_variants (Product Variant)
├─ variant_id (PK)
├─ product_id (FK)
├─ title
├─ sku
├─ price
├─ compare_at_price
├─ position
└─ created_at

customers (Customer Dimension)
├─ customer_id (PK)
├─ first_name
├─ last_name
├─ email
├─ phone
├─ created_at
└─ updated_at

    ↓ (1:N)

orders (Order Fact)
├─ order_id (PK)
├─ order_number
├─ customer_id (FK)
├─ email
├─ total_price
├─ currency
├─ created_at
├─ updated_at
├─ financial_status
└─ fulfillment_status

    ↓ (1:N)

line_items (Order Line Items)
├─ line_item_id (PK)
├─ order_id (FK)
├─ product_id (FK)
├─ variant_id (FK)
├─ title
├─ quantity
├─ price
└─ sku
```

### Key Measures (DAX Calculated)

```DAX
# Total Orders
Total Orders = COUNTA(orders[order_id])

# Total Sales
Total Sales = SUM(orders[total_price])

# Average Order Value
AOV = DIVIDE(
    SUM(orders[total_price]),
    COUNTA(orders[order_id])
)

# Unique Customers
Unique Customers = DISTINCTCOUNT(customers[customer_id])

# Processing Time (Days)
Processing Time = AVERAGE(
    DATEDIFF(orders[created_at], orders[updated_at], DAY)
)

# Repeat Customer Rate
Repeat Rate = DIVIDE(
    COUNTROWS(
        FILTER(
            VALUES(customers[customer_id]),
            COUNTA(RELATEDTABLE(orders)) > 1
        )
    ),
    DISTINCTCOUNT(customers[customer_id])
)

# Month-over-Month Growth
MoM Growth = DIVIDE(
    [This Month Sales] - [Last Month Sales],
    [Last Month Sales]
)
```

---

## Connection & Refresh Strategy

### Data Connection Flow

```
Step 1: SQLite Database (scripts/)
        └─ Runs every 10 minutes (daemon mode)
        └─ Updates shopify_data.db with latest data

Step 2: CSV Export (scripts/csv_export.py)
        └─ Exports 5 normalized CSV files
        └─ Files saved to data/ folder

Step 3: Google Sheets Sync (scripts/google_sheets.py)
        └─ Pushes CSVs to Google Sheets
        └─ Creates/updates worksheets
        └─ Full data refresh (clear + rewrite)

Step 4: Power BI Connection
        └─ Power BI connected to Google Sheets
        └─ Scheduled refresh in Power BI Service

Step 5: Dashboard Display
        └─ Automatic dashboard refresh
        └─ Real-time insights available
```

### Refresh Configuration

**Pipeline Execution:** Every 10 minutes
- Shopify API → SQLite
- SQLite → CSV
- CSV → Google Sheets
- Google Sheets → Power BI (scheduled refresh)

**Power BI Service Refresh:** Configurable
- Recommended: Every 15-30 minutes (aligned with pipeline)
- Can be set to hourly or more frequent
- Set in Power BI Service → Settings → Scheduled refresh

**Manual Refresh:**
1. In Power BI Desktop: Ctrl + R
2. In Power BI Service: Click refresh icon
3. Check last refresh timestamp on dashboard

---

## Using the Dashboard

### Navigation

**Tabs/Pages:** Click page tabs at bottom to switch between pages
- Overview
- Geographic Overview
- Orders & Customers
- Coherent Analysis

### Filtering

**Slicers (Top of pages):**
- Date range picker
- Customer segment
- Order status
- Geographic region (on Geographic Overview page)

**Cross-Filtering:**
- Click on a bar/element to filter all related visuals
- Click again to clear filter

### Drilling:**
- Some visuals support drill-down
- Double-click to drill deeper
- Breadcrumb appears at top

### Bookmarks:**
- Saved views for quick navigation
- Click bookmark button to save current view
- Load bookmarks from Bookmarks pane

---

## Key Performance Indicators (KPIs)

| KPI | Current Value | Target | Status |
|-----|---|---|---|
| Total Orders | 120 | 150+ | Monitor |
| Total Customers | 38 | 50+ | Growing |
| Average Order Value | $340.95 | $350+ | Close |
| Processing Time | 0.99 days | <1 day | Good |
| Total Sales | $40.91K | $50K+ | Strong |
| Repeat Rate | % | >20% | Track |

---

## Common Questions & Answers

**Q: Why is the dashboard showing old data?**
A: Check Power BI Service refresh schedule. If pipeline hasn't run, manual refresh won't help. Verify Google Sheets has latest data first.

**Q: How do I add a new metric to the dashboard?**
A: Edit the Power BI file (.pbix), add a new visual, connect to relevant table columns, and save.

**Q: Can I share the dashboard with others?**
A: Yes! Publish to Power BI Service and share the workspace/app with team members.

**Q: How do I drill down on a specific metric?**
A: Click on a bar/data point to filter. Some visuals support drill-down (double-click). Use slicers at top to filter by date, customer, status, etc.

**Q: What if a table is missing data?**
A: Check pipeline logs in `logs/` folder. Verify Google Sheets has the worksheet. Try manual refresh in Power BI.

---

## Dashboard Screenshots

**Overview Page Preview:** See `screenshots/overview_preview.jpg`
- Shows KPI cards and sales/customer charts
- 6-month trend visualization
- Key metrics at a glance

**Geographic Overview:** See `screenshots/geographic_overview.jpg`
- Map visualization
- Regional sales breakdown
- Customer distribution

**Orders & Customers:** See `screenshots/orders_customers.jpg`
- Order details and status
- Customer analytics
- Repeat purchase analysis

**Coherent Analysis:** See `screenshots/coherent_analysis.jpg`
- Integrated KPIs
- Correlation analysis
- Performance metrics

---

## Troubleshooting

### Issue: "No data showing"
**Solution:**
1. Verify Google Sheets has data (check worksheets)
2. Check pipeline logs for errors
3. Try manual refresh in Power BI
4. Reconnect to data source if needed

### Issue: "Filters not working"
**Solution:**
1. Clear all filters (click X on slicers)
2. Refresh page (F5)
3. Check data relationships in model view

### Issue: "Dashboard is slow"
**Solution:**
1. Reduce date range filter
2. Pre-filter data in queries
3. Optimize visuals (fewer data points)
4. Check internet connection to Google Sheets

### Issue: "Refresh fails in Power BI Service"
**Solution:**
1. Verify Google Sheets is still accessible
2. Check service account credentials are valid
3. Re-authorize data source connection
4. Restart Power BI Service gateway if using on-premises

---

## Advanced Configuration

### Custom Measures (DAX)

Add custom calculations to analyze specific scenarios:

```DAX
# Example: High-Value Orders
High Value Orders = CALCULATE(
    COUNTA(orders[order_id]),
    FILTER(orders, orders[total_price] > 500)
)

# Example: Last 30-Day Sales
L30D Sales = CALCULATE(
    SUM(orders[total_price]),
    DATESBETWEEN(orders[created_at], TODAY()-30, TODAY())
)
```

### Custom Columns

Add columns to enhance analysis:

```DAX
# Order Size Category
Order Size = 
    IF(orders[total_price] > 500, "Large",
    IF(orders[total_price] > 200, "Medium",
    "Small"))

# Days to Fulfill
Fulfillment Days = DATEDIFF(orders[created_at], orders[updated_at], DAY)
```

---

## Exporting Reports

**From Power BI Desktop:**
1. File → Export as PDF/PowerPoint
2. Select specific pages or all pages
3. Configure export settings
4. Choose location and save

**From Power BI Service:**
1. Click ellipsis (...) on visual
2. Select "Export data" or "Export this visual as image"
3. Download file

---

## Performance Tips

1. **Filter by date range** - Reduces data volume
2. **Use aggregations** - Pre-aggregated data loads faster
3. **Limit visuals** - Too many visuals slow down dashboard
4. **Archive old data** - Move old records out of main tables
5. **Optimize queries** - Use folding where possible
6. **Use DirectQuery sparingly** - Import mode is faster for static data

---

## Security & Sharing

**Data Security:**
- Google Sheets access controlled by service account
- Power BI Service has row-level security (RLS) available
- Sensitive data can be masked in Power BI

**Sharing:**
- Publish dashboard to Power BI Service
- Share workspace with team members
- Create app for broader distribution
- Set refresh schedule for service

**Audit:**
- Power BI tracks access logs
- Google Sheets has version history
- Pipeline logs available in `logs/` folder

---

## Next Steps

1. ✅ Verify pipeline is running (`main.py --daemon`)
2. ✅ Check Google Sheets has data
3. ✅ Open Power BI Desktop file
4. ✅ Configure refresh schedule in Power BI Service
5. ✅ Share dashboard with team
6. ✅ Set up alerts for key metrics (optional)
7. ✅ Create custom bookmarks for common views

---

**Dashboard Version:** 2.0  
**Last Updated:** 2025-11-18  
**Data Source:** Shopify via SQLite → Google Sheets → Power BI  
**Refresh Frequency:** Every 10 minutes (pipeline) + Power BI schedule
