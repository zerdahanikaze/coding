import streamlit as st
import pandas as pd
import numpy as np
from src.data_preprocessing import load_and_preprocess_data
from src.forecasting import forecast_sales
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

st.title("Smart Sales and Revenue Forecasting Dashboard")

# Sidebar for inputs
st.sidebar.header("Data Upload and Configuration")
uploaded_file = st.sidebar.file_uploader("Upload your historical sales data (CSV)", type="csv")

if uploaded_file is not None:
    data = load_and_preprocess_data(uploaded_file)
else:
    st.sidebar.write("Using sample data")
    data = load_and_preprocess_data("data/sample_sales_data.csv")

# Display data
st.header("Historical Data")
st.dataframe(data.head())

# Forecast configuration
st.sidebar.header("Forecast Configuration")
forecast_periods = st.sidebar.slider("Forecast periods (months)", 1, 24, 12)
model_choice = st.sidebar.selectbox("Choose Forecasting Model", ["ARIMA", "Prophet", "Linear Regression"])

# Run forecast
if st.sidebar.button("Generate Forecast"):
    with st.spinner("Generating forecast..."):
        forecast_df = forecast_sales(data, forecast_periods, model_choice)
    
    st.header("Forecast Results")
    st.dataframe(forecast_df)
    
    # Visualization
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['date'], y=data['sales'], mode='lines', name='Historical Sales'))
    fig.add_trace(go.Scatter(x=forecast_df['date'], y=forecast_df['forecast_sales'], mode='lines', name='Forecasted Sales', line=dict(dash='dash')))
    fig.update_layout(title="Sales Forecast", xaxis_title="Date", yaxis_title="Sales")
    st.plotly_chart(fig)
    
    # Revenue forecast
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=data['date'], y=data['revenue'], mode='lines', name='Historical Revenue'))
    fig2.add_trace(go.Scatter(x=forecast_df['date'], y=forecast_df['forecast_revenue'], mode='lines', name='Forecasted Revenue', line=dict(dash='dash')))
    fig2.update_layout(title="Revenue Forecast", xaxis_title="Date", yaxis_title="Revenue")
    st.plotly_chart(fig2)

st.sidebar.markdown("---")
st.sidebar.write("This dashboard adapts to any business data with date, sales, and revenue columns.")