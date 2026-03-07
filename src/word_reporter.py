"""
Word Report Generator for Peak Sales Forecasts
Generates professional Word documents with peak analysis results
"""

import pandas as pd
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

def generate_peak_report(peak_df, forecast_results, forecast_periods):
    """
    Generate a professional Word document with peak predictions.
    
    Parameters:
    - peak_df: DataFrame with peak predictions
    - forecast_results: Dict with historical and forecast data for each product
    - forecast_periods: Number of forecast periods
    
    Returns:
    - Path to generated Word file
    """
    
    # Create document
    doc = Document()
    
    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # Title
    title = doc.add_paragraph()
    title_run = title.add_run('📊 Sales Peak Forecast Report')
    title_run.font.size = Pt(24)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(0, 51, 102)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Date
    date_para = doc.add_paragraph()
    date_run = date_para.add_run(f'Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}')
    date_run.font.size = Pt(10)
    date_run.font.italic = True
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()  # Spacing
    
    # Executive Summary
    doc.add_heading('Executive Summary', level=1)
    summary_text = doc.add_paragraph(
        f'This report presents peak sales forecasts for {len(peak_df)} product(s) based on '
        f'historical data analysis. The forecast covers {forecast_periods} months into the future. '
        'Peak predictions indicate when each product is expected to reach maximum sales performance.'
    )
    summary_text.paragraph_format.space_after = Pt(12)
    
    # Add spacing
    doc.add_paragraph()
    
    # Key Findings Section
    doc.add_heading('🎯 Key Findings', level=1)
    
    # Find products with highest growth
    top_product = peak_df.loc[peak_df['Growth'].idxmax()] if not peak_df.empty else None
    
    findings_list = [
        f"Total Products Analyzed: {len(peak_df)}",
        f"Reporting Period: {forecast_periods} months ahead",
        f"Report Generated: {datetime.now().strftime('%Y-%m-%d')}",
    ]
    
    if top_product is not None:
        findings_list.append(
            f"Highest Growth Expected: {top_product['Product']} "
            f"({top_product['Growth']:.1f}% growth)"
        )
    
    for finding in findings_list:
        doc.add_paragraph(finding, style='List Bullet')
    
    doc.add_paragraph()
    
    # Peak Predictions Table
    doc.add_heading('📋 Peak Predictions Summary', level=1)
    
    # Create table
    table = doc.add_table(rows=1, cols=5)
    table.style = 'Light Grid Accent 1'
    
    # Header row
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Product'
    hdr_cells[1].text = 'Peak Month'
    hdr_cells[2].text = 'Peak Sales Value'
    hdr_cells[3].text = 'Expected Growth'
    hdr_cells[4].text = 'Days Until Peak'
    
    # Make header bold
    for cell in hdr_cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
        shading_elm = OxmlElement('w:shd')
        shading_elm.set(qn('w:fill'), '003366')
        cell._element.get_or_add_tcPr().append(shading_elm)
    
    # Data rows
    for idx, row in peak_df.iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text = str(row['Product'])
        row_cells[1].text = str(row['Peak Month'])
        row_cells[2].text = f"{row['Peak Value']:.0f} units"
        row_cells[3].text = f"{row['Growth']:.1f}%"
        
        days = int(row['Days Until Peak'])
        if days > 0:
            row_cells[4].text = f"{days} days"
        else:
            row_cells[4].text = "Upcoming"
    
    # Set column widths
    for row in table.rows:
        row.cells[0].width = Inches(2.0)
        row.cells[1].width = Inches(1.5)
        row.cells[2].width = Inches(1.3)
        row.cells[3].width = Inches(1.2)
        row.cells[4].width = Inches(1.2)
    
    doc.add_paragraph()
    
    # Detailed Analysis for Each Product
    doc.add_heading('📊 Detailed Analysis by Product', level=1)
    doc.add_paragraph()
    
    for idx, (product, data) in enumerate(forecast_results.items(), 1):
        # Product section
        heading = doc.add_heading(f'{idx}. {product}', level=2)
        heading.paragraph_format.space_before = Pt(12)
        heading.paragraph_format.space_after = Pt(6)
        
        # Get peak info
        peak_info = peak_df[peak_df['Product'] == product].iloc[0]
        
        # Key metrics paragraph
        historical = data['historical']
        forecast = data['forecast']
        
        # Calculate metrics
        last_historical = historical['sales'].iloc[-1] if len(historical) > 0 else 0
        peak_value = peak_info['Peak Value']
        growth_pct = peak_info['Growth']
        
        # Insights paragraph
        insights_text = (
            f"Based on historical sales trends, {product} is expected to reach peak sales of "
            f"{peak_value:.0f} units in {peak_info['Peak Month']}. "
            f"This represents a {growth_pct:.1f}% increase from the most recent period "
            f"(current sales: {last_historical:.0f} units). "
        )
        
        if peak_info['Days Until Peak'] > 0:
            insights_text += (
                f"Peak performance is expected in approximately {int(peak_info['Days Until Peak'])} days."
            )
        else:
            insights_text += "Peak performance is expected soon based on the forecast trend."
        
        doc.add_paragraph(insights_text)
        
        # Key metrics
        doc.add_paragraph()
        metrics_text = doc.add_paragraph()
        metrics_text.add_run('Key Metrics:\n').bold = True
        metrics = [
            f"• Current Sales: {last_historical:.0f} units",
            f"• Predicted Peak: {peak_value:.0f} units",
            f"• Growth Rate: {growth_pct:.1f}%",
            f"• Peak Period: {peak_info['Peak Month']}",
            f"• Forecast Horizon: {forecast_periods} months",
            f"• Data Points Used: {len(historical)} historical records"
        ]
        
        for metric in metrics:
            doc.add_paragraph(metric, style='List Bullet')
        
        # Recommendation paragraph
        doc.add_paragraph()
        rec_heading = doc.add_paragraph()
        rec_heading.add_run('Recommendation:').bold = True
        
        if growth_pct > 20:
            recommendation = (
                f"With forecasted growth of {growth_pct:.1f}%, it is recommended to increase inventory "
                f"and marketing efforts for {product} leading up to {peak_info['Peak Month']}. "
                f"Prepare supply chain and resources to meet peak demand."
            )
        elif growth_pct > 0:
            recommendation = (
                f"{product} shows moderate growth potential ({growth_pct:.1f}%). "
                f"Monitor inventory levels and consider slight resource adjustments for peak demand in {peak_info['Peak Month']}."
            )
        else:
            recommendation = (
                f"{product} sales are expected to be stable. Monitor market conditions and "
                f"customer demand to adjust strategies as needed."
            )
        
        doc.add_paragraph(recommendation)
        doc.add_paragraph()  # Spacing between products
    
    # Methodology section
    doc.add_page_break()
    doc.add_heading('📚 Methodology & Notes', level=1)
    
    methodology_text = """
This report uses advanced time series forecasting models to predict future sales patterns based on 
historical data. The analysis employs Prophet, a robust forecasting framework that automatically 
captures trends, seasonality, and anomalies in the data.

Key Methodology Points:
• Historical data is analyzed to identify underlying trends and seasonal patterns
• Multiple forecasting models are evaluated to select the best fit for each product
• Peak values represent the maximum expected sales within the forecast period
• Growth percentages compare predicted peak sales to the most recent historical sales
• All forecasts come with built-in uncertainty estimates

Important Considerations:
• Forecasts are based on historical patterns and may be affected by unusual market events
• External factors (marketing campaigns, competitions, trends) may impact actual results
• Regular model retraining is recommended as new data becomes available
• Use these predictions as guidance for planning, not as absolute guarantees
    """
    
    doc.add_paragraph(methodology_text)
    
    # Footer with disclaimer
    doc.add_paragraph()
    doc.add_page_break()
    
    disclaimer = doc.add_paragraph()
    disclaimer.add_run('Disclaimer:').bold = True
    disclaimer_text = (
        "\n\nThis forecast report is generated using statistical models based on historical sales data. "
        "While every effort has been made to ensure accuracy, actual results may vary significantly from "
        "predictions due to unforeseen market conditions, business decisions, or external factors. "
        "This report should be used as one input among many when making business decisions. "
        "For questions or concerns about this analysis, please contact the data science team."
    )
    doc.add_paragraph(disclaimer_text, style='Normal')
    
    # Timestamp
    timestamp_para = doc.add_paragraph()
    timestamp_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    timestamp_run = timestamp_para.add_run(
        f'\nReport Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    )
    timestamp_run.font.size = Pt(9)
    timestamp_run.font.italic = True
    
    # Save document
    output_dir = 'reports'
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{output_dir}/Peak_Forecast_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    doc.save(filename)
    
    return filename


def generate_forecast_report(historical_data, forecast_data, best_model, best_accuracy, model_results, stats, periods):
    """
    Generate a professional Word document with sales/revenue forecast results.
    
    Parameters:
    - historical_data: dict with dates, sales, revenue lists
    - forecast_data: dict with dates, forecast_sales, forecast_revenue lists
    - best_model: str, name of best model
    - best_accuracy: float, accuracy percentage
    - model_results: dict with model performance data
    - stats: dict with historical statistics
    - periods: int, number of forecast periods
    
    Returns:
    - Path to generated Word file
    """
    
    # Create document
    doc = Document()
    
    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # Title
    title = doc.add_paragraph()
    title_run = title.add_run('Sales & Revenue Forecast Report')
    title_run.font.size = Pt(24)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(0, 51, 102)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Date
    date_para = doc.add_paragraph()
    date_run = date_para.add_run(f'Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}')
    date_run.font.size = Pt(10)
    date_run.font.italic = True
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    
    # Executive Summary
    doc.add_heading('Executive Summary', level=1)
    
    avg_sales = stats.get('avg_sales', 0)
    avg_revenue = stats.get('avg_revenue', 0)
    min_sales = stats.get('min_sales', 0)
    max_sales = stats.get('max_sales', 0)
    
    summary_text = doc.add_paragraph(
        f'This report presents sales and revenue forecasts based on historical data analysis. '
        f'The forecast covers {periods} periods into the future using {best_model} as the best performing model.'
    )
    summary_text.paragraph_format.space_after = Pt(12)
    
    # Key Findings
    doc.add_heading('Key Findings', level=1)
    
    findings = [
        f"Best Model: {best_model}",
        f"Model Accuracy: {best_accuracy}%",
        f"Forecast Periods: {periods}",
        f"Average Historical Sales: {avg_sales:,.2f}",
        f"Average Historical Revenue: {avg_revenue:,.2f}",
        f"Sales Range: {min_sales:,.2f} - {max_sales:,.2f}",
    ]
    
    for finding in findings:
        doc.add_paragraph(finding, style='List Bullet')
    
    doc.add_paragraph()
    
    # Historical Statistics
    doc.add_heading('Historical Data Statistics', level=1)
    
    stats_table = doc.add_table(rows=5, cols=2)
    stats_table.style = 'Light Grid Accent 1'
    
    stats_headers = stats_table.rows[0].cells
    stats_headers[0].text = 'Metric'
    stats_headers[1].text = 'Value'
    
    for cell in stats_headers:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
        shading_elm = OxmlElement('w:shd')
        shading_elm.set(qn('w:fill'), '003366')
        cell._element.get_or_add_tcPr().append(shading_elm)
    
    stats_data = [
        ('Average Sales', f'{avg_sales:,.2f}'),
        ('Average Revenue', f'{avg_revenue:,.2f}'),
        ('Minimum Sales', f'{min_sales:,.2f}'),
        ('Maximum Sales', f'{max_sales:,.2f}'),
    ]
    
    for i, (metric, value) in enumerate(stats_data):
        row = stats_table.rows[i + 1].cells
        row[0].text = metric
        row[1].text = value
    
    doc.add_paragraph()
    
    # Forecast Summary
    doc.add_heading('Forecast Summary', level=1)
    
    if forecast_data and 'forecast_sales' in forecast_data:
        forecast_sales = forecast_data['forecast_sales']
        forecast_revenue = forecast_data['forecast_revenue']
        
        forecast_avg_sales = sum(forecast_sales) / len(forecast_sales) if forecast_sales else 0
        forecast_avg_revenue = sum(forecast_revenue) / len(forecast_revenue) if forecast_revenue else 0
        forecast_max_sales = max(forecast_sales) if forecast_sales else 0
        
        doc.add_paragraph(f"Forecast Periods: {len(forecast_sales)}", style='List Bullet')
        doc.add_paragraph(f"Projected Average Sales: {forecast_avg_sales:,.2f}", style='List Bullet')
        doc.add_paragraph(f"Projected Average Revenue: {forecast_avg_revenue:,.2f}", style='List Bullet')
        doc.add_paragraph(f"Projected Peak Sales: {forecast_max_sales:,.2f}", style='List Bullet')
    
    doc.add_paragraph()
    
    # Model Performance Comparison
    doc.add_heading('Model Performance Comparison', level=1)
    
    if model_results:
        model_table = doc.add_table(rows=1, cols=4)
        model_table.style = 'Light Grid Accent 1'
        
        hdr_cells = model_table.rows[0].cells
        hdr_cells[0].text = 'Model'
        hdr_cells[1].text = 'Accuracy (%)'
        hdr_cells[2].text = 'MAPE (%)'
        hdr_cells[3].text = 'RMSE'
        
        for cell in hdr_cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
            shading_elm = OxmlElement('w:shd')
            shading_elm.set(qn('w:fill'), '003366')
            cell._element.get_or_add_tcPr().append(shading_elm)
        
        for model_name, model_data in model_results.items():
            row_cells = model_table.add_row().cells
            row_cells[0].text = model_name
            row_cells[1].text = str(model_data.get('accuracy', 'N/A'))
            row_cells[2].text = str(model_data.get('mape', 'N/A'))
            row_cells[3].text = str(model_data.get('rmse', 'N/A'))
    
    doc.add_paragraph()
    
    # Insights and Recommendations
    doc.add_heading('Insights & Recommendations', level=1)
    
    # Calculate growth potential
    if forecast_sales and historical_data.get('sales'):
        last_historical_sales = historical_data['sales'][-1] if historical_data['sales'] else 0
        avg_forecast_sales = sum(forecast_sales) / len(forecast_sales) if forecast_sales else 0
        
        if last_historical_sales > 0:
            growth_pct = ((avg_forecast_sales - last_historical_sales) / last_historical_sales) * 100
            
            if growth_pct > 10:
                recommendation = (
                    f"The forecast shows strong growth potential of {growth_pct:.1f}%. "
                    "Consider increasing inventory and marketing efforts to capitalize on the projected demand increase."
                )
            elif growth_pct > 0:
                recommendation = (
                    f"The forecast shows moderate growth of {growth_pct:.1f}%. "
                    "Monitor trends and prepare for slight increases in demand."
                )
            elif growth_pct > -10:
                recommendation = (
                    f"The forecast indicates stable demand with a slight change of {growth_pct:.1f}%. "
                    "Maintain current operational levels."
                )
            else:
                recommendation = (
                    f"The forecast shows a decline of {abs(growth_pct):.1f}%. "
                    "Consider promotional strategies to maintain sales volumes."
                )
            
            doc.add_paragraph(recommendation)
    
    # Methodology
    doc.add_page_break()
    doc.add_heading('Methodology', level=1)
    
    methodology = """
This report uses advanced time series forecasting models to predict future sales and revenue patterns.
The analysis evaluates multiple forecasting algorithms to select the best performing model based on accuracy metrics.

Models Evaluated:
- Prophet: Robust with seasonality handling
- ARIMA: Classic time series model
- Exponential Smoothing: Smooth trend estimation
- SARIMA: Seasonal ARIMA
- Moving Average: Simple trend following
- Simple Exponential Smoothing: Basic smoothing
- Linear Regression: Linear trend projection

Metrics Used:
- Accuracy: Overall prediction accuracy percentage
- MAPE: Mean Absolute Percentage Error
- RMSE: Root Mean Square Error
    """
    
    doc.add_paragraph(methodology)
    
    # Disclaimer
    doc.add_paragraph()
    disclaimer = doc.add_paragraph()
    disclaimer.add_run('Disclaimer:').bold = True
    doc.add_paragraph(
        "This forecast report is generated using statistical models based on historical data. "
        "Actual results may vary due to external factors. Use this report as guidance for planning purposes."
    )
    
    # Timestamp
    timestamp_para = doc.add_paragraph()
    timestamp_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    timestamp_run = timestamp_para.add_run(f'Report Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    timestamp_run.font.size = Pt(9)
    timestamp_run.font.italic = True
    
    # Save
    output_dir = 'reports'
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{output_dir}/Forecast_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    doc.save(filename)
    
    return filename
