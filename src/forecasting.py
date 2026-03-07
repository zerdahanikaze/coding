import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing
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

def exponential_smoothing_forecast(series, periods, seasonal_periods=12):
    """
    Exponential Smoothing (Holt-Winters) forecasting.
    """
    try:
        # Detect seasonality
        if len(series) < seasonal_periods * 2:
            seasonal_periods = max(4, len(series) // 4)
        
        model = ExponentialSmoothing(
            series,
            seasonal_periods=seasonal_periods,
            trend='add',
            seasonal='add',
            initialization_method='estimated'
        )
        model_fit = model.fit(optimized=True)
        forecast = model_fit.forecast(steps=periods)
        return np.maximum(forecast.values, 0)  # Ensure non-negative
    except Exception as e:
        raise ValueError(f"Exponential Smoothing failed: {str(e)}")

def sarima_forecast(series, periods, freq='MS'):
    """
    Seasonal ARIMA (SARIMA) forecasting.
    """
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        
        # Determine seasonal period based on frequency
        if freq == 'D':
            seasonal_period = 7  # Weekly
        elif freq == 'W':
            seasonal_period = 52  # Yearly
        elif freq == 'MS':
            seasonal_period = 12  # Yearly
        else:
            seasonal_period = 4   # Quarterly
        
        # Adjust seasonal period if series is too short
        if len(series) < seasonal_period * 2:
            seasonal_period = max(2, seasonal_period // 2)
        
        # Simple SARIMA order
        order = (1, 1, 1)
        seasonal_order = (1, 1, 1, seasonal_period)
        
        model = SARIMAX(series, order=order, seasonal_order=seasonal_order)
        model_fit = model.fit(disp=False)
        forecast = model_fit.forecast(steps=periods)
        return np.maximum(forecast.values, 0)  # Ensure non-negative
    except Exception as e:
        raise ValueError(f"SARIMA failed: {str(e)}")

def moving_average_forecast(series, periods, window=3):
    """
    Moving Average based forecasting.
    """
    try:
        # Use exponential moving average for more weight on recent data
        ema = series.ewm(span=min(window, len(series))).mean()
        
        # Get last value and trend
        last_value = ema.iloc[-1]
        trend = (ema.iloc[-1] - ema.iloc[-min(5, len(series))]) / min(5, len(series))
        
        # Generate forecast
        forecast = np.array([last_value + (trend * i) for i in range(1, periods + 1)])
        return np.maximum(forecast, 0)  # Ensure non-negative
    except Exception as e:
        raise ValueError(f"Moving Average failed: {str(e)}")

def simple_exponential_smoothing_forecast(series, periods, alpha=0.3):
    """
    Simple Exponential Smoothing forecasting.
    """
    try:
        from statsmodels.tsa.holtwinters import SimpleExpSmoothing
        model = SimpleExpSmoothing(series)
        model_fit = model.fit(smoothing_level=alpha, optimized=False)
        forecast = model_fit.forecast(steps=periods)
        return np.maximum(forecast.values, 0)  # Ensure non-negative
    except Exception as e:
        raise ValueError(f"Simple Exponential Smoothing failed: {str(e)}")

def analyze_data_characteristics(series):
    """
    Analyze time series data to detect patterns and characteristics.
    
    Returns:
    - Dictionary with characteristics and recommended models
    """
    try:
        characteristics = {
            'length': len(series),
            'mean': series.mean(),
            'std': series.std(),
            'cv': series.std() / series.mean() if series.mean() != 0 else 0,  # Coefficient of variation
        }
        
        # Detect trend
        x = np.arange(len(series))
        z = np.polyfit(x, series.values, 1)
        trend_strength = abs(z[0]) / series.std() if series.std() > 0 else 0
        characteristics['trend_strength'] = trend_strength
        characteristics['has_trend'] = trend_strength > 0.1
        
        # Detect seasonality using autocorrelation
        if len(series) >= 4:
            acf_values = [series.autocorr(lag=lag) for lag in range(1, min(13, len(series)//2))]
            max_acf = max(acf_values) if acf_values else 0
            characteristics['seasonality_strength'] = max_acf
            characteristics['has_seasonality'] = max_acf > 0.3
        else:
            characteristics['seasonality_strength'] = 0
            characteristics['has_seasonality'] = False
        
        # Detect noise (volatility)
        returns = series.pct_change().dropna()
        characteristics['volatility'] = returns.std() if len(returns) > 0 else 0
        characteristics['is_noisy'] = characteristics['volatility'] > 0.1
        
        # Stationarity test
        try:
            adf_result = adfuller(series, autolag='AIC')
            characteristics['is_stationary'] = adf_result[1] < 0.05
        except:
            characteristics['is_stationary'] = False
        
        return characteristics
    except Exception as e:
        return {'error': str(e), 'length': len(series)}

def recommend_best_model(data, periods, test_size=0.2):
    """
    Automatically evaluate all models and recommend the best one based on accuracy.
    
    Parameters:
    - data: preprocessed dataframe with date, sales, revenue
    - periods: forecast periods
    - test_size: proportion of data to use for testing
    
    Returns:
    - Dictionary with best_model, accuracy, characteristics, and detailed results
    """
    data = data.copy()
    data['date'] = pd.to_datetime(data['date'])
    
    # Analyze data characteristics
    characteristics = analyze_data_characteristics(data['sales'])
    
    # Split data for testing
    split_idx = int(len(data) * (1 - test_size))
    train = data.iloc[:split_idx].copy()
    test = data.iloc[split_idx:].copy()
    
    # Ensure we have enough test data
    if len(test) < 2:
        test_size = 0.15
        split_idx = int(len(data) * (1 - test_size))
        train = data.iloc[:split_idx].copy()
        test = data.iloc[split_idx:].copy()
    
    models_to_test = ['Prophet', 'ARIMA', 'Exponential Smoothing', 'SARIMA', 'Moving Average', 'Linear Regression']
    results = {}
    best_model = None
    best_accuracy = -np.inf
    model_accuracies = {}
    
    for model_name in models_to_test:
        try:
            # Train and forecast
            forecast_df = forecast_sales(train, len(test), model_name, auto_config=True)
            
            # Calculate accuracy
            if len(forecast_df) >= len(test):
                predicted = forecast_df['forecast_sales'].values[:len(test)]
                actual = test['sales'].values
                
                # Ensure no NaN values
                valid_idx = ~(np.isnan(predicted) | np.isnan(actual))
                if valid_idx.sum() > 0:
                    predicted = predicted[valid_idx]
                    actual = actual[valid_idx]
                    
                    mae = np.mean(np.abs(actual - predicted))
                    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
                    mape = np.mean(np.abs((actual - predicted) / actual)) * 100 if np.all(actual != 0) else 100
                    
                    # Accuracy as percentage (0-100)
                    accuracy = max(0, 100 - mape) if mape < 100 else 0
                    
                    results[model_name] = {
                        'accuracy': round(accuracy, 2),
                        'mae': round(mae, 2),
                        'rmse': round(rmse, 2),
                        'mape': round(mape, 2)
                    }
                    model_accuracies[model_name] = accuracy
                    
                    if accuracy > best_accuracy:
                        best_accuracy = accuracy
                        best_model = model_name
        except Exception as e:
            results[model_name] = {
                'accuracy': 0,
                'mae': np.inf,
                'rmse': np.inf,
                'mape': np.inf,
                'error': str(e)
            }
    
    # If no model succeeded, recommend based on characteristics
    if best_model is None:
        if characteristics.get('has_seasonality', False):
            best_model = 'SARIMA'
        elif characteristics.get('has_trend', False):
            best_model = 'Exponential Smoothing'
        else:
            best_model = 'Prophet'
    
    # Determine why this model was selected
    reason = ""
    if characteristics.get('has_seasonality', False) and characteristics.get('has_trend', False):
        reason = "Data has clear seasonality and trend. Selected model handles both components."
    elif characteristics.get('has_seasonality', False):
        reason = "Data shows seasonal patterns. Selected model captures seasonality well."
    elif characteristics.get('has_trend', False):
        reason = "Data has strong trend component. Selected model follows trends effectively."
    elif characteristics.get('is_noisy', False):
        reason = "Data is noisy. Selected model smooths fluctuations effectively."
    elif characteristics.get('is_stationary', False):
        reason = "Data is stationary. Selected model suited for stationary series."
    else:
        reason = "Model selected based on comparative accuracy testing."
    
    return {
        'best_model': best_model,
        'accuracy': round(best_accuracy, 2),
        'reason': reason,
        'characteristics': characteristics,
        'model_accuracies': model_accuracies,
        'detailed_results': results
    }

def forecast_sales(data, periods, model_choice, auto_config=True):
    """
    Forecast sales and revenue using the chosen model.
    
    Parameters:
    - data: preprocessed dataframe with date, sales, revenue
    - periods: number of periods to forecast
    - model_choice: 'ARIMA', 'Prophet', 'Linear Regression', 'Exponential Smoothing', 'SARIMA', or 'Moving Average'
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
        elif model_choice == "Exponential Smoothing":
            sales_forecast = exponential_smoothing_forecast(data['sales'], periods)
        elif model_choice == "SARIMA":
            sales_forecast = sarima_forecast(data['sales'], periods, freq)
        elif model_choice == "Moving Average":
            sales_forecast = moving_average_forecast(data['sales'], periods)
        elif model_choice == "Simple Exponential Smoothing":
            sales_forecast = simple_exponential_smoothing_forecast(data['sales'], periods)
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
    elif model_choice == "Exponential Smoothing":
        revenue = exponential_smoothing_forecast(data['revenue'], periods)
    elif model_choice == "SARIMA":
        revenue = sarima_forecast(data['revenue'], periods, freq)
    elif model_choice == "Moving Average":
        revenue = moving_average_forecast(data['revenue'], periods)
    elif model_choice == "Simple Exponential Smoothing":
        revenue = simple_exponential_smoothing_forecast(data['revenue'], periods)
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
    
    models_to_test = ['Prophet', 'ARIMA', 'Exponential Smoothing', 'SARIMA', 'Moving Average', 'Simple Exponential Smoothing', 'Linear Regression']
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