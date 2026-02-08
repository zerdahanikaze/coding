import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from prophet import Prophet
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

def detect_frequency(dates):
    """
    Auto-detect the frequency of time series data.
    """
    if len(dates) < 2:
        return 'MS'  # Default to month start
    
    # Convert to pandas DatetimeIndex if needed
    if not isinstance(dates, pd.DatetimeIndex):
        dates = pd.to_datetime(dates)
    
    # Calculate the most common difference
    diffs = (dates[1:] - dates[:-1]).days
    median_diff = np.median(diffs)
    
    if median_diff <= 1:
        return 'D'  # Daily
    elif median_diff <= 7:
        return 'W'  # Weekly
    elif median_diff <= 31:
        return 'MS'  # Month start
    elif median_diff <= 365:
        return 'QS'  # Quarter start
    else:
        return 'YS'  # Year start

def suggest_arima_order(series, p_range=(0,5), d_range=(0,2), q_range=(0,5)):
    """
    Auto-suggest ARIMA order based on data characteristics.
    Uses AIC criteria for best fit.
    """
    best_order = (1, 1, 1)
    best_aic = np.inf
    
    for p in range(*p_range):
        for d in range(*d_range):
            for q in range(*q_range):
                try:
                    model = ARIMA(series, order=(p, d, q))
                    fitted = model.fit()
                    if fitted.aic < best_aic:
                        best_aic = fitted.aic
                        best_order = (p, d, q)
                except:
                    continue
    
    return best_order

def forecast_sales(data, periods, model_choice, auto_config=True):
    """
    Forecast sales and revenue using the chosen model.
    
    Parameters:
    - data: preprocessed dataframe with date, sales, revenue
    - periods: number of periods to forecast
    - model_choice: 'ARIMA', 'Prophet', or 'Linear Regression'
    - auto_config: if True, auto-detect best parameters
    """
    # Prepare data
    data = data.copy()
    data['date'] = pd.to_datetime(data['date'])
    data = data.set_index('date')
    
    # Detect frequency
    freq = detect_frequency(data.index)
    
    # Forecast sales
    try:
        if model_choice == "ARIMA":
            sales_forecast = arima_forecast(data['sales'], periods, auto_config, freq)
        elif model_choice == "Prophet":
            sales_forecast = prophet_forecast(data, periods, freq)
        elif model_choice == "Linear Regression":
            sales_forecast = linear_regression_forecast(data['sales'], periods)
        else:
            raise ValueError(f"Unknown model: {model_choice}")
    except Exception as e:
        raise ValueError(f"Forecasting failed with {model_choice}: {str(e)}")
    
    # Forecast revenue (can use separate model or ratio)
    try:
        revenue_forecast = forecast_revenue(data, sales_forecast, model_choice, periods, freq)
    except:
        # Fallback to ratio-based approach
        avg_ratio = (data['revenue'] / data['sales']).mean()
        revenue_forecast = sales_forecast * avg_ratio
    
    # Create forecast dataframe with proper frequency inference
    last_date = data.index[-1]
    if freq == 'D':
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods, freq=freq)
    else:
        future_dates = pd.date_range(start=last_date, periods=periods+1, freq=freq)[1:]
    
    forecast_df = pd.DataFrame({
        'date': future_dates[:len(sales_forecast)],
        'forecast_sales': sales_forecast,
        'forecast_revenue': revenue_forecast
    })
    
    return forecast_df

def arima_forecast(series, periods, auto_config=True, freq='MS'):
    """
    ARIMA forecasting with auto parameter selection.
    """
    try:
        if auto_config:
            order = suggest_arima_order(series)
        else:
            order = (5, 1, 0)
        
        model = ARIMA(series, order=order)
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=periods)
        return forecast.values
    except Exception as e:
        raise ValueError(f"ARIMA failed: {str(e)}. Try a different model.")

