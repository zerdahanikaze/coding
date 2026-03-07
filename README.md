# Smart Sales and Revenue Forecasting System

A Python-based application for forecasting sales and revenue using historical business data. This system features a user-friendly dashboard that identifies when products will reach peak performance and generates professional Word reports.

## Features

✨ **Core Features**
- 📊 **Multi-Product Analysis**: Analyze multiple products simultaneously
- 🎯 **Peak Predictions**: Automatically identifies when each product will reach peak sales
- 📈 **Advanced Forecasting**: Uses Prophet, ARIMA, and Linear Regression models
- 📄 **Word Export**: Generate professional reports in Word format
- 📉 **Interactive Charts**: Visual forecasts with growth metrics
- 💡 **Growth Analysis**: Shows expected growth percentages for each product
- 🔍 **Data Flexibility**: Works with various CSV formats

## Dashboard Features

### Peak Prediction Dashboard (`app_dashboard.py`)
The main dashboard for end-users featuring:
- **Simple Data Upload**: Select Date, Product, and Sales columns
- **Automatic Peak Detection**: System finds peak months for each product
- **Clear Metrics Display**: 
  - Peak Month prediction
  - Peak Sales Value
  - Expected Growth %
  - Days Until Peak
- **Interactive Visualizations**: Charts showing historical data and forecasts
- **Professional Reports**: Export results to Word format with insights and recommendations

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Launch the Peak Prediction Dashboard

```bash
streamlit run app_dashboard.py
```

Then:
1. Upload your CSV file with sales data
2. Map columns: Date, Product (optional), and Sales
3. Set forecast period (3-24 months)
4. View peak predictions automatically
5. Export results to Word report

### Sample Data Format

Required columns:
- **Date**: Transaction date (YYYY-MM-DD or flexible format)
- **Product**: Product or item name (optional - analysis works with single product too)
- **Sales**: Sales quantity or revenue value

Example:
```csv
Date,Product,Sales
2023-01-01,Laptop,450
2023-02-01,Laptop,480
2023-01-01,Smartphone,320
2023-02-01,Smartphone,340
```

A sample dataset is provided at: `data/products_sales_data.csv`

## Example Output

**Peak Predictions Summary:**
- 📦 **Laptop**: Peaks in December 2024 (750 units, +25.4% growth)
- 📦 **Smartphone**: Peaks in November 2024 (540 units, +18.8% growth)
- 📦 **Tablet**: Peaks in December 2024 (375 units, +14.3% growth)

## Forecasting Models

- **Prophet**: Recommended for seasonal data with trend changes (default)
- **ARIMA**: Statistical model for time series with complex patterns
- **Linear Regression**: Simple trend-based forecasting

## Report Export

The Word export includes:
- Executive Summary
- Key findings and statistics
- Peak predictions table
- Detailed analysis per product
- Growth metrics and recommendations
- Methodology explanation
- Generated timestamp

## Project Structure

```
.
├── app_dashboard.py           # Main Peak Prediction Dashboard
├── src/
│   ├── data_preprocessing.py  # Data handling
│   ├── forecasting.py         # Forecasting models
│   └── word_reporter.py       # Word report generation
├── data/
│   ├── sample_sales_data.csv
│   ├── products_sales_data.csv (sample with multiple products)
│   └── forecasts/
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.7+
- pandas, numpy, scikit-learn
- streamlit, plotly
- prophet, statsmodels
- python-docx (for Word export)
- See requirements.txt for dependencies

## Deployment & Demo

- Deploy the app on Streamlit Community Cloud for a hosted interactive dashboard. Connect your GitHub account and select this repo and `app.py` as the app entrypoint.
- A GitHub Actions CI workflow (`.github/workflows/ci.yml`) runs on push and executes `run_forecast.py`, producing forecast CSVs which are uploaded as workflow artifacts.

To run the forecasts locally (CLI):

```bash
D:/coding/.venv/Scripts/Activate.ps1
python run_forecast.py --periods 6 --model all
```

Demo input is available at `data/demo_input.csv` and generated forecasts are saved to `data/forecasts/` by the runner.
