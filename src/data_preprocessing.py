import pandas as pd
import numpy as np
from io import StringIO

def detect_column_names(df):
    """
    Auto-detect date, sales, and revenue columns.
    Returns a dict with mapped column names.
    """
    columns_lower = [col.lower() for col in df.columns]
    
    # Detect date column
    date_col = None
    for col in columns_lower:
        if any(term in col for term in ['date', 'time', 'day', 'month', 'year']):
            date_col = df.columns[columns_lower.index(col)]
            break
    
    # Detect sales column
    sales_col = None
    for col in columns_lower:
        if any(term in col for term in ['sales', 'quantity', 'qty', 'units', 'volume']):
            sales_col = df.columns[columns_lower.index(col)]
            break
    
    # Detect revenue column
    revenue_col = None
    for col in columns_lower:
        if any(term in col for term in ['revenue', 'income', 'amount', 'total', 'price']):
            revenue_col = df.columns[columns_lower.index(col)]
            break
    
    return {'date': date_col, 'sales': sales_col, 'revenue': revenue_col}

def load_and_preprocess_data(data_source, date_col=None, sales_col=None, revenue_col=None):
    """
    Load and preprocess historical business data.
    Auto-detects columns if not specified.
    
    Parameters:
    - data_source: file path or uploaded file
    - date_col: name of date column (auto-detected if None)
    - sales_col: name of sales column (auto-detected if None)
    - revenue_col: name of revenue column (auto-detected if None)
    """
    # Load data
    if isinstance(data_source, str):
        df = pd.read_csv(data_source)
    else:
        stringio = StringIO(data_source.getvalue().decode("utf-8"))
        df = pd.read_csv(stringio)
    
    # Auto-detect columns if not provided
    if date_col is None or sales_col is None or revenue_col is None:
        detected = detect_column_names(df)
        date_col = date_col or detected['date']
        sales_col = sales_col or detected['sales']
        revenue_col = revenue_col or detected['revenue']
    
    # Validate required columns
    if date_col not in df.columns:
        raise ValueError(f"Date column '{date_col}' not found in dataset. Available: {list(df.columns)}")
    if sales_col not in df.columns:
        raise ValueError(f"Sales column '{sales_col}' not found in dataset. Available: {list(df.columns)}")
    if revenue_col not in df.columns:
        raise ValueError(f"Revenue column '{revenue_col}' not found in dataset. Available: {list(df.columns)}")
    
    # Standardize column names
    df = df.rename(columns={date_col: 'date', sales_col: 'sales', revenue_col: 'revenue'})
    
    # Convert date to datetime
    try:
        df['date'] = pd.to_datetime(df['date'])
    except Exception as e:
        raise ValueError(f"Could not convert '{date_col}' to datetime: {str(e)}")
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Handle missing values (forward fill, then backward fill)
    df[['sales', 'revenue']] = df[['sales', 'revenue']].fillna(method='ffill').fillna(method='bfill')
    
    # Remove rows with any remaining NaN values
    df = df.dropna()
    
    if len(df) == 0:
        raise ValueError("No valid data rows after preprocessing")
    
    return df