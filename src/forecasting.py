"""
forecasting.py — Robust sales/revenue forecasting engine.

Handles two dataset shapes transparently:
  1. Simple:   date | sales | revenue
  2. Product:  date | product | sales | revenue

All models gracefully degrade — if a library is missing or fitting fails,
the model is skipped and a fallback is used so the app never crashes.
"""

import warnings
import numpy as np
import pandas as pd
from typing import Optional

warnings.filterwarnings("ignore")

# ── Optional heavy imports (degrade gracefully) ───────────────────────────────
try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from sklearn.linear_model import LinearRegression


# ── Helpers ───────────────────────────────────────────────────────────────────

def _aggregate_to_series(df: pd.DataFrame, value_col: str = 'sales') -> pd.Series:
    """
    Convert any supported DataFrame shape into a clean DatetimeIndex Series.
    Groups by date and sums the value column so duplicate dates are merged.
    """
    s = df.groupby('date')[value_col].sum().sort_index()
    s.index = pd.DatetimeIndex(s.index)
    # Infer and regularise frequency
    inferred = pd.infer_freq(s.index)
    if inferred:
        s = s.asfreq(inferred, fill_value=0)
    else:
        # Resample to monthly if freq is ambiguous
        s = s.resample('MS').sum()
    return s.fillna(0)


def _forecast_dates(last_date: pd.Timestamp, periods: int, freq: str) -> pd.DatetimeIndex:
    return pd.date_range(start=last_date, periods=periods + 1, freq=freq)[1:]


def _detect_freq(series: pd.Series) -> str:
    freq = pd.infer_freq(series.index)
    if freq is None:
        return 'MS'
    return freq


def _mape(actual, predicted) -> Optional[float]:
    actual, predicted = np.array(actual), np.array(predicted)
    mask = actual != 0
    if mask.sum() == 0:
        return None
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


def _rmse(actual, predicted) -> Optional[float]:
    actual, predicted = np.array(actual), np.array(predicted)
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def _safe_positive(arr) -> np.ndarray:
    """Clip forecast to non-negative values."""
    return np.clip(np.array(arr, dtype=float), 0, None)


