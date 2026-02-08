# 📊 Sales & Revenue Forecasting Dashboard

A powerful, interactive dashboard for sales and revenue forecasting with multiple ML models and beautiful visualizations.

## ✨ Features

- 📁 **Drag & Drop CSV Upload** - Easy data import
- 🤖 **Auto-Optimization** - Tests multiple models and selects the best
- 📈 **Interactive Charts** - Beautiful forecast visualizations
- 🎯 **Model Comparison** - Compare ARIMA, Prophet, and Linear Regression
- 📊 **Real-time Statistics** - Key metrics at a glance
- 💾 **Export Results** - Download forecast data
- 📱 **Responsive Design** - Works on all devices

## 🚀 Deployment Options

### Option 1: Streamlit Cloud (Recommended)
1. Fork this repository
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Connect your GitHub repository
4. Deploy instantly!

### Option 2: Local Development
```bash
# Clone the repository
git clone https://github.com/yourusername/sales-forecasting-dashboard.git
cd sales-forecasting-dashboard

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### Option 3: GitHub Pages (Static Version)
Open `index.html` directly in your browser or deploy to GitHub Pages for a static version.

## 📋 Requirements

- Python 3.8+
- Streamlit
- Pandas
- NumPy
- Plotly

## 📊 Data Format

Upload a CSV file with the following columns:
- `date` - Date values (any format)
- `sales` - Sales figures
- `revenue` - Revenue figures

Example CSV:
```csv
date,sales,revenue
2023-01-01,45000,120000
2023-02-01,52000,135000
2023-03-01,48000,125000
```

## 🎯 Models Available

- **ARIMA** - Time series forecasting
- **Prophet** - Facebook's forecasting tool
- **Linear Regression** - Statistical approach

## 🛠️ Customization

### Adding New Models
1. Update the `models` dictionary in `app.py`
2. Add your model logic to the `generate_forecast` function
3. Update the model performance metrics

### Styling
- Modify the Streamlit theme in `st.set_page_config()`
- Update colors and layouts in the chart functions
- Customize the sidebar configuration

## 📈 Usage

1. **Load Data**: Use sample data or upload your CSV
2. **Configure**: Set forecast periods and model options
3. **Generate**: Click "Generate Forecast" to run predictions
4. **Analyze**: View model performance and visualizations
5. **Export**: Download forecast results as CSV

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing framework
- [Plotly](https://plotly.com/) for beautiful visualizations
- [Pandas](https://pandas.pydata.org/) for data manipulation

---

**Made with ❤️ for data enthusiasts**
