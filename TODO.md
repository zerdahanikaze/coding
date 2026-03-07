# TODO: Complete Dashboard Report Generation Feature

## Steps to Complete:

- [ ] 1. Modify `src/word_reporter.py` - Add `generate_forecast_report()` function for single-series sales/revenue data
- [ ] 2. Modify `dashboard.py` - Add `/api/generate-report` and `/api/download-report/<filename>` endpoints
- [ ] 3. Modify `templates/index.html` - Add "Generate Report" button and download functionality
- [ ] 4. Test the complete flow

## Implementation Details:

### 1. word_reporter.py - New function: generate_forecast_report()
- Takes historical data, forecast data, best model info, and stats
- Generates a professional Word document with:
  - Executive summary
  - Historical statistics
  - Forecast summary
  - Model performance comparison
  - Key insights and recommendations

### 2. dashboard.py - New endpoints:
- POST `/api/generate-report` - Generates Word report from last forecast data
- GET `/api/download-report/<filename>` - Downloads generated report

### 3. index.html - New UI elements:
- "Generate Report" button in the button group
- Download functionality for the generated report

