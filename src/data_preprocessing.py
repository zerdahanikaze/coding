import pandas as pd
import numpy as np
from typing import Optional


def detect_column_names(df: pd.DataFrame) -> dict:
    """
    Auto-detect date, sales, revenue, and product column names from a DataFrame.
    Returns a dict with keys: 'date', 'sales', 'revenue', 'product'.
    """
    columns_lower = {col.lower(): col for col in df.columns}

    # Date detection
    date_keywords = ['date', 'time', 'period', 'month', 'year', 'week', 'day', 'timestamp']
    date_col = None
    for kw in date_keywords:
        for col_lower, col_orig in columns_lower.items():
            if kw in col_lower:
                date_col = col_orig
                break
        if date_col:
            break

    # Sales detection
    sales_keywords = ['sales', 'units', 'quantity', 'qty', 'sold', 'volume', 'orders']
    sales_col = None
    for kw in sales_keywords:
        for col_lower, col_orig in columns_lower.items():
            if kw in col_lower:
                sales_col = col_orig
                break
        if sales_col:
            break

    # Revenue detection
    revenue_keywords = ['revenue', 'income', 'amount', 'value', 'price', 'total', 'earnings']
    revenue_col = None
    for kw in revenue_keywords:
        for col_lower, col_orig in columns_lower.items():
            if kw in col_lower and col_orig != sales_col:
                revenue_col = col_orig
                break
        if revenue_col:
            break

    # Product detection
    product_keywords = ['product', 'item', 'sku', 'category', 'brand', 'name', 'goods', 'service']
    product_col = None
    for kw in product_keywords:
        for col_lower, col_orig in columns_lower.items():
            if kw in col_lower and col_orig not in [date_col, sales_col, revenue_col]:
                product_col = col_orig
                break
        if product_col:
            break

    return {
        'date': date_col,
        'sales': sales_col,
        'revenue': revenue_col,
        'product': product_col
    }


def load_and_preprocess_data(
    filepath,
    date_col: Optional[str] = None,
    sales_col: Optional[str] = None,
    revenue_col: Optional[str] = None,
    product_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Load and preprocess sales data from a CSV file or file-like object.
    Standardises column names to: date, sales, revenue, (optionally) product.
    """
    if hasattr(filepath, 'read'):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_csv(filepath)

    # Auto-detect if not provided
    if not all([date_col, sales_col, revenue_col]):
        detected = detect_column_names(df)
        date_col = date_col or detected['date']
        sales_col = sales_col or detected['sales']
        revenue_col = revenue_col or detected['revenue']
        if product_col is None:
            product_col = detected['product']

    if not date_col or not sales_col:
        raise ValueError("Could not detect date or sales columns. Please specify them manually.")

    # Build column rename map
    rename_map = {}
    if date_col and date_col != 'date':
        rename_map[date_col] = 'date'
    if sales_col and sales_col != 'sales':
        rename_map[sales_col] = 'sales'
    if revenue_col and revenue_col != 'revenue':
        rename_map[revenue_col] = 'revenue'
    if product_col and product_col != 'product':
        rename_map[product_col] = 'product'

    df = df.rename(columns=rename_map)

    # Parse date
    df['date'] = pd.to_datetime(df['date'], infer_datetime_format=True)

    # Ensure numeric
    df['sales'] = pd.to_numeric(df['sales'], errors='coerce')
    if 'revenue' in df.columns:
        df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce')
    else:
        # Derive revenue from sales if missing (assume 1:1)
        df['revenue'] = df['sales']

    # Handle product column
    if product_col:
        df['product'] = df['product'].astype(str).str.strip()
    # (if no product column, we just don't include one)

    # Drop rows with missing critical values
    df = df.dropna(subset=['date', 'sales'])
    df = df.sort_values('date').reset_index(drop=True)

    # Select output columns
    keep_cols = ['date', 'sales', 'revenue']
    if product_col and 'product' in df.columns:
        keep_cols.append('product')
    # Keep any extra columns as well
    extra_cols = [c for c in df.columns if c not in keep_cols]
    df = df[keep_cols + extra_cols]

    return df
