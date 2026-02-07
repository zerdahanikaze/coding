import pandas as pd
import numpy as np
from io import StringIO

def load_and_preprocess_data(data_source):
    """
    Load and preprocess historical business data.
    Adapts to CSV files with date, sales, and revenue columns.
    """
    if isinstance(data_source, str):
        # File path
        df = pd.read_csv(data_source)
    else:
        # Uploaded file
        stringio = StringIO(data_source.getvalue().decode("utf-8"))
        df = pd.read_csv(stringio)
    
    # Assume columns: date, sales, revenue
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Handle missing values (simple forward fill)
    df = df.fillna(method='ffill')
    
    return df