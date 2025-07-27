import schedule
import time
import json
import os
import logging
from datetime import datetime
from data.collector import NoHitterDataCollector
from algorithm.predictor import NoHitterPredictor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NoHitterScheduler:
    def __init__(self):
        self.collector = NoHitterDataCollector()
        self.predictor = NoHitterPredictor()
        self.predictions_file = 'data/daily_predictions.json'
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
    
    def is_mlb_season(self):
        """Check if current date is during MLB season"""
        return self.predictor.is_mlb_season()
    
    def run_daily_prediction(self):
        """Run the daily prediction routine"""
        try:
            logger.info("Starting daily prediction routine...")
            
            # Check if in season
            if not self.is_mlb_season():
                logger.info("Currently off-season. Skipping prediction.")
                return
            
            # Update data (check for new no-hitters)
            logger.info("Updating no-hitter data...")
            self.collector.update_data()
            
            # Generate prediction
            logger.info("Generating prediction...")
            prediction = self.predictor.predict_probability()
            
            # Save prediction
            self.save_prediction(prediction)
            
            # Clear any web cache files to force refresh
            self.clear_web_cache()
            
            logger.info(f"Daily prediction complete: {prediction['probability_percent']:.2f}%")
            
        except Exception as e:
            logger.error(f"Error in daily prediction routine: {str(e)}")
    
    def save_prediction(self, prediction):
        """Save prediction to JSON file with timestamp"""
        predictions = self.load_predictions()
        
        # Add timestamp to prediction for freshness tracking
        prediction['timestamp'] = datetime.now().isoformat()
        
        # Add current prediction
        predictions[prediction['date']] = prediction
        
        # Keep only last 30 days of predictions
        sorted_dates = sorted(predictions.keys())
        if len(sorted_dates) > 30:
            for old_date in sorted_dates[:-30]:
                del predictions[old_date]
        
        # Save to file
        with open(self.predictions_file, 'w') as f:
            json.dump(predictions, f, indent=2, default=str)
        
        logger.info(f"Prediction saved for {prediction['date']} at {prediction['timestamp']}")
    
    def clear_web_cache(self):
        """Clear web cache to force refresh of predictions"""
        try:
            # Signal file for web app to refresh
            cache_signal_file = 'data/cache_refresh.txt'
            with open(cache_signal_file, 'w') as f:
                f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            logger.info("Web cache refresh signal created")
        except Exception as e:
            logger.warning(f"Could not create cache refresh signal: {e}")
    
    def load_predictions(self):
        """Load existing predictions from file"""
        if os.path.exists(self.predictions_file):
            try:
                with open(self.predictions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading predictions file: {str(e)}")
                return {}
        return {}
    
    def get_latest_prediction(self):
        """Get the most recent prediction"""
        predictions = self.load_predictions()
        if not predictions:
            return None
        
        latest_date = max(predictions.keys())
        return predictions[latest_date]
    
    def start_scheduler(self):
        """Start the scheduling service"""
        logger.info("Starting No-Hitter Forecaster scheduler...")
        
        # Schedule daily prediction at 6 AM local time (adjust as needed)
        schedule.every().day.at("06:00").do(self.run_daily_prediction)
        
        # Also schedule at 7 AM as backup
        schedule.every().day.at("07:00").do(self.run_daily_prediction)
        
        # Run initial prediction if none exists for today
        today = datetime.now().strftime('%Y-%m-%d')
        predictions = self.load_predictions()
        if today not in predictions and self.is_mlb_season():
            logger.info("Running initial prediction for today...")
            self.run_daily_prediction()
        
        logger.info("Scheduler started. Daily predictions will run at 6:00 AM and 7:00 AM during MLB season.")
        logger.info(f"Current local time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_manual_prediction(self, date=None):
        """Run a manual prediction for testing"""
        try:
            if date:
                prediction = self.predictor.predict_probability(date)
            else:
                prediction = self.predictor.predict_probability()
            
            print(f"Prediction for {prediction['date']}:")
            print(f"Probability: {prediction['probability_percent']:.2f}%")
            print(f"Explanation: {prediction['explanation']}")
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error in manual prediction: {str(e)}")
            return None

def main():
    """Main function for running the scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='No-Hitter Forecaster Scheduler')
    parser.add_argument('--mode', choices=['schedule', 'manual'], default='schedule',
                       help='Run mode: schedule (continuous) or manual (one-time)')
    parser.add_argument('--date', type=str, help='Date for manual prediction (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    scheduler = NoHitterScheduler()
    
    if args.mode == 'manual':
        scheduler.run_manual_prediction(args.date)
    else:
        scheduler.start_scheduler()

if __name__ == "__main__":
    main()