def _split_train_test(series: pd.Series, test_size: int = 3):
    test_size = min(test_size, max(1, len(series) // 5))
    return series.iloc[:-test_size], series.iloc[-test_size:]


# ── Individual model forecasters ──────────────────────────────────────────────

def _forecast_prophet(series: pd.Series, periods: int) -> dict:
    if not HAS_PROPHET:
        raise ImportError("prophet not installed")
    if len(series) < 4:
        raise ValueError("Too few data points for Prophet")

    train, test = _split_train_test(series)
    freq = _detect_freq(series)

    def _fit_predict(s, n):
        df_p = pd.DataFrame({'ds': s.index, 'y': s.values})
        m = Prophet(yearly_seasonality='auto', weekly_seasonality=False,
                    daily_seasonality=False, seasonality_mode='additive')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m.fit(df_p)
        future = m.make_future_dataframe(periods=n, freq=freq)
        fc = m.predict(future)
        return fc[fc['ds'] > s.index[-1]]['yhat'].values[:n]

    test_pred = _fit_predict(train, len(test))
    mape = _mape(test.values, test_pred)
    rmse = _rmse(test.values, test_pred)

    forecast_vals = _fit_predict(series, periods)
    dates = _forecast_dates(series.index[-1], periods, freq)

    return {
        'forecast': _safe_positive(forecast_vals),
        'dates': dates,
        'mape': mape,
        'rmse': rmse,
        'accuracy': round(100 - mape, 2) if mape else None
    }


def _forecast_arima(series: pd.Series, periods: int) -> dict:
    if not HAS_STATSMODELS:
        raise ImportError("statsmodels not installed")
    if len(series) < 6:
        raise ValueError("Too few data points for ARIMA")

    freq = _detect_freq(series)
    train, test = _split_train_test(series)

    def _fit_predict(s, n, order=(1, 1, 1)):
        model = ARIMA(s, order=order)
        fit = model.fit()
        return fit.forecast(steps=n)

    # Try common orders, fall back gracefully
    orders = [(1, 1, 1), (1, 1, 0), (0, 1, 1), (2, 1, 2), (1, 0, 0)]
    last_exc = None
    for order in orders:
        try:
            test_pred = _fit_predict(train, len(test), order)
            mape = _mape(test.values, test_pred)
            rmse = _rmse(test.values, test_pred)
            forecast_vals = _fit_predict(series, periods, order)
            dates = _forecast_dates(series.index[-1], periods, freq)
            return {
                'forecast': _safe_positive(forecast_vals),
                'dates': dates,
                'mape': mape,
                'rmse': rmse,
                'accuracy': round(100 - mape, 2) if mape else None
            }
        except Exception as e:
            last_exc = e
            continue
    raise RuntimeError(f"ARIMA failed all orders: {last_exc}")


def _forecast_sarima(series: pd.Series, periods: int) -> dict:
    if not HAS_STATSMODELS:
        raise ImportError("statsmodels not installed")
    if len(series) < 12:
        raise ValueError("Too few data points for SARIMA (need >= 12)")

    freq = _detect_freq(series)
    # Determine seasonal period
    if 'M' in freq or 'MS' in freq:
        m = 12
    elif 'Q' in freq:
        m = 4
    elif 'W' in freq:
        m = 52
    else:
        m = 12

    train, test = _split_train_test(series)

    def _fit_predict(s, n):
        model = SARIMAX(s, order=(1, 1, 1), seasonal_order=(1, 1, 1, m),
                        enforce_stationarity=False, enforce_invertibility=False)
        fit = model.fit(disp=False)
        return fit.forecast(steps=n)

    try:
        test_pred = _fit_predict(train, len(test))
        mape = _mape(test.values, test_pred)
        rmse = _rmse(test.values, test_pred)
        forecast_vals = _fit_predict(series, periods)
        dates = _forecast_dates(series.index[-1], periods, freq)
        return {
            'forecast': _safe_positive(forecast_vals),
            'dates': dates,
            'mape': mape,
            'rmse': rmse,
            'accuracy': round(100 - mape, 2) if mape else None
        }
    except Exception as e:
        raise RuntimeError(f"SARIMA failed: {e}")


def _forecast_exp_smoothing(series: pd.Series, periods: int) -> dict:
    if not HAS_STATSMODELS:
        raise ImportError("statsmodels not installed")
    if len(series) < 4:
        raise ValueError("Too few data points")

    freq = _detect_freq(series)
    train, test = _split_train_test(series)

    def _fit_predict(s, n):
        trend_type = 'add' if len(s) >= 4 else None
        seasonal_type = None
        seasonal_periods = None

        if 'M' in freq or 'MS' in freq:
            if len(s) >= 24:
                seasonal_type = 'add'
                seasonal_periods = 12
        elif 'Q' in freq:
            if len(s) >= 8:
                seasonal_type = 'add'
                seasonal_periods = 4

        model = ExponentialSmoothing(
            s, trend=trend_type,
            seasonal=seasonal_type,
            seasonal_periods=seasonal_periods,
            initialization_method='estimated'
        )
        fit = model.fit(optimized=True)
        return fit.forecast(n)

    test_pred = _fit_predict(train, len(test))
    mape = _mape(test.values, test_pred)
    rmse = _rmse(test.values, test_pred)
    forecast_vals = _fit_predict(series, periods)
    dates = _forecast_dates(series.index[-1], periods, freq)

    return {
        'forecast': _safe_positive(forecast_vals),
        'dates': dates,
        'mape': mape,
        'rmse': rmse,
        'accuracy': round(100 - mape, 2) if mape else None
    }


def _forecast_simple_exp_smoothing(series: pd.Series, periods: int) -> dict:
    if not HAS_STATSMODELS:
        raise ImportError("statsmodels not installed")
    if len(series) < 3:
        raise ValueError("Too few data points")

    freq = _detect_freq(series)
    train, test = _split_train_test(series)

    def _fit_predict(s, n):
        model = SimpleExpSmoothing(s, initialization_method='estimated')
        fit = model.fit(optimized=True)
        return fit.forecast(n)

    test_pred = _fit_predict(train, len(test))
    mape = _mape(test.values, test_pred)
    rmse = _rmse(test.values, test_pred)
    forecast_vals = _fit_predict(series, periods)
    dates = _forecast_dates(series.index[-1], periods, freq)

    return {
        'forecast': _safe_positive(forecast_vals),
        'dates': dates,
        'mape': mape,
        'rmse': rmse,
        'accuracy': round(100 - mape, 2) if mape else None
    }


def _forecast_moving_average(series: pd.Series, periods: int) -> dict:
    freq = _detect_freq(series)
    train, test = _split_train_test(series)

    # Adaptive window: use up to 1/3 of training length, min 2, max 12
    window = max(2, min(12, len(train) // 3))

    def _fit_predict(s, n):
        forecasts = []
        history = list(s.values)
        for _ in range(n):
            val = np.mean(history[-window:])
            forecasts.append(val)
            history.append(val)
        return np.array(forecasts)

    test_pred = _fit_predict(train, len(test))
    mape = _mape(test.values, test_pred)
    rmse = _rmse(test.values, test_pred)
    forecast_vals = _fit_predict(series, periods)
    dates = _forecast_dates(series.index[-1], periods, freq)

    return {
        'forecast': _safe_positive(forecast_vals),
        'dates': dates,
        'mape': mape,
        'rmse': rmse,
        'accuracy': round(100 - mape, 2) if mape else None
    }


def _forecast_linear_regression(series: pd.Series, periods: int) -> dict:
    freq = _detect_freq(series)
    train, test = _split_train_test(series)

    def _fit_predict(s, n):
        X = np.arange(len(s)).reshape(-1, 1)
        y = s.values
        model = LinearRegression()
        model.fit(X, y)
        X_future = np.arange(len(s), len(s) + n).reshape(-1, 1)
        return model.predict(X_future)

    test_pred = _fit_predict(train, len(test))
    mape = _mape(test.values, test_pred)
    rmse = _rmse(test.values, test_pred)
    forecast_vals = _fit_predict(series, periods)
    dates = _forecast_dates(series.index[-1], periods, freq)

    return {
        'forecast': _safe_positive(forecast_vals),
        'dates': dates,
        'mape': mape,
        'rmse': rmse,
        'accuracy': round(100 - mape, 2) if mape else None
    }


def _forecast_xgboost(series: pd.Series, periods: int) -> dict:
    if not HAS_XGBOOST:
        raise ImportError("xgboost not installed")
    if len(series) < 6:
        raise ValueError("Too few data points for XGBoost (need >= 6)")

    freq = _detect_freq(series)
    train, test = _split_train_test(series)

    def _fit_predict(s, n):
        # Create lagged features for time series forecasting
        lookback = min(5, max(1, len(s) // 4))  # Adaptive lookback window
        X, y = [], []
        
        for i in range(lookback, len(s)):
            X.append(s.iloc[i - lookback:i].values)
            y.append(s.iloc[i])
        
        if len(X) < 2:
            raise ValueError("Insufficient data after feature engineering")
        
        X = np.array(X)
        y = np.array(y)
        
        # Train XGBoost model with conservative hyperparameters
        model = XGBRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
            eval_metric='rmse'
        )
        model.fit(X, y, verbose=False)
        
        # Forecast iteratively
        forecasts = []
        current_window = list(s.iloc[-lookback:].values)
        
        for _ in range(n):
            X_next = np.array(current_window[-lookback:]).reshape(1, -1)
            pred = model.predict(X_next)[0]
            pred = max(0, pred)  # Ensure non-negative
            forecasts.append(pred)
            current_window.append(pred)
        
        return np.array(forecasts)

    try:
        test_pred = _fit_predict(train, len(test))
        mape = _mape(test.values, test_pred)
        rmse = _rmse(test.values, test_pred)
        forecast_vals = _fit_predict(series, periods)
        dates = _forecast_dates(series.index[-1], periods, freq)
        
        return {
            'forecast': _safe_positive(forecast_vals),
            'dates': dates,
            'mape': mape,
            'rmse': rmse,
            'accuracy': round(100 - mape, 2) if mape else None
        }
    except Exception as e:
        raise RuntimeError(f"XGBoost forecasting failed: {e}")


# ── Model registry ────────────────────────────────────────────────────────────

MODEL_REGISTRY = {
    'Prophet':                   _forecast_prophet,
    'ARIMA':                     _forecast_arima,
    'SARIMA':                    _forecast_sarima,
    'Exponential Smoothing':     _forecast_exp_smoothing,
    'Simple Exponential Smoothing': _forecast_simple_exp_smoothing,
    'Moving Average':            _forecast_moving_average,
    'Linear Regression':         _forecast_linear_regression,
    'XGBoost':                   _forecast_xgboost,
}


# ── Revenue forecasting helper ────────────────────────────────────────────────

def _forecast_revenue_series(df: pd.DataFrame, periods: int, dates: pd.DatetimeIndex,
                              model_name: str, sales_series: pd.Series) -> np.ndarray:
    """
    Forecast revenue using the same model as sales.
    Falls back to a revenue/sales ratio approach if model fails.
    """
    try:
        rev_series = _aggregate_to_series(df, 'revenue')
        # Align length with sales series
        rev_series = rev_series.reindex(sales_series.index, fill_value=0)
        result = MODEL_REGISTRY[model_name](rev_series, periods)
        return _safe_positive(result['forecast'][:len(dates)])
    except Exception:
        # Fallback: derive revenue from sales using historical ratio
        sales_agg = _aggregate_to_series(df, 'sales')
        rev_agg = _aggregate_to_series(df, 'revenue')
        ratio = (rev_agg.sum() / sales_agg.sum()) if sales_agg.sum() > 0 else 1.0
        sales_fc = MODEL_REGISTRY[model_name](_aggregate_to_series(df, 'sales'), periods)
        return _safe_positive(sales_fc['forecast'][:len(dates)] * ratio)


# ── Public API ────────────────────────────────────────────────────────────────

def forecast_sales(df: pd.DataFrame, periods: int = 6,
                   model_name: str = 'Moving Average') -> pd.DataFrame:
    """
    Forecast sales (and revenue) for `periods` steps ahead.

    Parameters
    ----------
    df          : DataFrame with at least 'date' and 'sales' columns.
                  Optionally 'revenue' and 'product' columns.
    periods     : Number of future periods to forecast.
    model_name  : One of the keys in MODEL_REGISTRY.

    Returns
    -------
    DataFrame with columns: date, forecast_sales, forecast_revenue
    """
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model '{model_name}'. "
                         f"Available: {list(MODEL_REGISTRY.keys())}")

    sales_series = _aggregate_to_series(df, 'sales')
    result = MODEL_REGISTRY[model_name](sales_series, periods)

    dates = result['dates']
    forecast_sales_vals = result['forecast'][:len(dates)]

    # Revenue
    if 'revenue' in df.columns:
        forecast_rev_vals = _forecast_revenue_series(
            df, periods, dates, model_name, sales_series)
    else:
        forecast_rev_vals = forecast_sales_vals.copy()

    return pd.DataFrame({
        'date': dates,
        'forecast_sales': np.round(forecast_sales_vals, 2),
        'forecast_revenue': np.round(forecast_rev_vals, 2)
    })


def evaluate_models(df: pd.DataFrame, periods: int = 6,
                    models_to_run: Optional[list] = None) -> dict:
    """
    Run all (or selected) models and return results + best model.

    Parameters
    ----------
    df            : DataFrame with 'date', 'sales', optionally 'revenue', 'product'.
    periods       : Forecast horizon.
    models_to_run : List of model names to evaluate. None = all available.

    Returns
    -------
    {
      'results': { model_name: { 'forecast': DataFrame, 'mape': float, 'rmse': float, ... } },
      'best_model': str,
      'best_accuracy': float
    }
    """
    if models_to_run is None:
        models_to_run = list(MODEL_REGISTRY.keys())
    else:
        # Validate names — unknown names are silently dropped with a warning
        valid = []
        for m in models_to_run:
            if m in MODEL_REGISTRY:
                valid.append(m)
            else:
                warnings.warn(f"Unknown model '{m}' — skipped.")
        models_to_run = valid

    if not models_to_run:
        raise ValueError("No valid models selected.")

    sales_series = _aggregate_to_series(df, 'sales')
    has_revenue = 'revenue' in df.columns

    results = {}
    errors = {}

    for model_name in models_to_run:
        try:
            # Sales forecast
            raw = MODEL_REGISTRY[model_name](sales_series, periods)
            dates = raw['dates']
            fc_sales = raw['forecast'][:len(dates)]

            # Revenue forecast
            if has_revenue:
                fc_rev = _forecast_revenue_series(df, periods, dates, model_name, sales_series)
            else:
                fc_rev = fc_sales.copy()

            forecast_df = pd.DataFrame({
                'date': dates,
                'forecast_sales': np.round(fc_sales, 2),
                'forecast_revenue': np.round(fc_rev, 2)
            })

            results[model_name] = {
                'forecast': forecast_df,
                'mape': raw.get('mape'),
                'rmse': raw.get('rmse'),
                'accuracy': raw.get('accuracy')
            }

        except Exception as e:
            errors[model_name] = str(e)

    # If nothing succeeded, raise with all error details
    if not results:
        err_detail = '\n'.join(f"  {m}: {e}" for m, e in errors.items())
        raise RuntimeError(
            f"All selected models failed. Details:\n{err_detail}\n\n"
            f"Tip: Ensure your data has at least 4-6 rows and a valid date column."
        )

    # Pick best model by lowest MAPE (None MAPE ranks last)
    def _mape_key(item):
        mape = item[1].get('mape')
        return mape if mape is not None else float('inf')

    sorted_results = sorted(results.items(), key=_mape_key)
    best_model = sorted_results[0][0]
    best_accuracy = results[best_model].get('accuracy')

    # Attach error info for models that failed (shown in UI)
    for model_name, err_msg in errors.items():
        results[model_name] = {
            'forecast': None,
            'mape': None,
            'rmse': None,
            'accuracy': None,
            'error': err_msg
        }

    return {
        'results': results,
        'best_model': best_model,
        'best_accuracy': best_accuracy
    }
