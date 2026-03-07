from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
from src.data_preprocessing import load_and_preprocess_data, detect_column_names
from src.forecasting import forecast_sales, evaluate_models, recommend_best_model
from src.word_reporter import generate_peak_report, generate_forecast_report
import json
from werkzeug.utils import secure_filename
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'csv'}

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

# Global variable to store last forecast for report generation
last_forecast_data = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get list of available forecasting models"""
    return jsonify({
        'models': AVAILABLE_MODELS,
        'count': len(AVAILABLE_MODELS)
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only CSV files allowed'}), 400
        
        # Save and read file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read and detect columns
        df = pd.read_csv(filepath)
        detected = detect_column_names(df)
        
        # Get preview
        preview_df = df.head(10).to_dict('records')
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'columns': list(df.columns),
            'detected': detected,
            'preview': preview_df,
            'rows': len(df)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecast', methods=['POST'])
def run_forecast():
    try:
        data = request.json
        filepath = data.get('filepath')
        date_col = data.get('date_col')
        sales_col = data.get('sales_col')
        revenue_col = data.get('revenue_col')
        periods = int(data.get('periods', 6))
        auto_optimize = data.get('auto_optimize', True)
        selected_models = data.get('models', [])  # List of selected models
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'Invalid file path'}), 400
        
        # Load and preprocess
        df = load_and_preprocess_data(filepath, date_col, sales_col, revenue_col)
        
        if auto_optimize:
            # Evaluate multiple models and return all results
            if selected_models and len(selected_models) > 0:
                # Test only selected models
                results = evaluate_models(df, periods)
                # Filter to selected models
                all_results = {k: v for k, v in results['results'].items() if k in selected_models}
                best_model = results['best_model']
                best_accuracy = results['best_accuracy']
            else:
                # Test all available models
                results = evaluate_models(df, periods)
                all_results = results['results']
                best_model = results['best_model']
                best_accuracy = results['best_accuracy']
        else:
            # Use specific model
            model = data.get('model', 'Prophet')
            if model not in AVAILABLE_MODELS:
                return jsonify({'error': f'Unknown model: {model}'}), 400
                
            forecast_df = forecast_sales(df, periods, model, auto_config=True)
            best_model = model
            all_results = {model: {'forecast': forecast_df, 'accuracy': None}}
            best_accuracy = None
        
        # Get best forecast
        forecast_df = all_results[best_model]['forecast'] if best_model in all_results else list(all_results.values())[0]['forecast']
        
        # Prepare response
        historical_data = {
            'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'sales': df['sales'].round(2).tolist(),
            'revenue': df['revenue'].round(2).tolist()
        }
        
        forecast_data = {
            'dates': forecast_df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'sales': forecast_df['forecast_sales'].round(2).tolist(),
            'revenue': forecast_df['forecast_revenue'].round(2).tolist()
        }
        
        model_results = {}
        for model, result in all_results.items():
            model_results[model] = {
                'accuracy': result.get('accuracy'),
                'mape': result.get('mape'),
                'rmse': result.get('rmse')
            }
        
        # Store forecast data for report generation
        global last_forecast_data
        last_forecast_data = {
            'df': df,
            'forecast_results': all_results,
            'best_model': best_model,
            'best_accuracy': best_accuracy,
            'periods': periods,
            'date_col': date_col,
            'sales_col': sales_col
        }
        
        return jsonify({
            'success': True,
            'best_model': best_model,
            'best_accuracy': best_accuracy,
            'historical': historical_data,
            'forecast': forecast_data,
            'models': model_results,
            'stats': {
                'avg_sales': float(df['sales'].mean()),
                'avg_revenue': float(df['revenue'].mean()),
                'min_sales': float(df['sales'].min()),
                'max_sales': float(df['sales'].max())
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sample', methods=['POST'])
def load_sample():
    try:
        df = load_and_preprocess_data('data/sample_sales_data.csv')
        
        historical_data = {
            'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'sales': df['sales'].round(2).tolist(),
            'revenue': df['revenue'].round(2).tolist()
        }
        
        return jsonify({
            'success': True,
            'filename': 'sample_sales_data.csv',
            'filepath': 'data/sample_sales_data.csv',
            'data': historical_data,
            'rows': len(df),
            'stats': {
                'avg_sales': float(df['sales'].mean()),
                'avg_revenue': float(df['revenue'].mean())
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-report', methods=['POST'])
def create_report():
    try:
        global last_forecast_data
        
        if not last_forecast_data or 'df' not in last_forecast_data:
            return jsonify({'error': 'No forecast data available. Please run a forecast first.'}), 400
        
        df = last_forecast_data['df']
        all_results = last_forecast_data['forecast_results']
        best_model = last_forecast_data['best_model']
        best_accuracy = last_forecast_data['best_accuracy']
        periods = last_forecast_data['periods']
        
        # Get forecast data for best model
        if best_model in all_results:
            forecast_df = all_results[best_model]['forecast']
        else:
            forecast_df = list(all_results.values())[0]['forecast']
        
        # Prepare historical data
        historical_data = {
            'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'sales': df['sales'].round(2).tolist(),
            'revenue': df['revenue'].round(2).tolist()
        }
        
        # Prepare forecast data
        forecast_data = {
            'dates': forecast_df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'forecast_sales': forecast_df['forecast_sales'].round(2).tolist(),
            'forecast_revenue': forecast_df['forecast_revenue'].round(2).tolist()
        }
        
        # Get model results
        model_results = {}
        for model, result in all_results.items():
            model_results[model] = {
                'accuracy': result.get('accuracy'),
                'mape': result.get('mape'),
                'rmse': result.get('rmse')
            }
        
        # Stats
        stats = {
            'avg_sales': float(df['sales'].mean()),
            'avg_revenue': float(df['revenue'].mean()),
            'min_sales': float(df['sales'].min()),
            'max_sales': float(df['sales'].max())
        }
        
        # Generate report
        report_path = generate_forecast_report(
            historical_data=historical_data,
            forecast_data=forecast_data,
            best_model=best_model,
            best_accuracy=best_accuracy,
            model_results=model_results,
            stats=stats,
            periods=periods
        )
        
        return jsonify({
            'success': True,
            'report_file': os.path.basename(report_path),
            'message': 'Report generated successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-report/<filename>', methods=['GET'])
def download_report(filename):
    try:
        # Security: prevent directory traversal
        filename = secure_filename(filename)
        filepath = os.path.join('reports', filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Report not found'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, port=int(os.getenv('PORT', 5000)))
