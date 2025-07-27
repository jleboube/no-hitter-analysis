#!/usr/bin/env python3
"""
No-Hitter Forecaster - Main Application Entry Point

This script provides a command-line interface to run different components 
of the No-Hitter Forecaster application.
"""

import argparse
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def run_web_app():
    """Launch the Streamlit web application"""
    import subprocess
    import os
    import shutil
    
    app_path = os.path.join('src', 'web', 'app.py')
    
    # Try to find streamlit in common locations
    streamlit_paths = [
        'streamlit',  # If in PATH
        os.path.expanduser('~/.local/bin/streamlit'),  # User install
        '/usr/local/bin/streamlit',  # System install
    ]
    
    streamlit_cmd = None
    for path in streamlit_paths:
        if shutil.which(path) or os.path.exists(path):
            streamlit_cmd = path
            break
    
    if not streamlit_cmd:
        print("❌ Streamlit not found. Please ensure it's installed:")
        print("   pip install streamlit")
        print("   or add ~/.local/bin to your PATH")
        return
    
    cmd = [streamlit_cmd, 'run', app_path, '--server.port=8501']
    
    print("Starting No-Hitter Forecaster web application...")
    print("Open your browser to: http://localhost:8501")
    
    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        print("❌ Error: Could not execute streamlit command")
        print("Try running directly: ~/.local/bin/streamlit run src/web/app.py")
    except KeyboardInterrupt:
        print("\nShutting down web application...")

def run_scheduler():
    """Start the prediction scheduler"""
    from src.scheduler import NoHitterScheduler
    
    scheduler = NoHitterScheduler()
    print("Starting prediction scheduler...")
    
    try:
        scheduler.start_scheduler()
    except KeyboardInterrupt:
        print("\nShutting down scheduler...")

def run_prediction(date=None):
    """Run a single prediction"""
    from src.scheduler import NoHitterScheduler
    
    scheduler = NoHitterScheduler()
    result = scheduler.run_manual_prediction(date)
    
    if result:
        print(f"\n📊 No-Hitter Prediction Results:")
        print(f"Date: {result['date']}")
        print(f"Probability: {result['probability_percent']:.2f}%")
        print(f"Confidence Interval: {result['confidence_interval']['lower']:.1f}% - {result['confidence_interval']['upper']:.1f}%")
        print(f"Explanation: {result['explanation']}")

def update_data():
    """Update the no-hitter database"""
    from src.data.collector import NoHitterDataCollector
    
    collector = NoHitterDataCollector()
    print("Updating no-hitter database...")
    
    df = collector.update_data()
    validation = collector.validate_data()
    
    print(f"✅ Data update complete!")
    print(f"Total records: {validation['total_records']}")
    print(f"Date range: {validation['date_range'][0]} to {validation['date_range'][1]}")

