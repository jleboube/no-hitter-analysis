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

def main():
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
        """
    )
    
    parser.add_argument(
        'command',
        choices=['web', 'scheduler', 'predict', 'update'],
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

if __name__ == "__main__":
    main()