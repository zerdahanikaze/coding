from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from src.data_preprocessing import load_and_preprocess_data, detect_column_names
from src.forecasting import forecast_sales, evaluate_models
import json
from werkzeug.utils import secure_filename
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

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
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'Invalid file path'}), 400
        
        # Load and preprocess
        df = load_and_preprocess_data(filepath, date_col, sales_col, revenue_col)
        
        if auto_optimize:
            # Evaluate all models and pick best
            results = evaluate_models(df, periods)
            best_model = results['best_model']
            best_accuracy = results['best_accuracy']
            all_results = results['results']
        else:
            model = data.get('model', 'Prophet')
            forecast_df = forecast_sales(df, periods, model, auto_config=True)
            best_model = model
            all_results = {model: {'forecast': forecast_df, 'accuracy': None}}
            best_accuracy = None
        
        # Get best forecast
        forecast_df = all_results[best_model]['forecast']
        
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
