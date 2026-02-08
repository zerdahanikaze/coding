import streamlit as st
import pandas as pd
import numpy as np
from src.data_preprocessing import load_and_preprocess_data, detect_column_names
from src.forecasting import forecast_sales
import plotly.graph_objects as go

st.set_page_config(page_title="Sales Forecasting Dashboard", layout="wide")
st.title("Smart Sales and Revenue Forecasting Dashboard")

# Sidebar for inputs
st.sidebar.header("📊 Data Upload and Configuration")
uploaded_file = st.sidebar.file_uploader("Upload your historical sales data (CSV)", type="csv")

data = None
detected_cols = None

if uploaded_file is not None:
    try:
        # Read and show available columns
        temp_df = pd.read_csv(uploaded_file)
        detected_cols = detect_column_names(temp_df)
        
        st.sidebar.success(f"✓ File loaded: {uploaded_file.name}")
        st.sidebar.write("**Detected columns:**")
        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            st.write(f"📅 Date: {detected_cols['date']}")
        with col2:
            st.write(f"📈 Sales: {detected_cols['sales']}")
        with col3:
            st.write(f"💰 Revenue: {detected_cols['revenue']}")
        
        # Allow manual override if needed
        with st.sidebar.expander("🔧 Custom Column Names"):
            col_date = st.text_input("Date column", value=detected_cols['date'] or '')
            col_sales = st.text_input("Sales column", value=detected_cols['sales'] or '')
            col_revenue = st.text_input("Revenue column", value=detected_cols['revenue'] or '')
            
            detected_cols = {
                'date': col_date if col_date else detected_cols['date'],
                'sales': col_sales if col_sales else detected_cols['sales'],
                'revenue': col_revenue if col_revenue else detected_cols['revenue']
            }
        
        # Load and preprocess data
        uploaded_file.seek(0)  # Reset file pointer
        data = load_and_preprocess_data(
            uploaded_file,
            date_col=detected_cols['date'],
            sales_col=detected_cols['sales'],
            revenue_col=detected_cols['revenue']
        )
        
    except Exception as e:
        st.sidebar.error(f"❌ Error loading file: {str(e)}")
        st.stop()
else:
    st.sidebar.info("💡 No file uploaded. Using sample data.")
    try:
        data = load_and_preprocess_data("data/sample_sales_data.csv")
    except FileNotFoundError:
        st.error("Sample data not found. Please upload a CSV file.")
        st.stop()

# Display data
if data is not None:
    st.header("📊 Historical Data")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", len(data))
    with col2:
        st.metric("Date Range", f"{data['date'].min().date()} to {data['date'].max().date()}")
    with col3:
        st.metric("Avg Sales", f"{data['sales'].mean():.2f}")
    
    st.dataframe(data.head(10), use_container_width=True)
    
    # Forecast configuration
    st.sidebar.header("⚙️ Forecast Configuration")
    forecast_periods = st.sidebar.slider("Forecast periods", 1, 24, 6)
    model_choice = st.sidebar.selectbox(
        "Choose Forecasting Model",
        ["ARIMA", "Prophet", "Linear Regression"],
        help="ARIMA: Good for stationary data\nProphet: Good for seasonal patterns\nLinear Regression: Good for trends"
    )
    
    auto_config = st.sidebar.checkbox("Auto-configure model parameters", value=True, help="Let the system find best parameters")
    
    # Run forecast
    if st.sidebar.button("🚀 Generate Forecast", use_container_width=True):
        try:
            with st.spinner(f"🔄 Generating forecast using {model_choice}..."):
                forecast_df = forecast_sales(data, forecast_periods, model_choice, auto_config=auto_config)
            
            st.header("📈 Forecast Results")
            st.dataframe(forecast_df, use_container_width=True)
            
            # Visualizations side by side
            col1, col2 = st.columns(2)
            
            with col1:
                # Sales forecast
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data['date'], y=data['sales'],
                    mode='lines', name='Historical Sales',
                    line=dict(color='#1f77b4', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=forecast_df['date'], y=forecast_df['forecast_sales'],
                    mode='lines+markers', name='Forecasted Sales',
                    line=dict(color='#ff7f0e', dash='dash', width=2),
                    marker=dict(size=6)
                ))
                fig.update_layout(
                    title="Sales Forecast",
                    xaxis_title="Date",
                    yaxis_title="Sales",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Revenue forecast
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=data['date'], y=data['revenue'],
                    mode='lines', name='Historical Revenue',
                    line=dict(color='#2ca02c', width=2)
                ))
                fig2.add_trace(go.Scatter(
                    x=forecast_df['date'], y=forecast_df['forecast_revenue'],
                    mode='lines+markers', name='Forecasted Revenue',
                    line=dict(color='#d62728', dash='dash', width=2),
                    marker=dict(size=6)
                ))
                fig2.update_layout(
                    title="Revenue Forecast",
                    xaxis_title="Date",
                    yaxis_title="Revenue",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            st.success("✅ Forecast generated successfully!")
            
        except Exception as e:
            st.error(f"❌ Forecasting failed: {str(e)}")
            st.info("Try a different model or check your data format.")

st.sidebar.markdown("---")
st.sidebar.markdown("""
    ### 📋 Features
    - **Auto-detect** date, sales, and revenue columns
    - **Support** any CSV format
    - **Multiple** forecasting models
    - **Flexible** forecast periods
    - **Error handling** for invalid data
""")