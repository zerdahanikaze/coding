import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

def forecast_sales(data, periods, model_choice):
    """
    Forecast sales and revenue using the chosen model.
    """
    # Prepare data
    data = data.copy()
    data['date'] = pd.to_datetime(data['date'])
    data = data.set_index('date')
    
    # Forecast sales
    if model_choice == "ARIMA":
        sales_forecast = arima_forecast(data['sales'], periods)
    elif model_choice == "Prophet":
        sales_forecast = prophet_forecast(data['sales'], periods)
    elif model_choice == "Linear Regression":
        sales_forecast = linear_regression_forecast(data['sales'], periods)
    
    # Assume revenue is proportional to sales (simple assumption)
    # In real scenario, might need separate forecasting
    avg_ratio = (data['revenue'] / data['sales']).mean()
    revenue_forecast = sales_forecast * avg_ratio
    
    # Create forecast dataframe
    future_dates = pd.date_range(start=data.index[-1] + pd.DateOffset(months=1), periods=periods, freq='M')
    forecast_df = pd.DataFrame({
        'date': future_dates,
        'forecast_sales': sales_forecast,
        'forecast_revenue': revenue_forecast
    })
    
    return forecast_df

def arima_forecast(series, periods):
    model = ARIMA(series, order=(5,1,0))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=periods)
    return forecast.values

def prophet_forecast(series, periods):
    df = pd.DataFrame({'ds': series.index, 'y': series.values})
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=periods, freq='M')
    forecast = model.predict(future)
    return forecast['yhat'].tail(periods).values

def linear_regression_forecast(series, periods):
    # Simple linear regression on time index
    X = np.arange(len(series)).reshape(-1, 1)
    y = series.values
    model = LinearRegression()
    model.fit(X, y)
    
    # Forecast
    future_X = np.arange(len(series), len(series) + periods).reshape(-1, 1)
    forecast = model.predict(future_X)
    return forecast