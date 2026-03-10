"""
Word report generator for Sales Forecasting Dashboard.
Generates a .docx report using the docx npm package via Node.js.
"""
import os
import json
import subprocess
import tempfile
from datetime import datetime
from typing import Optional


def generate_forecast_report(
    historical_data: dict,
    forecast_data: dict,
    best_model: str,
    best_accuracy,
    model_results: dict,
    stats: dict,
    periods: int,
    selected_product: Optional[str] = None,
    product_profit_summary: Optional[list] = None,
    product_trend_summary: Optional[list] = None,
    has_product: bool = False
) -> str:
    """
    Generate a Word (.docx) forecast report.
    Returns the path to the generated file.
    """
    output_dir = tempfile.mkdtemp()
    output_path = os.path.join(output_dir, f"forecast_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx")

    # ── Compute summary numbers ────────────────────────────────────────────────
    total_forecast_sales = sum(forecast_data.get('forecast_sales', []))
    total_forecast_revenue = sum(forecast_data.get('forecast_revenue', []))
    avg_forecast_sales = total_forecast_sales / max(len(forecast_data.get('forecast_sales', [1])), 1)
    avg_forecast_revenue = total_forecast_revenue / max(len(forecast_data.get('forecast_revenue', [1])), 1)

    hist_sales = historical_data.get('sales', [])
    hist_revenue = historical_data.get('revenue', [])
    sales_growth = ((avg_forecast_sales - stats['avg_sales']) / stats['avg_sales'] * 100) if stats['avg_sales'] else 0
    revenue_growth = ((avg_forecast_revenue - (sum(hist_revenue) / max(len(hist_revenue), 1))) /
                      (sum(hist_revenue) / max(len(hist_revenue), 1)) * 100) if hist_revenue else 0

    # ── Prepare model comparison rows ─────────────────────────────────────────
    model_rows_js = []
    for model_name, result in model_results.items():
        mape = f"{result['mape']:.2f}%" if result.get('mape') else 'N/A'
        rmse = f"{result['rmse']:.2f}" if result.get('rmse') else 'N/A'
        is_best = model_name == best_model
        model_rows_js.append({'model': model_name, 'mape': mape, 'rmse': rmse, 'is_best': is_best})

    # ── Prepare forecast table rows ────────────────────────────────────────────
    forecast_rows_js = []
    for i, (d, s, r) in enumerate(zip(
        forecast_data.get('dates', []),
        forecast_data.get('forecast_sales', []),
        forecast_data.get('forecast_revenue', [])
    )):
        forecast_rows_js.append({'date': d, 'sales': f"${s:,.2f}", 'revenue': f"${r:,.2f}"})

    # ── Product profitability rows ─────────────────────────────────────────────
    product_profit_rows_js = []
    top_product = None
    if product_profit_summary:
        top_product = product_profit_summary[0]
        for p in product_profit_summary:
            product_profit_rows_js.append({
                'product': p['product'],
                'total_sales': f"${p['Total_Sales']:,.2f}",
                'total_revenue': f"${p['Total_Revenue']:,.2f}",
                'profit': f"${p['Profit']:,.2f}",
                'margin': f"{p['Profit_Margin_%']:.2f}%",
                'is_top': p['product'] == top_product['product']
            })

    # ── Product trend rows ────────────────────────────────────────────────────
    product_trend_rows_js = []
    if product_trend_summary:
        for t in product_trend_summary:
            product_trend_rows_js.append({
                'product': t['product'],
                'avg_sales': f"${t['avg_sales']:,.2f}",
                'avg_revenue': f"${t['avg_revenue']:,.2f}",
                'growth_pct': f"{t['growth_pct']:+.2f}%",
                'trend': t['trend']
            })

    # ── Build the JavaScript for docx generation ──────────────────────────────
    report_title = f"Sales & Revenue Forecast Report" + (f" — {selected_product}" if selected_product else "")
    generated_on = datetime.now().strftime("%B %d, %Y at %H:%M")
    accuracy_text = f"{best_accuracy:.2f}%" if best_accuracy else "N/A"

    js_code = f"""
const {{ Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
         HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
         VerticalAlign, LevelFormat, PageNumber, PageBreak }} = require('docx');
const fs = require('fs');

// ── Helpers ──────────────────────────────────────────────────────────────────
const COLORS = {{
  primary: '1E3A5F',
  accent: '2E86C1',
  light_blue: 'D6EAF8',
  green: '1E8449',
  light_green: 'D5F5E3',
  red: 'C0392B',
  light_red: 'FADBD8',
  orange: 'D35400',
  light_orange: 'FDEBD0',
  yellow_bg: 'FEF9E7',
  grey_bg: 'F2F3F4',
  white: 'FFFFFF',
  dark_text: '1C2833',
  mid_grey: '7F8C8D',
  border: 'BDC3C7',
}};

const border = {{ style: BorderStyle.SINGLE, size: 1, color: COLORS.border }};
const borders = {{ top: border, bottom: border, left: border, right: border }};
const noBorder = {{ style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }};
const noBorders = {{ top: noBorder, bottom: noBorder, left: noBorder, right: noBorder }};

function hCell(text, widthDxa, bgColor = COLORS.primary) {{
  return new TableCell({{
    borders,
    width: {{ size: widthDxa, type: WidthType.DXA }},
    shading: {{ fill: bgColor, type: ShadingType.CLEAR }},
    margins: {{ top: 80, bottom: 80, left: 120, right: 120 }},
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({{
      alignment: AlignmentType.CENTER,
      children: [new TextRun({{ text, bold: true, color: COLORS.white, size: 20, font: 'Arial' }})]
    }})]
  }});
}}

function dCell(text, widthDxa, bgColor = COLORS.white, bold = false, color = COLORS.dark_text) {{
  return new TableCell({{
    borders,
    width: {{ size: widthDxa, type: WidthType.DXA }},
    shading: {{ fill: bgColor, type: ShadingType.CLEAR }},
    margins: {{ top: 80, bottom: 80, left: 120, right: 120 }},
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({{
      alignment: AlignmentType.CENTER,
      children: [new TextRun({{ text: String(text), bold, color, size: 18, font: 'Arial' }})]
    }})]
  }});
}}

function sectionHeading(text) {{
  return new Paragraph({{
    heading: HeadingLevel.HEADING_1,
    spacing: {{ before: 360, after: 160 }},
    children: [new TextRun({{ text, bold: true, color: COLORS.primary, size: 28, font: 'Arial' }})]
  }});
}}

function subHeading(text) {{
  return new Paragraph({{
    heading: HeadingLevel.HEADING_2,
    spacing: {{ before: 240, after: 120 }},
    children: [new TextRun({{ text, bold: true, color: COLORS.accent, size: 24, font: 'Arial' }})]
  }});
}}

function bodyPara(text, spacing_before = 80) {{
  return new Paragraph({{
    spacing: {{ before: spacing_before, after: 80 }},
    children: [new TextRun({{ text, size: 20, font: 'Arial', color: COLORS.dark_text }})]
  }});
}}

function kpiBox(label, value, bgColor) {{
  return new Table({{
    width: {{ size: 2200, type: WidthType.DXA }},
    columnWidths: [2200],
    rows: [
      new TableRow({{ children: [
        new TableCell({{
          borders: noBorders,
          width: {{ size: 2200, type: WidthType.DXA }},
          shading: {{ fill: bgColor, type: ShadingType.CLEAR }},
          margins: {{ top: 120, bottom: 120, left: 160, right: 160 }},
          children: [
            new Paragraph({{ alignment: AlignmentType.CENTER, children: [
              new TextRun({{ text: value, bold: true, size: 28, color: COLORS.primary, font: 'Arial' }})
            ]}}),
            new Paragraph({{ alignment: AlignmentType.CENTER, children: [
              new TextRun({{ text: label, size: 16, color: COLORS.mid_grey, font: 'Arial' }})
            ]}})
          ]
        }})
      ]}})
    ]
  }});
}}

// ── Data ─────────────────────────────────────────────────────────────────────
const modelRows = {json.dumps(model_rows_js)};
const forecastRows = {json.dumps(forecast_rows_js)};
const productProfitRows = {json.dumps(product_profit_rows_js)};
const productTrendRows = {json.dumps(product_trend_rows_js)};
const hasProduct = {str(has_product).lower()};
const selectedProduct = {json.dumps(selected_product)};
const topProduct = {json.dumps(top_product)};

// ── Document Children ─────────────────────────────────────────────────────────
const children = [];

// Cover block
children.push(new Paragraph({{
  spacing: {{ before: 480, after: 80 }},
  alignment: AlignmentType.CENTER,
  children: [new TextRun({{ text: '{report_title}', bold: true, size: 40, color: COLORS.primary, font: 'Arial' }})]
}}));
children.push(new Paragraph({{
  spacing: {{ before: 80, after: 80 }},
  alignment: AlignmentType.CENTER,
  children: [new TextRun({{ text: 'AI-Powered Sales Intelligence Report', size: 22, color: COLORS.mid_grey, font: 'Arial' }})]
}}));
children.push(new Paragraph({{
  spacing: {{ before: 80, after: 80 }},
  alignment: AlignmentType.CENTER,
  children: [new TextRun({{ text: 'Generated on {generated_on}', size: 18, color: COLORS.mid_grey, font: 'Arial', italics: true }})]
}}));
children.push(new Paragraph({{ spacing: {{ before: 80, after: 80 }}, children: [new TextRun('')] }}));
// Divider
children.push(new Paragraph({{
  spacing: {{ before: 0, after: 320 }},
  border: {{ bottom: {{ style: BorderStyle.SINGLE, size: 6, color: COLORS.accent, space: 1 }} }},
  children: []
}}));

// ── 1. Executive Summary ──────────────────────────────────────────────────────
children.push(sectionHeading('1. Executive Summary'));
const summaryText = selectedProduct
  ? `This report presents a ${{periods}}-period sales and revenue forecast for the product "${{selectedProduct}}", ` +
    `generated using the ${{'{best_model}'}} model (MAPE: {accuracy_text}). ` +
    `Forecasted average sales are $${{ {avg_forecast_sales:.2f} .toFixed(2)}} and average revenue is $${{ {avg_forecast_revenue:.2f} .toFixed(2)}} per period.`
  : `This report presents a ${{periods}}-period sales and revenue forecast across all products, ` +
    `generated using the best-performing ${{'{best_model}'}} model (MAPE: {accuracy_text}). ` +
    `Forecasted average sales are ${avg_forecast_sales:.2f} and average revenue is ${avg_forecast_revenue:.2f} per period.`;

children.push(bodyPara(
  `This report presents a {periods}-period sales and revenue forecast` +
  (selectedProduct ? ` for product "${{selectedProduct}}"` : ' across all products') +
  `, generated using the best-performing model: {best_model} (Accuracy MAPE: {accuracy_text}). ` +
  `Forecasted average sales stand at ${avg_forecast_sales:,.2f} and average revenue at ${avg_forecast_revenue:,.2f} per period, ` +
  `reflecting a ${{'{sales_growth:.1f}%'}} growth trend vs historical averages.`
));

// KPI row (use a table for side-by-side layout)
children.push(new Paragraph({{ spacing: {{ before: 160, after: 80 }}, children: [] }}));
children.push(new Table({{
  width: {{ size: 9360, type: WidthType.DXA }},
  columnWidths: [2340, 2340, 2340, 2340],
  rows: [new TableRow({{ children: [
    dCell('${avg_forecast_sales:,.0f}\\nForecast Avg Sales', 2340, COLORS.light_blue, true, COLORS.primary),
    dCell('${avg_forecast_revenue:,.0f}\\nForecast Avg Revenue', 2340, COLORS.light_green, true, COLORS.green),
    dCell('{sales_growth:+.1f}%\\nSales Growth', 2340, {'COLORS.light_green' if sales_growth >= 0 else 'COLORS.light_red'}, true, {'COLORS.green' if sales_growth >= 0 else 'COLORS.red'}),
    dCell('{periods} Periods\\nForecast Horizon', 2340, COLORS.light_orange, true, COLORS.orange),
  ]}})]
}}));
children.push(new Paragraph({{ spacing: {{ before: 80, after: 80 }}, children: [] }}));

// ── 2. Historical Data Summary ────────────────────────────────────────────────
children.push(sectionHeading('2. Historical Data Summary'));
children.push(bodyPara(`Historical dataset contains {len(hist_sales)} records. Average sales: ${stats['avg_sales']:,.2f} | Average revenue: ${sum(hist_revenue)/max(len(hist_revenue),1):,.2f} | Min sales: ${stats['min_sales']:,.2f} | Max sales: ${stats['max_sales']:,.2f}.`));

// ── 3. Model Performance ──────────────────────────────────────────────────────
children.push(sectionHeading('3. Model Performance Comparison'));
children.push(bodyPara('The following table shows all evaluated forecasting models ranked by accuracy (MAPE — Mean Absolute Percentage Error). Lower MAPE = better accuracy. The winning model is highlighted.'));
children.push(new Paragraph({{ spacing: {{ before: 120, after: 80 }}, children: [] }}));

const modelTableRows = [
  new TableRow({{ children: [hCell('Model', 4680), hCell('MAPE (Accuracy)', 2340), hCell('RMSE', 2340)] }})
];
modelRows.forEach(r => {{
  const bg = r.is_best ? COLORS.light_green : COLORS.white;
  const bold = r.is_best;
  modelTableRows.push(new TableRow({{ children: [
    dCell(r.model + (r.is_best ? ' ★ Best' : ''), 4680, bg, bold),
    dCell(r.mape, 2340, bg, bold),
    dCell(r.rmse, 2340, bg, bold),
  ]}}));
}});
children.push(new Table({{ width: {{ size: 9360, type: WidthType.DXA }}, columnWidths: [4680, 2340, 2340], rows: modelTableRows }}));

// ── 4. Forecast Results ───────────────────────────────────────────────────────
children.push(new Paragraph({{ spacing: {{ before: 80, after: 80 }}, children: [] }}));
children.push(sectionHeading('4. Forecast Results'));
children.push(bodyPara(`Forecast generated for {periods} periods using the {best_model} model. Sales and revenue projections are shown below.`));
children.push(new Paragraph({{ spacing: {{ before: 120, after: 80 }}, children: [] }}));

const forecastTableRows = [
  new TableRow({{ children: [hCell('Period / Date', 3120), hCell('Forecast Sales ($)', 3120), hCell('Forecast Revenue ($)', 3120)] }})
];
forecastRows.forEach((r, i) => {{
  const bg = i % 2 === 0 ? COLORS.white : COLORS.grey_bg;
  forecastTableRows.push(new TableRow({{ children: [
    dCell(r.date, 3120, bg),
    dCell(r.sales, 3120, bg),
    dCell(r.revenue, 3120, bg),
  ]}}));
}});
children.push(new Table({{ width: {{ size: 9360, type: WidthType.DXA }}, columnWidths: [3120, 3120, 3120], rows: forecastTableRows }}));

// ── 5. Product Profitability Analysis (conditional) ───────────────────────────
if (hasProduct && productProfitRows.length > 0 && !selectedProduct) {{
  children.push(new Paragraph({{ spacing: {{ before: 80, after: 80 }}, children: [] }}));
  children.push(sectionHeading('5. Product Profitability Analysis'));

  const topName = topProduct ? topProduct.product : '';
  const topProfit = topProduct ? '$' + topProduct.Profit.toFixed(2) : '';
  const topMargin = topProduct ? topProduct['Profit_Margin_%'].toFixed(2) + '%' : '';

  children.push(bodyPara(
    topProduct
      ? `Across all products, "${{topName}}" leads in profitability with a total profit of ${{topProfit}} and a margin of ${{topMargin}}. ` +
        `Products are ranked below from most to least profitable. Use this analysis to prioritise marketing, inventory, and pricing strategies.`
      : 'Product profitability breakdown across all products is shown below.'
  ));

  // Highlight box for top product
  if (topProduct) {{
    children.push(new Paragraph({{ spacing: {{ before: 120, after: 80 }}, children: [] }}));
    children.push(new Table({{
      width: {{ size: 9360, type: WidthType.DXA }},
      columnWidths: [9360],
      rows: [new TableRow({{ children: [new TableCell({{
        borders: noBorders,
        width: {{ size: 9360, type: WidthType.DXA }},
        shading: {{ fill: COLORS.light_green, type: ShadingType.CLEAR }},
        margins: {{ top: 120, bottom: 120, left: 200, right: 200 }},
        children: [
          new Paragraph({{ alignment: AlignmentType.CENTER, children: [
            new TextRun({{ text: '🏆 Top Performing Product', bold: true, size: 22, color: COLORS.green, font: 'Arial' }})
          ]}}),
          new Paragraph({{ alignment: AlignmentType.CENTER, children: [
            new TextRun({{ text: `${{topName}}  |  Profit: ${{topProfit}}  |  Margin: ${{topMargin}}`, size: 20, color: COLORS.dark_text, font: 'Arial' }})
          ]}})
        ]
      }})]}})]
    }}));
  }}

  children.push(new Paragraph({{ spacing: {{ before: 160, after: 80 }}, children: [] }}));
  const profitTableRows = [
    new TableRow({{ children: [
      hCell('Product', 2600), hCell('Total Sales', 1690), hCell('Total Revenue', 1690),
      hCell('Profit', 1690), hCell('Margin %', 1690)
    ]}})
  ];
  productProfitRows.forEach((r, i) => {{
    const bg = r.is_top ? COLORS.light_green : (i % 2 === 0 ? COLORS.white : COLORS.grey_bg);
    const bold = r.is_top;
    profitTableRows.push(new TableRow({{ children: [
      dCell(r.product + (r.is_top ? ' ★' : ''), 2600, bg, bold),
      dCell(r.total_sales, 1690, bg, bold),
      dCell(r.total_revenue, 1690, bg, bold),
      dCell(r.profit, 1690, bg, bold),
      dCell(r.margin, 1690, bg, bold),
    ]}}));
  }});
  children.push(new Table({{
    width: {{ size: 9360, type: WidthType.DXA }},
    columnWidths: [2600, 1690, 1690, 1690, 1690],
    rows: profitTableRows
  }}));
}}

// ── 6. Product Sales Trend Review (conditional) ───────────────────────────────
if (hasProduct && productTrendRows.length > 0 && !selectedProduct) {{
  children.push(new Paragraph({{ spacing: {{ before: 80, after: 80 }}, children: [] }}));
  children.push(sectionHeading('6. Product Sales Trend Review'));
  children.push(bodyPara(
    'This section reviews the historical sales trend for each product by comparing the first half vs the second half of the available data period. ' +
    'Growth rate is calculated as the percentage change in average sales between the two halves, providing an early signal of momentum.'
  ));
  children.push(new Paragraph({{ spacing: {{ before: 120, after: 80 }}, children: [] }}));

  const trendTableRows = [
    new TableRow({{ children: [
      hCell('Product', 2600), hCell('Avg Sales', 1690), hCell('Avg Revenue', 1690),
      hCell('Growth Rate', 1690), hCell('Trend Signal', 1690)
    ]}})
  ];
  productTrendRows.forEach((r, i) => {{
    const growth = parseFloat(r.growth_pct);
    const bg = growth > 5 ? COLORS.light_green : (growth < -5 ? COLORS.light_red : (i % 2 === 0 ? COLORS.white : COLORS.grey_bg));
    const bold = Math.abs(growth) > 5;
    trendTableRows.push(new TableRow({{ children: [
      dCell(r.product, 2600, bg, bold),
      dCell(r.avg_sales, 1690, bg),
      dCell(r.avg_revenue, 1690, bg),
      dCell(r.growth_pct, 1690, bg, bold),
      dCell(r.trend, 1690, bg, bold),
    ]}}));
  }});
  children.push(new Table({{
    width: {{ size: 9360, type: WidthType.DXA }},
    columnWidths: [2600, 1690, 1690, 1690, 1690],
    rows: trendTableRows
  }}));

  // Legend note
  children.push(new Paragraph({{ spacing: {{ before: 120, after: 80 }},
    children: [new TextRun({{
      text: 'Legend: 📈 Growing = >+5% growth  |  📉 Declining = >-5% decline  |  ➡️ Stable = within ±5%',
      size: 16, italics: true, color: COLORS.mid_grey, font: 'Arial'
    }})]
  }}));
}}

// ── 7. Recommendations ───────────────────────────────────────────────────────
const recSection = hasProduct && productProfitRows.length > 0 ? '7' : '5';
children.push(new Paragraph({{ spacing: {{ before: 80, after: 80 }}, children: [] }}));
children.push(sectionHeading(`${{recSection}}. Recommendations`));

const recItems = [
  `Model Selection: Continue using {best_model} for future forecasts given its superior accuracy (MAPE: {accuracy_text}).`,
  `Forecast Horizon: The current {periods}-period forecast is suitable for near-term planning. For longer-term strategy, consider extending to 12-24 periods.`,
];
if (hasProduct && topProduct) {{
  recItems.push(`Product Focus: Prioritise "${{topProduct.product}}" in marketing and inventory planning — it delivers the highest profitability.`);
  recItems.push('Declining Products: Investigate products flagged as Declining in the Trend Review and consider promotional actions or discontinuation.');
}}
recItems.push('Data Quality: Ensure historical data is consistently updated to maintain forecast accuracy over time.');
recItems.push('Review Cycle: Re-run this forecast monthly or after any major business event to keep projections current.');

recItems.forEach(item => {{
  children.push(new Paragraph({{
    spacing: {{ before: 80, after: 60 }},
    numbering: {{ reference: 'bullets', level: 0 }},
    children: [new TextRun({{ text: item, size: 20, font: 'Arial', color: COLORS.dark_text }})]
  }}));
}});

// ── Footer note ───────────────────────────────────────────────────────────────
children.push(new Paragraph({{ spacing: {{ before: 360, after: 80 }},
  border: {{ top: {{ style: BorderStyle.SINGLE, size: 1, color: COLORS.border, space: 1 }} }},
  children: [new TextRun({{
    text: 'This report was automatically generated by the Smart Sales Forecasting Dashboard. ' +
          'Forecasts are statistical estimates and should be used as a guide alongside business judgment.',
    size: 16, italics: true, color: COLORS.mid_grey, font: 'Arial'
  }})]
}}));

// ── Assemble Document ─────────────────────────────────────────────────────────
const doc = new Document({{
  numbering: {{
    config: [{{
      reference: 'bullets',
      levels: [{{ level: 0, format: LevelFormat.BULLET, text: '\\u2022',
        alignment: AlignmentType.LEFT,
        style: {{ paragraph: {{ indent: {{ left: 720, hanging: 360 }} }} }}
      }}]
    }}]
  }},
  styles: {{
    default: {{ document: {{ run: {{ font: 'Arial', size: 20 }} }} }},
    paragraphStyles: [
      {{ id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: {{ size: 28, bold: true, font: 'Arial' }},
        paragraph: {{ spacing: {{ before: 360, after: 160 }}, outlineLevel: 0 }} }},
      {{ id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: {{ size: 24, bold: true, font: 'Arial' }},
        paragraph: {{ spacing: {{ before: 240, after: 120 }}, outlineLevel: 1 }} }},
    ]
  }},
  sections: [{{
    properties: {{
      page: {{
        size: {{ width: 12240, height: 15840 }},
        margin: {{ top: 1440, right: 1440, bottom: 1440, left: 1440 }}
      }}
    }},
    children
  }}]
}});

Packer.toBuffer(doc).then(buf => {{
  fs.writeFileSync('{output_path.replace(os.sep, "/")}', buf);
  console.log('SUCCESS');
}}).catch(err => {{
  console.error('ERROR:', err.message);
  process.exit(1);
}});
"""

    # Write JS to temp file and run
    js_path = os.path.join(output_dir, 'gen_report.js')
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_code)

    # Ensure docx is installed
    subprocess.run(['npm', 'install', '-g', 'docx'], capture_output=True)

    result = subprocess.run(
        ['node', js_path],
        capture_output=True, text=True, timeout=60
    )

    if result.returncode != 0 or not os.path.exists(output_path):
        raise RuntimeError(
            f"Report generation failed.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

    return output_path
