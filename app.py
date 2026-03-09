import streamlit as st
import pandas as pd
import numpy as np
from src.data_preprocessing import load_and_preprocess_data, detect_column_names
from src.forecasting import forecast_sales, evaluate_models
from src.word_reporter import generate_forecast_report
import plotly.graph_objects as go
import os
import altair as alt

st.set_page_config(page_title="Sales Forecasting Dashboard", layout="wide")
st.title("🚀 Smart Sales and Revenue Forecasting Dashboard")

# Available forecasting models
AVAILABLE_MODELS = [
    'Prophet',
    'ARIMA', 
    'Exponential Smoothing',
    'SARIMA',
    'Moving Average',
    'Simple Exponential Smoothing',
    'Linear Regression'
]

# Initialize session state
if 'last_forecast_data' not in st.session_state:
    st.session_state.last_forecast_data = None

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
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", len(data))
    with col2:
        st.metric("Date Range", f"{data['date'].min().date()} to {data['date'].max().date()}")
    with col3:
        st.metric("Avg Sales", f"${data['sales'].mean():.2f}")
    with col4:
        st.metric("Avg Revenue", f"${data['revenue'].mean():.2f}")
    
    st.dataframe(data.head(10), use_container_width=True)
    
    # Forecast configuration
    st.sidebar.header("⚙️ Forecast Configuration")
    forecast_periods = st.sidebar.slider("Forecast periods", 1, 24, 6)
    
    # Model selection
    st.sidebar.write("**Select Models to Compare:**")
    use_auto_optimize = st.sidebar.checkbox("Auto-optimize (test all models)", value=True)
    
    if use_auto_optimize:
        models_to_use = AVAILABLE_MODELS
        st.sidebar.info("✓ Will test all models and pick the best")
    else:
        models_to_use = st.sidebar.multiselect(
            "Choose models",
            AVAILABLE_MODELS,
            default=["Prophet", "ARIMA"]
        )
    
    auto_config = st.sidebar.checkbox("Auto-configure model parameters", value=True)
    
    # Run forecast
    if st.sidebar.button("🚀 Generate Forecast", use_container_width=True):
        try:
            with st.spinner("🔄 Evaluating models and generating forecast..."):
                if use_auto_optimize:
                    # Test all models
                    results = evaluate_models(data, forecast_periods)
                    all_results = results['results']
                    best_model = results['best_model']
                    best_accuracy = results['best_accuracy']
                else:
                    # Test selected models
                    if not models_to_use:
                        st.error("Please select at least one model")
                        st.stop()
                    
                    results = evaluate_models(data, forecast_periods)
                    all_results = {k: v for k, v in results['results'].items() if k in models_to_use}
                    best_model = results['best_model'] if results['best_model'] in all_results else models_to_use[0]
                    best_accuracy = results['best_accuracy']
                
                # Get best forecast
                forecast_df = all_results[best_model]['forecast']
                
                # Store in session for report generation
                st.session_state.last_forecast_data = {
                    'df': data,
                    'forecast_results': all_results,
                    'best_model': best_model,
                    'best_accuracy': best_accuracy,
                    'periods': forecast_periods,
                    'date_col': detected_cols['date'],
                    'sales_col': detected_cols['sales']
                }
            
            st.success("✅ Forecast generated successfully!")
            
            # Display best model info
            st.header(f"📈 Best Model: {best_model}")
            if best_accuracy:
                st.metric("Accuracy (MAPE)", f"{best_accuracy:.2f}%")
            
            # Model comparison table
            st.subheader("📊 Model Comparison")
            comparison_data = []
            for model, result in all_results.items():
                comparison_data.append({
                    'Model': model,
                    'Accuracy (MAPE)': f"{result.get('mape', 'N/A'):.2f}%" if result.get('mape') else 'N/A',
                    'RMSE': f"{result.get('rmse', 'N/A'):.2f}" if result.get('rmse') else 'N/A'
                })
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)
            
            # Forecast results
            st.subheader("📋 Forecast Data")
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
                    yaxis_title="Sales ($)",
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
                    yaxis_title="Revenue ($)",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # Report generation
            if st.session_state.last_forecast_data:
                st.subheader("📄 Generate Report")
                
                try:
                    with st.spinner("Generating report..."):
                        forecast_data_dict = st.session_state.last_forecast_data
                        
                        historical_data = {
                            'dates': forecast_data_dict['df']['date'].dt.strftime('%Y-%m-%d').tolist(),
                            'sales': forecast_data_dict['df']['sales'].round(2).tolist(),
                            'revenue': forecast_data_dict['df']['revenue'].round(2).tolist()
                        }
                        
                        forecast_data_for_report = {
                            'dates': forecast_df['date'].dt.strftime('%Y-%m-%d').tolist(),
                            'forecast_sales': forecast_df['forecast_sales'].round(2).tolist(),
                            'forecast_revenue': forecast_df['forecast_revenue'].round(2).tolist()
                        }
                        
                        model_results = {}
                        for model, result in all_results.items():
                            model_results[model] = {
                                'accuracy': result.get('accuracy'),
                                'mape': result.get('mape'),
                                'rmse': result.get('rmse')
                            }
                        
                        stats = {
                            'avg_sales': float(forecast_data_dict['df']['sales'].mean()),
                            'avg_revenue': float(forecast_data_dict['df']['revenue'].mean()),
                            'min_sales': float(forecast_data_dict['df']['sales'].min()),
                            'max_sales': float(forecast_data_dict['df']['sales'].max())
                        }
                        
                        report_path = generate_forecast_report(
                            historical_data=historical_data,
                            forecast_data=forecast_data_for_report,
                            best_model=best_model,
                            best_accuracy=best_accuracy,
                            model_results=model_results,
                            stats=stats,
                            periods=forecast_periods
                        )
                        
                        # Read file and create download button
                        with open(report_path, "rb") as f:
                            report_bytes = f.read()
                        
                        st.download_button(
                            label="📥 Download Word Report",
                            data=report_bytes,
                            file_name=os.path.basename(report_path),
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                        st.success("✅ Report generated successfully!")
                except Exception as e:
                    st.error(f"❌ Report generation failed: {str(e)}")
                    st.info(f"Error details: {str(e)}")
            
        except Exception as e:
            st.error(f"❌ Forecasting failed: {str(e)}")
            st.info("Try a different model or check your data format.")

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
    ### 📋 Features
    - **Auto-detect** date, sales, and revenue columns
    - **Support** any CSV format
    - **{len(AVAILABLE_MODELS)} forecasting models** available
    - **Model comparison** with accuracy metrics
    - **Flexible** forecast periods
    - **Download reports** as Word documents
    - **Error handling** for invalid data
""")