import argparse
from src.data_preprocessing import load_and_preprocess_data
from src.forecasting import forecast_sales
import pandas as pd
import os

def run(data_path, periods, model):
    df = load_and_preprocess_data(data_path)
    models = [model] if model != 'all' else ['ARIMA','Prophet','Linear Regression']
    out_dir = 'data/forecasts'
    os.makedirs(out_dir, exist_ok=True)

    for m in models:
        print(f"Running forecast with model: {m} for {periods} periods")
        forecast_df = forecast_sales(df, periods, m)
        out_path = os.path.join(out_dir, f'forecast_{m.replace(" ","_")}_{periods}.csv')
        forecast_df.to_csv(out_path, index=False)
        print(f"Saved forecast to: {out_path}")
        print(forecast_df.head())
        print('-'*60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run sales/revenue forecasts locally')
    parser.add_argument('--data', default='data/sample_sales_data.csv', help='Path to CSV data')
    parser.add_argument('--periods', type=int, default=6, help='Forecast periods (months)')
    parser.add_argument('--model', default='all', choices=['ARIMA','Prophet','Linear Regression','all'], help='Model to run')
    args = parser.parse_args()
    run(args.data, args.periods, args.model)
