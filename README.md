# ⚾ No-Hitter Forecaster

A Python web application that predicts the daily probability of MLB no-hitters using a novel Bayesian-updated Poisson statistical model.

## Features

- **Daily Predictions**: Calculates percentage chance of at least one no-hitter occurring each day during MLB season
- **Historical Analysis**: Analyzes trends by month, specific dates, decades, and time since last no-hitter  
- **Interactive Web Interface**: Streamlit-based dashboard with visualizations and historical data browser
- **Automated Scheduling**: Runs predictions automatically each morning during MLB season
- **Novel Algorithm**: Combines base rates, seasonal patterns, date-specific trends, and recency effects

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd no-hitter-analysis
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Initialize the database:
```bash
python3 main.py update
```

### Running the Application

#### Web Interface (Recommended)
```bash
python3 main.py web
```
Then open your browser to `http://localhost:8501`

#### Command Line Prediction
```bash
# Today's prediction
python3 main.py predict

# Prediction for specific date
python3 main.py predict --date 2024-07-26
```

#### Start Scheduler (for automated daily predictions)
```bash
python3 main.py scheduler
```

## How It Works

### The Algorithm

Our novel prediction model combines multiple factors using a Bayesian-updated Poisson approach:

1. **Base Rate**: Historical frequency of no-hitters (~1.2% daily probability)
2. **Monthly Factors**: Seasonal adjustments (e.g., September shows higher frequency)
3. **Date-Specific Patterns**: Boost for historically significant dates (April 27, May 15, etc.)
4. **Decadal Trends**: Weight recent decades more heavily
5. **Recency Effects**: Adjust based on time since last no-hitter using exponential waiting time model

Final probability = Base Rate × Monthly Factor × Date Factor × Decadal Weight × Recency Adjustment

### Data Sources

The application uses historical no-hitter data including:
- Date of occurrence
- Pitcher name  
- Teams involved
- Game details (complete game, combined, perfect game, etc.)

## Project Structure

```
no-hitter-analysis/
├── src/
│   ├── data/
│   │   ├── collector.py          # Data collection and management
│   │   └── __init__.py
│   ├── algorithm/
│   │   ├── predictor.py          # Core prediction algorithm
│   │   └── __init__.py
│   ├── web/
│   │   ├── app.py               # Streamlit web interface
│   │   └── __init__.py
│   ├── scheduler.py             # Automated scheduling
│   └── __init__.py
├── data/                        # Data files (CSV, JSON)
├── logs/                        # Application logs
├── static/                      # Static web assets
├── templates/                   # HTML templates
├── requirements.txt             # Python dependencies
├── main.py                     # Application entry point
└── README.md                   # This file
```

## Web Interface

The Streamlit web app includes four main pages:

### Home
- Current day's prediction percentage
- Risk level indicator (Low/Medium/High)
- Confidence interval
- Explanation of factors contributing to the prediction
- Factor breakdown showing individual components

### Trends  
- No-hitters by month visualization
- No-hitters by decade chart
- High-frequency dates analysis

### History
- Searchable database of historical no-hitters
- Filter by year range
- Search by pitcher, team, or opponent

### About
- Algorithm explanation
- Data sources and limitations
- Accuracy considerations

## Configuration

### Scheduling
The scheduler runs daily predictions at 6:00 AM ET during MLB season (April-October). Modify the schedule in `src/scheduler.py`:

```python
schedule.every().day.at("06:00").do(self.run_daily_prediction)
```

### Data Updates
Historical data is stored in `data/no_hitters.csv`. To add new no-hitters or update the dataset:

```bash
python main.py update
```

## Development

### Adding New Data Sources
Extend the `NoHitterDataCollector` class in `src/data/collector.py` to add new scraping sources or API integrations.

### Modifying the Algorithm
The prediction algorithm is implemented in `src/algorithm/predictor.py`. Key methods:
- `calculate_base_rate()`: Base probability calculation
- `calculate_monthly_factors()`: Seasonal adjustments
- `calculate_date_factors()`: Date-specific patterns
- `predict_probability()`: Main prediction method

### Customizing the Web Interface
Modify `src/web/app.py` to add new pages, visualizations, or features to the Streamlit interface.

## Dependencies

- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **scipy**: Statistical functions  
- **streamlit**: Web interface framework
- **matplotlib/seaborn**: Data visualization
- **beautifulsoup4**: Web scraping
- **requests**: HTTP requests
- **schedule**: Task scheduling

## Limitations

This is a statistical model for entertainment and analysis purposes. Real baseball involves many factors not captured:

- Pitcher skill and current form
- Weather conditions
- Team matchups and strategies  
- Injuries and roster changes
- Game situations and context

Predictions should not be used for gambling or considered definitive forecasts.

## License

This project is open source. See the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check the logs in the `logs/` directory for debugging
- Ensure all dependencies are properly installed

---

Built with ❤️ for baseball fans and data enthusiasts.