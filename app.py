import streamlit as st
import pandas as pd
import numpy as np
from src.data_preprocessing import load_and_preprocess_data, detect_column_names
from src.forecasting import evaluate_models, MODEL_REGISTRY
from src.word_reporter import generate_forecast_report
import plotly.graph_objects as go
import plotly.express as px
import os
import altair as alt

st.set_page_config(page_title="Sales Forecasting Dashboard", layout="wide")
st.title(" Smart Sales and Revenue Forecasting Dashboard")

AVAILABLE_MODELS = list(MODEL_REGISTRY.keys())

if 'last_forecast_data' not in st.session_state:
    st.session_state.last_forecast_data = None

# ── Sidebar: Upload ────────────────────────────────────────────────────────────
st.sidebar.header(" Data Upload and Configuration")
uploaded_file = st.sidebar.file_uploader("Upload your historical sales data (CSV)", type="csv")

data = None
detected_cols = None

if uploaded_file is not None:
    try:
        temp_df = pd.read_csv(uploaded_file)
        detected_cols = detect_column_names(temp_df)

        st.sidebar.success(f"✓ File loaded: {uploaded_file.name}")
        st.sidebar.write("**Detected columns:**")
        c1, c2, c3, c4 = st.sidebar.columns(4)
        c1.caption(f" {detected_cols['date']}")
        c2.caption(f" {detected_cols['sales']}")
        c3.caption(f" {detected_cols.get('revenue') or '—'}")
        c4.caption(f" {detected_cols.get('product') or '—'}")

        with st.sidebar.expander("🔧 Override Column Names"):
            col_date    = st.text_input("Date column",    value=detected_cols['date'] or '')
            col_sales   = st.text_input("Sales column",   value=detected_cols['sales'] or '')
            col_revenue = st.text_input("Revenue column", value=detected_cols.get('revenue') or '')
            col_product = st.text_input("Product column (optional)", value=detected_cols.get('product') or '')

            detected_cols = {
                'date':    col_date    or detected_cols['date'],
                'sales':   col_sales   or detected_cols['sales'],
                'revenue': col_revenue or detected_cols.get('revenue'),
                'product': col_product or detected_cols.get('product') or None,
            }

        uploaded_file.seek(0)
        data = load_and_preprocess_data(
            uploaded_file,
            date_col=detected_cols['date'],
            sales_col=detected_cols['sales'],
            revenue_col=detected_cols.get('revenue'),
            product_col=detected_cols.get('product'),
        )

    except Exception as e:
        st.sidebar.error(f"❌ Error loading file: {e}")
        st.stop()
else:
    st.sidebar.info(" No file uploaded. Using sample data.")
    try:
        data = load_and_preprocess_data("data/sample_sales_data.csv")
        detected_cols = {'date': 'date', 'sales': 'sales', 'revenue': 'revenue', 'product': None}
    except FileNotFoundError:
        st.error("Sample data not found. Please upload a CSV file.")
        st.stop()