def check_status():
    """Check the status of predictions and cache"""
    import json
    from datetime import datetime
    
    print(f"🕐 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Check predictions file
    predictions_file = 'data/daily_predictions.json'
    if os.path.exists(predictions_file):
        try:
            with open(predictions_file, 'r') as f:
                predictions = json.load(f)
            
            print(f"📊 Found {len(predictions)} predictions in database")
            
            # Get today's date
            today_str = datetime.now().strftime('%Y-%m-%d')
            
            if today_str in predictions:
                pred = predictions[today_str]
                print(f"✅ Today's prediction exists:")
                print(f"   📅 Date: {pred['date']}")
                print(f"   📊 Probability: {pred['probability_percent']:.2f}%")
                
                if 'selected_pitcher' in pred:
                    pitcher = pred['selected_pitcher']
                    print(f"   🎯 Selected Pitcher: {pitcher['name']} ({pitcher['team']} vs {pitcher['opponent']})")
                
                if 'timestamp' in pred:
                    print(f"   ⏰ Generated: {pred['timestamp']}")
                else:
                    print(f"   ⏰ Generated: No timestamp (legacy prediction)")
            else:
                print(f"❌ No prediction found for today ({today_str})")
                
                # Show most recent prediction
                if predictions:
                    latest_date = max(predictions.keys())
                    latest_pred = predictions[latest_date]
                    print(f"📅 Most recent prediction: {latest_date}")
                    print(f"   📊 Probability: {latest_pred['probability_percent']:.2f}%")
                    
        except Exception as e:
            print(f"❌ Error reading predictions file: {e}")
    else:
        print(f"❌ Predictions file not found: {predictions_file}")
    
    print("")
    
    # Check if in MLB season
    try:
        from src.algorithm.predictor import NoHitterPredictor
        predictor = NoHitterPredictor()
        today = datetime.now().date()
        
        if predictor.is_mlb_season(today):
            print("⚾ Currently in MLB season - predictions active")
        else:
            print("⚠️ Currently in MLB off-season - predictions paused")
    except Exception as e:
        print(f"❌ Error checking MLB season: {e}")
    
    print("")
    print("💡 Tips:")
    print("   • Run `python main.py force-update` to generate today's prediction")
    print("   • Run `systemctl restart no-hitter-*` to restart services")
    print("   • Check logs in `logs/scheduler.log` for detailed information")

def force_update():
    """Force update today's prediction"""
    from datetime import datetime
    
    try:
        from src.scheduler import NoHitterScheduler
        from src.algorithm.predictor import NoHitterPredictor
        
        print(f"🕐 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check if in MLB season
        predictor = NoHitterPredictor()
        today = datetime.now().date()
        
        if not predictor.is_mlb_season(today):
            print("⚠️  Currently in MLB off-season")
            print("📅 Predictions available April-October")
            return
        
        print("🔄 Generating today's prediction...")
        
        # Run scheduler
        scheduler = NoHitterScheduler()
        scheduler.run_daily_prediction()
        
        # Also get and display the prediction
        result = scheduler.run_manual_prediction()
        
        if result:
            print("\n✅ Today's prediction updated successfully!")
            print(f"📅 Date: {result['date']}")
            print(f"📊 Probability: {result['probability_percent']:.2f}%")
            
            if 'selected_pitcher' in result:
                pitcher = result['selected_pitcher']
                print(f"🎯 Selected Pitcher: {pitcher['name']} ({pitcher['team']} vs {pitcher['opponent']})")
            
            print(f"💡 Explanation: {result['explanation']}")
            
            # Check confidence interval
            ci = result.get('confidence_interval', {})
            if ci:
                print(f"📈 Confidence: {ci.get('lower', 0):.1f}% - {ci.get('upper', 0):.1f}%")
            
            print("\n🌐 Refresh your web browser to see the updated prediction!")
            
        else:
            print("❌ Failed to generate prediction")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📋 Make sure you're in the no-hitter-analysis directory")
        print("🐍 And that dependencies are installed: pip3 install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("📋 Check logs for more details")

def ensure_directories():
    """Ensure required directories exist with proper permissions"""
    import os
    import stat
    
    directories = ['data', 'logs']
    for dir_name in directories:
        if not os.path.exists(dir_name):
            print(f"📁 Creating {dir_name} directory...")
            os.makedirs(dir_name, mode=0o755)
        else:
            # Check if we can write to the directory
            try:
                test_file = os.path.join(dir_name, '.write_test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except (OSError, PermissionError):
                print(f"❌ Permission error: Cannot write to {dir_name}/ directory")
                print(f"💡 Fix with: sudo chown -R $USER:$USER {dir_name}/ && chmod 755 {dir_name}/")
                sys.exit(1)

def main():
    # Ensure directories exist and are writable
    ensure_directories()
    
    parser = argparse.ArgumentParser(
        description='No-Hitter Forecaster - MLB No-Hitter Prediction System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py web                    # Launch web application
  python main.py scheduler              # Start daily prediction scheduler  
  python main.py predict                # Get today's prediction
  python main.py predict --date 2024-07-26  # Get prediction for specific date
  python main.py update                 # Update no-hitter database
  python main.py status                 # Check prediction status
  python main.py force-update           # Force generate today's prediction
        """
    )
    
    parser.add_argument(
        'command',
        choices=['web', 'scheduler', 'predict', 'update', 'status', 'force-update'],
        help='Command to run'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='Date for prediction (YYYY-MM-DD format)'
    )
    
    args = parser.parse_args()
    
    if args.command == 'web':
        run_web_app()
    elif args.command == 'scheduler':
        run_scheduler()
    elif args.command == 'predict':
        run_prediction(args.date)
    elif args.command == 'update':
        update_data()
    elif args.command == 'status':
        check_status()
    elif args.command == 'force-update':
        force_update()

if __name__ == "__main__":
    main()