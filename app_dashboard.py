import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')

from src.forecasting import forecast_sales, recommend_best_model
from src.data_preprocessing import load_and_preprocess_data
from src.word_reporter import generate_peak_report

# Page config
st.set_page_config(
    page_title="Sales and Revenue Forecasting System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding-top: 0rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Sales and Revenue Forecasting System")
st.markdown("---")

# Sidebar
st.sidebar.title("📁 Upload & Configure")

uploaded_file = st.sidebar.file_uploader(
    "Upload your sales data (CSV)",
    type="csv",
    help="CSV file should have Date, Product, and Sales columns"
)

if uploaded_file is not None:
    # Read the data
    try:
        df = pd.read_csv(uploaded_file)
        
        st.sidebar.success("✅ File uploaded successfully!")
        
        # Data preview
        st.sidebar.subheader("Data Preview")
        st.sidebar.dataframe(df.head(5), use_container_width=True)
        
        # Column selection
        st.sidebar.subheader("📋 Column Mapping")
        columns = list(df.columns)
        
        date_col = st.sidebar.selectbox("Select Date Column", columns)
        
        # Check if product column exists
        product_columns = [col for col in columns if col.lower() in ['product', 'item', 'product_name', 'item_name']]
        if product_columns:
            product_col = st.sidebar.selectbox("Select Product Column", columns, index=columns.index(product_columns[0]) if product_columns[0] in columns else 0)
        else:
            product_col = st.sidebar.selectbox("Select Product Column (Optional)", [None] + columns, index=0)
        
        sales_col = st.sidebar.selectbox("Select Sales/Quantity Column", columns)
        
        # Forecast periods
        forecast_periods = st.sidebar.slider(
            "Forecast Periods (months ahead)",
            min_value=3,
            max_value=24,
            value=6,
            step=1
        )
        
        # Model selection
        st.sidebar.subheader("🤖 Forecasting Model")
        
        # Auto-select toggle
        use_auto_model = st.sidebar.checkbox(
            "🎯 Auto-Select Best Model",
            value=True,
            help="Let the system analyze your data and recommend the most accurate model"
        )
        
        if use_auto_model:
            st.sidebar.info("System will analyze your data and select the best performing model automatically.")
            model_choice = None  # Will be determined automatically
        else:
            model_choice = st.sidebar.selectbox(
                "Select Forecasting Model Manually",
                [
                    "Prophet",
                    "ARIMA", 
                    "Exponential Smoothing",
                    "SARIMA",
                    "Moving Average",
                    "Simple Exponential Smoothing",
                    "Linear Regression"
                ],
                help="Choose the forecasting algorithm to use\\n\\n"
                     "• Prophet: Best for seasonal data\\n"
                     "• ARIMA: For statistical time series\\n"
                     "• Exponential Smoothing: Holt-Winters method\\n"
                     "• SARIMA: Seasonal ARIMA for seasonal patterns\\n"
                     "• Moving Average: Trend-based smoothing\\n"
                     "• Simple Exponential Smoothing: Basic exponential decay\\n"
                     "• Linear Regression: Simple trend extrapolation"
            )
        
        # Convert date column
        df[date_col] = pd.to_datetime(df[date_col])
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"📈 Sales & Revenue Forecast ({model_choice} Model)")
        
        with col2:
            if st.button("🎯 Analyze & Generate Report", key="analyze_btn"):
                st.session_state.analyze = True
            
            if st.button("📄 Export to Word", key="export_btn"):
                st.session_state.export = True
        
        st.markdown("---")
        
        # Process data
        if product_col and product_col in df.columns:
            products = df[product_col].unique()
            st.info(f"📦 Found {len(products)} products: {', '.join(map(str, products[:5]))}{('...' if len(products) > 5 else '')}")
        else:
            products = ["All"]
            df['Product'] = 'All'
            product_col = 'Product'
        
        # Forecast results storage
        forecast_results = {}
        peak_predictions = []
        
        # Process each product
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, product in enumerate(products):
            status_text.text(f"Processing {product}... ({idx+1}/{len(products)})")
            
            # Filter data for product
            if products[0] != "All":
                product_data = df[df[product_col] == product].copy()
            else:
                product_data = df.copy()
            
            if len(product_data) < 3:
                st.warning(f"⚠️ Insufficient data for {product}")
                continue
            
            # Prepare data
            product_data = product_data[[date_col, sales_col]].copy()
            product_data.columns = ['date', 'sales']
            product_data['revenue'] = product_data['sales'].values
            product_data = product_data.sort_values('date').reset_index(drop=True)
            
            # Auto-select best model if enabled
            selected_model = model_choice
            model_info = None
            
            if use_auto_model:
                try:
                    model_info = recommend_best_model(product_data, forecast_periods, test_size=0.2)
                    selected_model = model_info['best_model']
                except Exception as e:
                    st.warning(f"⚠️ Could not auto-select model for {product}, using Prophet: {str(e)}")
                    selected_model = "Prophet"
            
            # Forecast
            try:
                forecast_df = forecast_sales(product_data, forecast_periods, selected_model, auto_config=True)
                
                # Store results
                forecast_results[product] = {
                    'historical': product_data,
                    'forecast': forecast_df,
                    'model': selected_model,
                    'model_info': model_info
                }
                
                # Find peak
                max_forecast_value = forecast_df['sales'].max()
                max_forecast_date = forecast_df[forecast_df['sales'] == max_forecast_value]['date'].iloc[0]
                max_forecast_idx = forecast_df[forecast_df['sales'] == max_forecast_value].index[0]
                
                peak_predictions.append({
                    'Product': product,
                    'Peak Month': max_forecast_date.strftime('%B %Y'),
                    'Peak Value': max_forecast_value,
                    'Days Until Peak': (max_forecast_date - datetime.now()).days,
                    'Growth': ((max_forecast_value - product_data['sales'].iloc[-1]) / product_data['sales'].iloc[-1] * 100) if product_data['sales'].iloc[-1] > 0 else 0
                })
                
            except Exception as e:
                st.warning(f"❌ Could not forecast {product}: {str(e)}")
            
            progress_bar.progress((idx + 1) / len(products))
        
        progress_bar.empty()
        status_text.empty()
        
        if forecast_results:
            # Display Peak Predictions Summary
            st.subheader("🎯 Peak Predictions Summary")
            
            peak_df = pd.DataFrame(peak_predictions)
            
            # Display as formatted table
            cols = st.columns(len(peak_predictions)) if len(peak_predictions) <= 3 else [st.container()]
            
            for idx, row in peak_df.iterrows():
                if len(peak_predictions) <= 3:
                    with cols[idx]:
                        st.metric(
                            label=f"📦 {row['Product']}",
                            value=row['Peak Month'],
                            delta=f"{row['Growth']:.1f}% growth" if row['Growth'] != 0 else "Stable"
                        )
                        st.caption(f"Peak Sales: {row['Peak Value']:.0f}")
                else:
                    st.write(f"### {row['Product']}")
                    st.write(f"**Peak Month:** {row['Peak Month']}")
                    st.write(f"**Peak Sales:** {row['Peak Value']:.0f}")
                    st.write(f"**Growth:** {row['Growth']:.1f}%")
            
            st.markdown("---")
            
            # Detailed Forecasts
            if use_auto_model:
                st.subheader("📊 Sales & Revenue Forecasts (Auto-Selected Models)")
            else:
                st.subheader(f"📊 Sales & Revenue Forecasts ({model_choice} Model)")
            
            # Tabs for each product
            if len(products) > 1:
                tabs = st.tabs([f"📦 {p}" for p in forecast_results.keys()])
                for tab, product in enumerate(forecast_results.keys()):
                    with tabs[tab]:
                        display_product_forecast(product, forecast_results[product], peak_predictions)
            else:
                for product in forecast_results.keys():
                    display_product_forecast(product, forecast_results[product], peak_predictions)
            
            # Export functionality
            st.markdown("---")
            st.subheader("📄 Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📥 Export Peak Analysis to Word", use_container_width=True):
                    try:
                        # Generate Word report
                        word_file = generate_peak_report(
                            peak_df, 
                            forecast_results,
                            forecast_periods
                        )
                        
                        # Download button
                        with open(word_file, 'rb') as f:
                            st.download_button(
                                label="⬇️ Download Report (Word)",
                                data=f.read(),
                                file_name=f"Peak_Forecast_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                        st.success("✅ Word report generated successfully!")
                    except Exception as e:
                        st.error(f"❌ Error generating report: {str(e)}")
            
            with col2:
                # Export to CSV
                csv = peak_df.to_csv(index=False)
                st.download_button(
                    label="📥 Export Peak Predictions (CSV)",
                    data=csv,
                    file_name=f"Peak_Predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        else:
            st.error("❌ No forecasts could be generated. Please check your data.")
    
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.info("Please ensure your CSV has proper Date, Product, and Sales columns.")

else:
    # Welcome screen
    st.info("""
    ### 👋 Welcome to Sales and Revenue Forecasting System!
    
    Advanced forecasting system that predicts sales and revenue trends for your products using machine learning.
    
    **How to use:**
    1. 📁 Upload a CSV file with your historical sales data
    2. 📋 Map your columns (Date, Product, Sales)
    3. 🤖 Choose your forecasting model (Prophet, ARIMA, or Linear Regression)
    4. 🎯 Get automatic peak predictions and revenue forecasts
    5. 📄 Export detailed analysis to a professional Word document
    
    **Required columns in your CSV:**
    - **Date**: Transaction date (any standard date format)
    - **Product**: Product or item name
    - **Sales**: Sales quantity or revenue values
    
    **Example CSV format:**
    ```
    Date,Product,Sales
    2023-01-01,Product A,150
    2023-02-01,Product A,165
    2023-01-01,Product B,200
    ```
    """)
    
    st.markdown("---")
    
    # Sample data
    st.subheader("📊 Sample Data Format")
    sample_data = {
        'Date': ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01'],
        'Product': ['Product A', 'Product A', 'Product B', 'Product B'],
        'Sales': [150, 165, 200, 215]
    }
    st.dataframe(pd.DataFrame(sample_data), use_container_width=True)
    
    st.markdown("---")
    st.markdown("""
    **Key Features:**
    - 🤖 Multiple forecasting models (Prophet, ARIMA, Linear Regression)
    - 📈 Interactive visual forecasts and trend analysis
    - 📊 Multi-product sales and revenue analysis
    - 🎯 Automatic peak prediction and growth analysis
    - 📄 Professional Word report export
    - 💡 Data-driven business insights and recommendations
    """)

def display_product_forecast(product, data, peak_predictions):
    """Display forecast visualization for a product"""
    historical = data['historical']
    forecast = data['forecast']
    model_used = data.get('model', 'Unknown')
    model_info = data.get('model_info', None)
    
    # Display model information if available
    if model_info:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "🤖 Selected Model",
                model_used
            )
        
        with col2:
            st.metric(
                "📊 Forecast Accuracy",
                f"{model_info['accuracy']:.1f}%"
            )
        
        with col3:
            st.metric(
                "✨ Data Pattern",
                "Seasonal" if model_info['characteristics'].get('has_seasonality') else 
                "Trending" if model_info['characteristics'].get('has_trend') else 
                "Stable"
            )
        
        # Show why this model was selected
        with st.expander("📖 Why this model was selected?"):
            st.info(f"**Reason:** {model_info['reason']}")
            
            # Show data characteristics
            st.write("**Data Characteristics:**")
            chars = model_info['characteristics']
            char_text = f"""
            - Data Points: {chars.get('length', 'N/A')}
            - Trend Strength: {'Strong ⬆️' if chars.get('has_trend') else 'Weak ➡️'}
            - Seasonality: {'Present 📈' if chars.get('has_seasonality') else 'None ➡️'}
            - Volatility: {'High 📊' if chars.get('is_noisy') else 'Low ✅'}
            """
            st.markdown(char_text)
            
            # Show model comparison
            if model_info.get('model_accuracies'):
                st.write("**Model Accuracy Comparison:**")
                comparisons = model_info['model_accuracies']
                # Sort by accuracy descending
                sorted_models = sorted(comparisons.items(), key=lambda x: x[1], reverse=True)
                
                comparison_df = pd.DataFrame([
                    {'Model': m[0], 'Accuracy': f"{m[1]:.1f}%", 'Status': '✅ Selected' if m[0] == model_used else ''}
                    for m in sorted_models
                ])
                st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # Find peak info
    peak_info = [p for p in peak_predictions if p['Product'] == product][0]
    
    # Create figure
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=historical['date'],
        y=historical['sales'],
        mode='lines+markers',
        name='Historical Sales',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    # Forecast data
    fig.add_trace(go.Scatter(
        x=forecast['date'],
        y=forecast['sales'],
        mode='lines+markers',
        name='Forecasted Sales',
        line=dict(color='#ff7f0e', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    # Peak point
    peak_row = forecast[forecast['date'].dt.strftime('%B %Y') == peak_info['Peak Month']].iloc[0] if len(forecast[forecast['date'].dt.strftime('%B %Y') == peak_info['Peak Month']]) > 0 else forecast.loc[forecast['sales'].idxmax()]
    
    fig.add_trace(go.Scatter(
        x=[peak_row['date']],
        y=[peak_row['sales']],
        mode='markers',
        name='Predicted Peak',
        marker=dict(size=15, color='#2ca02c', symbol='star'),
        text=f"Peak: {peak_info['Peak Month']}<br>Value: {peak_row['sales']:.0f}",
        hovertemplate='%{text}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=f"📈 {product} - Sales Forecast ({model_used} Model)",
        xaxis_title="Date",
        yaxis_title="Sales",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Peak info box
    with st.container():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "🎯 Peak Month",
                peak_info['Peak Month'],
            )
        
        with col2:
            st.metric(
                "📊 Peak Sales",
                f"{peak_info['Peak Value']:.0f}",
                f"{peak_info['Growth']:.1f}% growth"
            )
        
        with col3:
            days = peak_info['Days Until Peak']
            if days > 0:
                st.metric("⏰ Days Until Peak", f"{days} days")
            else:
                st.metric("⏰ Peak Status", "Upcoming")