def prophet_forecast(data, periods, freq='MS'):
    """
    Prophet forecasting with frequency detection.
    """
    try:
        df = pd.DataFrame({
            'ds': data.index,
            'y': data['sales'].values
        })
        
        model = Prophet(daily_seasonality=False)
        model.fit(df)
        
        future = model.make_future_dataframe(periods=periods, freq=freq)
        forecast = model.predict(future)
        return forecast['yhat'].tail(periods).values
    except Exception as e:
        raise ValueError(f"Prophet failed: {str(e)}. Try a different model.")

def linear_regression_forecast(series, periods):
    """
    Linear regression forecasting with trend detection.
    """
    try:
        X = np.arange(len(series)).reshape(-1, 1)
        y = series.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        future_X = np.arange(len(series), len(series) + periods).reshape(-1, 1)
        forecast = model.predict(future_X)
        
        # Ensure non-negative forecasts
        forecast = np.maximum(forecast, 0)
        return forecast
    except Exception as e:
        raise ValueError(f"Linear Regression failed: {str(e)}")

def forecast_revenue(data, sales_forecast, model_choice, periods, freq):
    """
    Forecast revenue using the same model as sales or ratio-based approach.
    """
    if model_choice == "ARIMA":
        revenue = arima_forecast(data['revenue'], periods, auto_config=True, freq=freq)
    elif model_choice == "Prophet":
        revenue = prophet_forecast(
            pd.DataFrame({'sales': data['sales'].values, 'revenue': data['revenue'].values}, index=data.index),
            periods, freq
        )
    elif model_choice == "Linear Regression":
        revenue = linear_regression_forecast(data['revenue'], periods)
    else:
        revenue = sales_forecast * ((data['revenue'] / data['sales']).mean())
    
    return revenue

def calculate_accuracy_metrics(actual, predicted):
    """
    Calculate MAE, RMSE, MAPE accuracy metrics.
    """
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100 if np.all(actual != 0) else np.inf
    return {'mae': mae, 'rmse': rmse, 'mape': mape}

def evaluate_models(data, periods, test_size=0.2):
    """
    Evaluate all models on test data and return the best one.
    
    Parameters:
    - data: preprocessed dataframe
    - periods: forecast periods
    - test_size: proportion of data to use for testing (0-1)
    
    Returns:
    - Dictionary with best model, accuracy, and all results
    """
    data = data.copy()
    data['date'] = pd.to_datetime(data['date'])
    
    # Split data
    split_idx = int(len(data) * (1 - test_size))
    train = data.iloc[:split_idx].copy()
    test = data.iloc[split_idx:].copy()
    
    models_to_test = ['ARIMA', 'Prophet', 'Linear Regression']
    results = {}
    best_model = None
    best_accuracy = float('inf')
    
    for model_name in models_to_test:
        try:
            # Train on train set, forecast test period
            forecast_df = forecast_sales(train, len(test), model_name, auto_config=True)
            
            # Calculate accuracy on test set
            if len(forecast_df) >= len(test):
                predicted = forecast_df['forecast_sales'].values[:len(test)]
                actual = test['sales'].values
                
                metrics = calculate_accuracy_metrics(actual, predicted)
                accuracy = 100 - metrics['mape'] if metrics['mape'] != np.inf else 0
                accuracy = max(0, min(100, accuracy))  # Clamp between 0-100
                
                results[model_name] = {
                    'forecast': forecast_df,
                    'accuracy': round(accuracy, 2),
                    'mape': round(metrics['mape'], 2),
                    'rmse': round(metrics['rmse'], 2)
                }
                
                if metrics['mape'] < best_accuracy and metrics['mape'] != np.inf:
                    best_accuracy = metrics['mape']
                    best_model = model_name
        except:
            results[model_name] = {
                'forecast': None,
                'accuracy': 0,
                'mape': np.inf,
                'rmse': np.inf
            }
    
    # If no model succeeded, default to Prophet
    if best_model is None:
        best_model = 'Prophet'
    
    # Get best forecast on full data
    best_forecast = forecast_sales(data, periods, best_model, auto_config=True)
    results[best_model]['forecast'] = best_forecast
    
    return {
        'best_model': best_model,
        'best_accuracy': results[best_model]['accuracy'],
        'results': results
    }