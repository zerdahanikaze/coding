# Smart Sales and Revenue Forecasting System

A Python-based application for forecasting sales and revenue using historical business data. The system adapts to various business datasets and provides interactive visualizations through a Streamlit dashboard.

## Features

- **Adaptive Data Handling**: Accepts CSV files with date, sales, and revenue columns
- **Multiple Forecasting Models**: ARIMA, Facebook Prophet, and Linear Regression
- **Interactive Dashboard**: Built with Streamlit for easy visualization
- **Flexible Forecast Periods**: Configure forecast length from 1 to 24 months

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the dashboard:
   ```
   streamlit run app.py
   ```

2. Upload your historical data (CSV format) or use the provided sample data

3. Configure forecast parameters:
   - Select forecasting model
   - Set forecast periods

4. View historical data and forecasts with interactive charts

## Data Format

Your CSV file should contain at least these columns:
- `date`: Date in YYYY-MM-DD format
- `sales`: Sales figures
- `revenue`: Revenue figures

## Models

- **ARIMA**: Statistical model for time series forecasting
- **Prophet**: Facebook's forecasting tool for seasonal data
- **Linear Regression**: Simple trend-based forecasting

## Requirements

- Python 3.7+
- See requirements.txt for dependencies