# ── Main Dashboard ─────────────────────────────────────────────────────────────
if data is not None:

    has_product = 'product' in data.columns
    all_products = sorted(data['product'].unique().tolist()) if has_product else []

    # ── Product Drill-Down ─────────────────────────────────────────────────────
    selected_product = None
    if has_product:
        st.sidebar.header("🔍 Product Drill-Down")
        label = st.sidebar.selectbox("Select Product", ["All Products"] + all_products)
        selected_product = None if label == "All Products" else label

    filtered_data = (
        data[data['product'] == selected_product].copy()
        if selected_product else data.copy()
    )

    # ── KPIs ───────────────────────────────────────────────────────────────────
    title_suffix = f" — {selected_product}" if selected_product else ""
    st.header(f"📊 Historical Data{title_suffix}")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Records",  len(filtered_data))
    k2.metric("Date Range",     f"{filtered_data['date'].min().date()} → {filtered_data['date'].max().date()}")
    k3.metric("Avg Sales",      f"${filtered_data['sales'].mean():,.2f}")
    k4.metric("Avg Revenue",    f"${filtered_data['revenue'].mean():,.2f}" if 'revenue' in filtered_data.columns else "N/A")
    st.dataframe(filtered_data.head(10), use_container_width=True)

    # ── Product Overview (All Products view) ──────────────────────────────────
    if has_product and not selected_product:
        st.header("📦 Product Overview")
        product_summary = (
            data.groupby('product')
            .agg(Total_Sales=('sales', 'sum'), Total_Revenue=('revenue', 'sum'),
                 Avg_Sales=('sales', 'mean'), Avg_Revenue=('revenue', 'mean'),
                 Records=('sales', 'count'))
            .reset_index().rename(columns={'product': 'Product'})
            .sort_values('Total_Revenue', ascending=False)
        )
        product_summary['Profit_Margin_%'] = (
            (product_summary['Total_Revenue'] - product_summary['Total_Sales'])
            / product_summary['Total_Revenue'] * 100
        ).round(2)
        st.dataframe(product_summary.style.format({
            'Total_Sales': '${:,.2f}', 'Total_Revenue': '${:,.2f}',
            'Avg_Sales': '${:,.2f}',  'Avg_Revenue': '${:,.2f}',
            'Profit_Margin_%': '{:.2f}%'
        }), use_container_width=True)

        c1, c2 = st.columns(2)
        c1.plotly_chart(px.bar(product_summary, x='Product', y='Total_Revenue',
            title='Revenue by Product', color='Total_Revenue',
            color_continuous_scale='Blues'), use_container_width=True)
        c2.plotly_chart(px.pie(product_summary, names='Product', values='Total_Sales',
            title='Sales Share by Product', hole=0.4), use_container_width=True)

        trend_data = data.groupby(['date', 'product'])['sales'].sum().reset_index()
        st.plotly_chart(px.line(trend_data, x='date', y='sales', color='product',
            title='Sales Trend per Product',
            labels={'sales': 'Sales ($)', 'date': 'Date', 'product': 'Product'}),
            use_container_width=True)

    # ── Sidebar: Forecast Config ───────────────────────────────────────────────
    st.sidebar.header("⚙️ Forecast Configuration")
    forecast_periods = st.sidebar.slider("Forecast periods", 1, 24, 6)

    st.sidebar.write("**Select Models:**")
    use_auto = st.sidebar.checkbox("Auto-optimize (test all models)", value=True)

    if use_auto:
        models_to_use = None          # None → evaluate_models runs all
        st.sidebar.info("✓ Will test all models and pick the best")
    else:
        models_to_use = st.sidebar.multiselect(
            "Choose models", AVAILABLE_MODELS,
            default=["Moving Average", "Linear Regression"]
        )
        if not models_to_use:
            st.sidebar.warning("⚠️ Select at least one model.")

    # ── Run Forecast ───────────────────────────────────────────────────────────
    run_disabled = (not use_auto) and (not models_to_use)
    if st.sidebar.button(" Generate Forecast", use_container_width=True,
                         disabled=run_disabled):
        try:
            with st.spinner("🔄 Running models…"):
                results = evaluate_models(
                    filtered_data,
                    periods=forecast_periods,
                    models_to_run=models_to_use   # None = all; list = selected
                )
                all_results   = results['results']
                best_model    = results['best_model']
                best_accuracy = results['best_accuracy']
                forecast_df   = all_results[best_model]['forecast']

            st.success("✅ Forecast generated successfully!")

            # ── Best model banner ──────────────────────────────────────────────
            st.header(f"📈 Best Model: {best_model}{title_suffix}")
            if best_accuracy:
                st.metric("Accuracy (MAPE)", f"{best_accuracy:.2f}%")

            # ── Model comparison table (shows failures too) ────────────────────
            st.subheader("📊 Model Comparison")
            comp_rows = []
            for model_name, result in all_results.items():
                if result.get('error'):
                    comp_rows.append({
                        'Model':  model_name,
                        'Status': '❌ Failed',
                        'MAPE':   '—',
                        'RMSE':   '—',
                        'Note':   result['error'][:90]
                    })
                else:
                    comp_rows.append({
                        'Model':  ('⭐ ' if model_name == best_model else '') + model_name,
                        'Status': '✅ OK',
                        'MAPE':   f"{result['mape']:.2f}%" if result.get('mape') else 'N/A',
                        'RMSE':   f"{result['rmse']:.2f}"  if result.get('rmse') else 'N/A',
                        'Note':   'Best model' if model_name == best_model else ''
                    })
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True)

            # ── Forecast table ─────────────────────────────────────────────────
            st.subheader("📋 Forecast Data")
            st.dataframe(forecast_df, use_container_width=True)

            # ── Charts ────────────────────────────────────────────────────────
            c1, c2 = st.columns(2)
            with c1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=filtered_data['date'], y=filtered_data['sales'],
                    mode='lines', name='Historical Sales', line=dict(color='#1f77b4', width=2)))
                fig.add_trace(go.Scatter(x=forecast_df['date'], y=forecast_df['forecast_sales'],
                    mode='lines+markers', name='Forecasted Sales',
                    line=dict(color='#ff7f0e', dash='dash', width=2), marker=dict(size=6)))
                fig.update_layout(title="Sales Forecast", xaxis_title="Date",
                                  yaxis_title="Sales ($)", hovermode='x unified', height=400)
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=filtered_data['date'], y=filtered_data['revenue'],
                    mode='lines', name='Historical Revenue', line=dict(color='#2ca02c', width=2)))
                fig2.add_trace(go.Scatter(x=forecast_df['date'], y=forecast_df['forecast_revenue'],
                    mode='lines+markers', name='Forecasted Revenue',
                    line=dict(color='#d62728', dash='dash', width=2), marker=dict(size=6)))
                fig2.update_layout(title="Revenue Forecast", xaxis_title="Date",
                                   yaxis_title="Revenue ($)", hovermode='x unified', height=400)
                st.plotly_chart(fig2, use_container_width=True)

            # ── Product profitability charts ───────────────────────────────────
            product_profit_summary = None
            product_trend_summary  = None

            if has_product and not selected_product:
                grp = data.groupby('product').agg(
                    Total_Sales=('sales', 'sum'),
                    Total_Revenue=('revenue', 'sum')
                ).reset_index()
                grp['Profit'] = grp['Total_Revenue'] - grp['Total_Sales']
                grp['Profit_Margin_%'] = (grp['Profit'] / grp['Total_Revenue'] * 100).round(2)
                product_profit_summary = grp.sort_values('Profit', ascending=False).to_dict('records')

                st.subheader("💰 Product Profitability")
                pc1, pc2 = st.columns(2)
                pc1.plotly_chart(px.bar(grp, x='product', y='Profit',
                    title='Total Profit by Product', color='Profit',
                    color_continuous_scale=['#d62728', '#2ca02c']), use_container_width=True)
                pc2.plotly_chart(px.bar(grp, x='product', y='Profit_Margin_%',
                    title='Profit Margin % by Product', color='Profit_Margin_%',
                    color_continuous_scale='RdYlGn'), use_container_width=True)

                # Trend summary
                trend_list = []
                for prod in all_products:
                    pd_ = data[data['product'] == prod].sort_values('date')
                    if len(pd_) >= 2:
                        h1 = pd_.iloc[:len(pd_)//2]['sales'].mean()
                        h2 = pd_.iloc[len(pd_)//2:]['sales'].mean()
                        g  = ((h2 - h1) / h1 * 100) if h1 else 0
                        trend_list.append({
                            'product':     prod,
                            'avg_sales':   round(pd_['sales'].mean(), 2),
                            'avg_revenue': round(pd_['revenue'].mean(), 2),
                            'growth_pct':  round(g, 2),
                            'trend': '📈 Growing' if g > 5 else ('📉 Declining' if g < -5 else '➡️ Stable')
                        })
                product_trend_summary = sorted(trend_list, key=lambda x: x['growth_pct'], reverse=True)

            # ── Store session state ────────────────────────────────────────────
            st.session_state.last_forecast_data = {
                'df': filtered_data, 'full_df': data,
                'forecast_results': all_results,
                'best_model': best_model, 'best_accuracy': best_accuracy,
                'periods': forecast_periods,
                'date_col': detected_cols['date'], 'sales_col': detected_cols['sales'],
                'selected_product': selected_product,
                'product_profit_summary': product_profit_summary,
                'product_trend_summary':  product_trend_summary,
                'has_product': has_product, 'all_products': all_products,
                'forecast_df': forecast_df,
            }

            # ── Report ────────────────────────────────────────────────────────
            st.subheader("📄 Generate Report")
            try:
                with st.spinner("Building Word report…"):
                    fdata = st.session_state.last_forecast_data
                    historical_data = {
                        'dates':   fdata['df']['date'].dt.strftime('%Y-%m-%d').tolist(),
                        'sales':   fdata['df']['sales'].round(2).tolist(),
                        'revenue': fdata['df']['revenue'].round(2).tolist()
                    }
                    forecast_data_for_report = {
                        'dates':            forecast_df['date'].dt.strftime('%Y-%m-%d').tolist(),
                        'forecast_sales':   forecast_df['forecast_sales'].round(2).tolist(),
                        'forecast_revenue': forecast_df['forecast_revenue'].round(2).tolist()
                    }
                    model_results_for_report = {
                        m: {'accuracy': r.get('accuracy'), 'mape': r.get('mape'), 'rmse': r.get('rmse')}
                        for m, r in all_results.items() if not r.get('error')
                    }
                    stats = {
                        'avg_sales':   float(fdata['df']['sales'].mean()),
                        'avg_revenue': float(fdata['df']['revenue'].mean()),
                        'min_sales':   float(fdata['df']['sales'].min()),
                        'max_sales':   float(fdata['df']['sales'].max()),
                    }
                    report_path = generate_forecast_report(
                        historical_data=historical_data,
                        forecast_data=forecast_data_for_report,
                        best_model=best_model,
                        best_accuracy=best_accuracy,
                        model_results=model_results_for_report,
                        stats=stats,
                        periods=forecast_periods,
                        selected_product=fdata.get('selected_product'),
                        product_profit_summary=fdata.get('product_profit_summary'),
                        product_trend_summary=fdata.get('product_trend_summary'),
                        has_product=fdata.get('has_product', False),
                    )
                with open(report_path, "rb") as f:
                    report_bytes = f.read()
                st.download_button(
                    label="📥 Download Word Report", data=report_bytes,
                    file_name=os.path.basename(report_path),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                st.success("✅ Report ready!")
            except Exception as e:
                st.error(f"❌ Report generation failed: {e}")

        except Exception as e:
            st.error(f"❌ Forecasting failed: {e}")
            st.info("Check that your data has at least 4+ rows and a valid date column.")

# ── Sidebar footer ────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
### 📋 Features
- Auto-detect date / sales / revenue / product columns
- Works with **or without** a product column
- Product drill-down — filter by individual product
- **{len(AVAILABLE_MODELS)} forecasting models** with graceful failure handling
- Model comparison table (shows errors for failed models)
- Sales & revenue charts
- Product profitability & trend analysis
- Downloadable Word report
""")
