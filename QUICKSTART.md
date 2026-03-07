# 🚀 Quick Start Guide - Peak Sales Forecast Dashboard

## What is This Dashboard?

The **Sales Peak Forecast Dashboard** is an easy-to-use tool that:
- 📊 Predicts when your products will reach peak sales
- 📈 Shows growth percentages for each item
- 📄 Exports professional reports to Word format
- 💡 Provides clear, understandable insights

Perfect for business users who need straightforward answers about sales trends!

---

## Step 1: Launch the Dashboard

Open a terminal in your project directory and run:

```bash
streamlit run app_dashboard.py
```

The dashboard will open in your browser automatically.

---

## Step 2: Upload Your Data

1. Click **"Upload your sales data (CSV)"** in the sidebar
2. Select your CSV file

**Your CSV file should have these columns:**
- **Date**: Any standard date format (2023-01-01, Jan 01 2023, etc.)
- **Product**: Product or item name (optional)
- **Sales**: Sales quantity or revenue value

**Example format:**
```
Date,Product,Sales
2023-01-01,Laptop,450
2023-02-01,Laptop,480
2023-01-01,Smartphone,320
2023-02-01,Smartphone,340
```

---

## Step 3: Configure Your Columns

After uploading, the sidebar shows your data preview. Select:
1. **Date Column** - Which column contains dates
2. **Product Column** - Which column contains product names (if you have one)
3. **Sales Column** - Which column has the sales/revenue data

You can also adjust the **Forecast Period** (3-24 months) using the slider.

---

## Step 4: View Peak Predictions

The dashboard automatically shows:

### 📊 Peak Predictions Summary
Card-style display showing for each product:
- **Peak Month** - When the product will reach maximum sales
- **Peak Sales** - The predicted sales value
- **Growth %** - How much it will grow from current levels

### 📈 Detailed Forecasts
For each product:
- Interactive chart showing past sales and forecast
- Peak point highlighted with a star
- Key metrics like peak month, sales value, and growth

---

## Step 5: Export to Word Report

Click **"📥 Export Peak Analysis to Word"** to generate a professional report that includes:

✅ **Executive Summary** - Overview of analysis  
✅ **Key Findings** - Top-level insights  
✅ **Peak Predictions Table** - All products at a glance  
✅ **Detailed Analysis** - Per-product deep dive with:
   - Current sales vs. peak forecast
   - Growth percentages
   - Recommendations for each product
   - Timeline to peak

✅ **Methodology** - How the forecasts were created  

The Word file will download automatically. Perfect for sharing with team members!

---

## Test with Sample Data

A sample dataset with 4 products is included:

```bash
data/products_sales_data.csv
```

Products in sample:
- **Laptop**: Electronics - seasonal peak in Dec
- **Smartphone**: Electronics - steady growth trend  
- **Tablet**: Electronics - gradual increase
- **Headphones**: Accessories - consistent growth

Use this to test the dashboard features!

---

## Understanding the Results

### What Does "Peak" Mean?

**Peak** = The highest expected sales value in the forecast period

Example:
- Current sales: 100 units/month
- Predicted peak: 125 units in June 2025
- Growth: **25%**

This means your sales are expected to grow by 25% and reach maximum levels in June.

### What Does "Days Until Peak" Mean?

Shows approximately how many days until the peak month is reached.
- **Positive number** = Days from today until peak
- **"Upcoming"** = Peak is very soon (within a few weeks)

### Growth Percentage

Shows the expected increase from your current (most recent) sales to the predicted peak.

Examples:
- **+25%** = Good growth expected - plan inventory increase
- **+5%** = Stable, modest growth - monitor as usual
- **0% or negative** = Flat or declining - review marketing strategy

---

## Tips for Best Results

✅ **Use at least 12 months of data** for accurate forecasts  
✅ **Data should be consistent** (monthly, weekly, daily - any regular interval)  
✅ **Remove unusual one-time spikes** that don't represent normal patterns  
✅ **Run forecast regularly** with new data to track accuracy  
✅ **Use predictions as guidance**, not absolute guarantees  

---

## FAQ

**Q: Can I use data with a different time interval (weekly, daily)?**  
A: Yes! The system auto-detects frequency. Can be daily, weekly, monthly, etc.

**Q: What if I don't have a Product column?**  
A: That's fine! Leave "Product Column" blank and analyze all sales together.

**Q: How far ahead can I forecast?**  
A: 3-24 months ahead. More data = more reliable longer forecasts.

**Q: Can I export results in other formats?**  
A: Currently Word (via button) and CSV (via download button). More formats coming soon.

**Q: What if my forecast looks wrong?**  
A: Check your data for:
   - Unusual spikes or gaps
   - Inconsistent date format
   - Missing values
   - Wrong column mapping

---

## Common Column Names

System recognizes columns named:
- Date: "Date", "date", "Date_Sold", "Transaction_Date"
- Product: "Product", "Product_Id", "Item", "Item_Name", "Product_Name"
- Sales: "Sales", "Revenue", "Units", "Quantity", "Units_Sold"

Can't find your column? Select manually in the sidebar!

---

## Need Help?

Make sure your CSV:
1. ✅ Has a date column with dates
2. ✅ Has a sales column with numbers
3. ✅ Is properly formatted (no special characters in headers)
4. ✅ Has at least 12 rows of data
5. ✅ Is under 16MB in size

---

## Next Steps

After generating a report:
- 📧 Share the Word document with stakeholders
- 📋 Use predictions for inventory planning
- 🎯 Set sales targets based on peak months
- 📊 Monitor actual sales vs. forecast
- ♻️ Re-run dashboard monthly with new data

---

**Happy Forecasting! 📈**
