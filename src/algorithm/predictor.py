import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
import json
import logging
import os
import sys
from typing import Dict, Tuple

# Add data modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))

from weather import WeatherAnalyzer
from pitcher_analysis import PitcherPerformanceAnalyzer
from stadium_analysis import StadiumEnvironmentAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NoHitterPredictor:
    def __init__(self, data_file='data/no_hitters.csv'):
        self.data_file = data_file
        self.base_rate = None
        self.monthly_factors = {}
        self.date_factors = {}
        self.decadal_weights = {}
        
        # Initialize new analysis modules
        self.weather_analyzer = WeatherAnalyzer()
        self.pitcher_analyzer = PitcherPerformanceAnalyzer()
        self.stadium_analyzer = StadiumEnvironmentAnalyzer()
        
        # Cache for analysis patterns
        self.weather_patterns = None
        self.pitcher_patterns = None
        self.stadium_patterns = None
        
    def load_data(self):
        """Load no-hitter data"""
        df = pd.read_csv(self.data_file)
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    def calculate_base_rate(self, df):
        """Calculate base daily probability of no-hitter"""
        # Historical data: ~326 no-hitters over ~150 years
        # Season length: ~180 days (April-October)
        total_season_days = 150 * 180  # approximate
        total_no_hitters = len(df)
        
        # Poisson approximation: P(at least one) = 1 - e^(-λ)
        # where λ = average no-hitters per day
        lambda_daily = total_no_hitters / total_season_days
        
        # Base probability of at least one no-hitter per day
        self.base_rate = 1 - np.exp(-lambda_daily)
        
        logger.info(f"Base rate calculated: {self.base_rate:.4f} ({self.base_rate*100:.2f}%)")
        return self.base_rate
    
    def calculate_monthly_factors(self, df):
        """Calculate monthly adjustment factors"""
        df['month'] = df['date'].dt.month
        monthly_counts = df.groupby('month').size()
        total_no_hitters = len(df)
        
        # Expected proportion for each month (assuming equal distribution)
        expected_per_month = total_no_hitters / 7  # 7 months in season (April-October)
        
        for month in range(4, 11):  # April to October
            actual_count = monthly_counts.get(month, 0)
            factor = actual_count / expected_per_month if expected_per_month > 0 else 1.0
            self.monthly_factors[month] = factor
            
        logger.info(f"Monthly factors: {self.monthly_factors}")
        return self.monthly_factors
    
    def calculate_date_factors(self, df):
        """Calculate specific date adjustment factors"""
        # High-frequency dates from PRD: April 27, May 15, Sept 20, Sept 28
        high_freq_dates = [
            (4, 27), (5, 15), (9, 20), (9, 28)
        ]
        
        df['month_day'] = df['date'].dt.strftime('%m-%d')
        date_counts = df.groupby('month_day').size()
        
        for month, day in high_freq_dates:
            date_key = f"{month:02d}-{day:02d}"
            count = date_counts.get(date_key, 0)
            # Factor based on historical frequency vs average
            avg_freq = len(df) / 365  # rough average per calendar day
            factor = count / avg_freq if avg_freq > 0 else 1.0
            self.date_factors[(month, day)] = max(factor, 1.0)  # At least 1.0
            
        logger.info(f"Date factors: {self.date_factors}")
        return self.date_factors
    
    def calculate_decadal_weights(self, df):
        """Calculate decadal trend weights"""
        df['decade'] = (df['date'].dt.year // 10) * 10
        decade_counts = df.groupby('decade').size()
        
        current_decade = (datetime.now().year // 10) * 10
        
        # Weight recent decades more heavily
        for decade in decade_counts.index:
            years_ago = current_decade - decade
            # Exponential decay: more recent = higher weight
            weight = np.exp(-years_ago / 50)  # 50-year half-life
            self.decadal_weights[decade] = weight
            
        # Normalize weights
        total_weight = sum(self.decadal_weights.values())
        for decade in self.decadal_weights:
            self.decadal_weights[decade] /= total_weight
            
        logger.info(f"Decadal weights: {self.decadal_weights}")
        return self.decadal_weights
    
    def calculate_recency_adjustment(self, df, target_date):
        """Calculate recency-based adjustment using exponential waiting time"""
        # Find most recent no-hitter before target date
        recent_no_hitters = df[df['date'] < target_date]
        
        if len(recent_no_hitters) == 0:
            return 1.0
            
        last_no_hitter_date = recent_no_hitters['date'].max()
        days_since_last = (target_date - last_no_hitter_date).days
        
        # Historical average wait time between no-hitters
        date_diffs = df['date'].diff().dropna()
        avg_wait_days = date_diffs.dt.days.mean()
        
        # Exponential distribution parameter
        lambda_wait = 1 / avg_wait_days
        
        # Probability adjustment based on waiting time
        # If we've waited longer than average, increase probability
        if days_since_last > avg_wait_days:
            adjustment = 1 + (days_since_last - avg_wait_days) / avg_wait_days * 0.1
        else:
            adjustment = 1.0
            
        logger.info(f"Recency adjustment: {adjustment:.3f} (days since last: {days_since_last}, avg wait: {avg_wait_days:.1f})")
        return min(adjustment, 2.0)  # Cap at 2x
    
    def predict_probability(self, target_date=None):
        """Predict no-hitter probability for given date"""
        if target_date is None:
            target_date = datetime.now().date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # Load and prepare data
        df = self.load_data()
        
        # Initialize weather and pitcher analysis if not done
        if self.weather_patterns is None:
            logger.info("Analyzing weather patterns for historical no-hitters...")
            try:
                self.weather_patterns, _ = self.weather_analyzer.analyze_no_hitter_weather_patterns(df)
            except Exception as e:
                logger.warning(f"Weather analysis failed: {e}")
                self.weather_patterns = None
        
        if self.pitcher_patterns is None:
            logger.info("Analyzing pitcher performance patterns for historical no-hitters...")
            try:
                self.pitcher_patterns, _ = self.pitcher_analyzer.analyze_no_hitter_pitcher_patterns(df)
            except Exception as e:
                logger.warning(f"Pitcher analysis failed: {e}")
                self.pitcher_patterns = None
        
        if self.stadium_patterns is None:
            logger.info("Analyzing stadium environment patterns for historical no-hitters...")
            try:
                self.stadium_patterns, _ = self.stadium_analyzer.analyze_stadium_no_hitter_patterns(df)
            except Exception as e:
                logger.warning(f"Stadium analysis failed: {e}")
                self.stadium_patterns = None
        
        # Calculate traditional factors
        base_rate = self.calculate_base_rate(df)
        monthly_factors = self.calculate_monthly_factors(df)
        date_factors = self.calculate_date_factors(df)
        decadal_weights = self.calculate_decadal_weights(df)
        recency_adjustment = self.calculate_recency_adjustment(df, pd.Timestamp(target_date))
        
        # Calculate new factors
        weather_factor, current_weather = self.calculate_weather_factor()
        pitcher_factor, current_pitcher_stats = self.calculate_pitcher_factor()
        stadium_factor, stadium_info = self.calculate_stadium_factor()
        
        # Get factors for target date
        month = target_date.month
        day = target_date.day
        
        monthly_factor = monthly_factors.get(month, 1.0)
        date_factor = date_factors.get((month, day), 1.0)
        
        # Decadal factor (use current decade weight)
        current_decade = (target_date.year // 10) * 10
        decadal_factor = decadal_weights.get(current_decade, 1.0)
        
        # Enhanced Bayesian-inspired formula with new factors
        probability = (base_rate * monthly_factor * date_factor * decadal_factor * 
                      recency_adjustment * weather_factor * pitcher_factor * stadium_factor)
        
        # Ensure probability stays within reasonable bounds
        probability = min(probability, 0.15)  # Increased cap due to new factors
        probability = max(probability, 0.0005)  # Floor at 0.05%
        
        # Monte Carlo confidence interval
        confidence_interval = self.calculate_confidence_interval(probability)
        
        result = {
            'date': target_date.strftime('%Y-%m-%d'),
            'probability': probability,
            'probability_percent': probability * 100,
            'confidence_interval': confidence_interval,
            'factors': {
                'base_rate': base_rate,
                'monthly_factor': monthly_factor,
                'date_factor': date_factor,
                'decadal_factor': decadal_factor,
                'recency_adjustment': recency_adjustment,
                'weather_factor': weather_factor,
                'pitcher_factor': pitcher_factor,
                'stadium_factor': stadium_factor
            },
            'current_conditions': {
                'weather': current_weather,
                'pitcher_stats': current_pitcher_stats,
                'stadium_info': stadium_info
            },
            'explanation': self.generate_enhanced_explanation(
                target_date, probability, monthly_factor, date_factor, 
                recency_adjustment, weather_factor, pitcher_factor, stadium_factor,
                current_weather, current_pitcher_stats, stadium_info
            )
        }
        
        logger.info(f"Enhanced prediction for {target_date}: {probability*100:.2f}%")
        return result
    
    def calculate_confidence_interval(self, probability, num_simulations=1000):
        """Calculate confidence interval using Monte Carlo simulation"""
        simulations = []
        
        for _ in range(num_simulations):
            # Add noise to each factor
            noise_factor = np.random.normal(1.0, 0.1)  # 10% standard deviation
            sim_prob = probability * noise_factor
            sim_prob = max(min(sim_prob, 0.1), 0.001)  # Keep within bounds
            simulations.append(sim_prob)
        
        lower_bound = np.percentile(simulations, 2.5)
        upper_bound = np.percentile(simulations, 97.5)
        
        return {
            'lower': lower_bound * 100,
            'upper': upper_bound * 100
        }
    
    def generate_explanation(self, target_date, probability, monthly_factor, date_factor, recency_adjustment):
        """Generate human-readable explanation of the prediction"""
        explanations = []
        
        month_names = {4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October'}
        month_name = month_names.get(target_date.month, 'Unknown')
        
        if monthly_factor > 1.1:
            explanations.append(f"{month_name} historically shows higher no-hitter frequency")
        elif monthly_factor < 0.9:
            explanations.append(f"{month_name} historically shows lower no-hitter frequency")
        
        if date_factor > 1.1:
            explanations.append(f"{month_name} {target_date.day} is a historically significant date for no-hitters")
        
        if recency_adjustment > 1.1:
            explanations.append("It's been longer than average since the last no-hitter")
        
        if not explanations:
            explanations.append("Probability based on historical average patterns")
        
        return "; ".join(explanations)
    
    def calculate_weather_factor(self):
        """Calculate weather-based adjustment factor for current conditions"""
        try:
            # For now, simulate getting weather for a major league city
            # In production, this would get weather for all games today
            current_weather = self.weather_analyzer.get_current_weather('NYY')  # Use Yankees as default
            
            if current_weather and self.weather_patterns:
                factor = self.weather_analyzer.calculate_weather_factor(current_weather, self.weather_patterns)
                return factor, current_weather
            else:
                return 1.0, None
        except Exception as e:
            logger.warning(f"Weather factor calculation failed: {e}")
            return 1.0, None
    
    def calculate_pitcher_factor(self):
        """Calculate pitcher performance-based adjustment factor"""
        try:
            # Simulate current pitcher performance for today's games
            current_pitcher_stats = self.pitcher_analyzer.simulate_current_pitcher_form()
            
            if current_pitcher_stats:
                if self.pitcher_patterns:
                    factor = self.pitcher_analyzer.calculate_pitcher_form_factor(
                        current_pitcher_stats, self.pitcher_patterns
                    )
                else:
                    factor = 1.0  # Use neutral factor if no patterns yet
                return factor, current_pitcher_stats
            else:
                return 1.0, None
        except Exception as e:
            logger.warning(f"Pitcher factor calculation failed: {e}")
            return 1.0, None
    
    def calculate_stadium_factor(self):
        """Calculate stadium environment-based adjustment factor"""
        try:
            # For now, simulate getting today's games and stadium conditions
            # In production, this would analyze all scheduled games for the day
            sample_team = 'NYY'  # Use Yankees as default for simulation
            
            current_conditions = {
                'weather': getattr(self, '_current_weather', None)
            }
            
            # Always get stadium info, even without patterns
            stadium_info = self.stadium_analyzer.get_stadium_characteristics(sample_team)
            
            if self.stadium_patterns:
                factor, enhanced_stadium_info = self.stadium_analyzer.calculate_stadium_factor(
                    sample_team, current_conditions, self.stadium_patterns
                )
                return factor, enhanced_stadium_info
            else:
                # Provide basic stadium info even without patterns
                basic_info = {
                    'stadium': stadium_info.get('stadium', 'Unknown Stadium'),
                    'type': stadium_info.get('type', 'outdoor'),
                    'altitude': stadium_info.get('altitude', 0),
                    'altitude_category': self.stadium_analyzer.categorize_altitude(stadium_info.get('altitude', 0)),
                    'pitcher_friendliness_score': self.stadium_analyzer.calculate_pitcher_friendliness(stadium_info),
                    'characteristics': stadium_info.get('characteristics', [])
                }
                return 1.0, basic_info
        except Exception as e:
            logger.warning(f"Stadium factor calculation failed: {e}")
            return 1.0, None
    
    def generate_enhanced_explanation(self, target_date, probability, monthly_factor, 
                                    date_factor, recency_adjustment, weather_factor, 
                                    pitcher_factor, stadium_factor, current_weather, 
                                    current_pitcher_stats, stadium_info):
        """Generate enhanced explanation including weather and pitcher factors"""
        explanations = []
        
        month_names = {4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October'}
        month_name = month_names.get(target_date.month, 'Unknown')
        
        # Traditional factors
        if monthly_factor > 1.1:
            explanations.append(f"{month_name} historically shows higher no-hitter frequency")
        elif monthly_factor < 0.9:
            explanations.append(f"{month_name} historically shows lower no-hitter frequency")
        
        if date_factor > 1.1:
            explanations.append(f"{month_name} {target_date.day} is a historically significant date for no-hitters")
        
        if recency_adjustment > 1.1:
            explanations.append("It's been longer than average since the last no-hitter")
        
        # Weather factors
        if weather_factor > 1.1 and current_weather:
            weather_explanation = self.weather_analyzer.get_weather_explanation(current_weather, weather_factor)
            explanations.append(f"favorable {weather_explanation.lower()}")
        elif weather_factor < 0.9 and current_weather:
            weather_explanation = self.weather_analyzer.get_weather_explanation(current_weather, weather_factor)
            explanations.append(f"challenging {weather_explanation.lower()}")
        
        # Pitcher factors
        if pitcher_factor > 1.2 and current_pitcher_stats:
            pitcher_explanation = self.pitcher_analyzer.get_pitcher_explanation(
                current_pitcher_stats, pitcher_factor, self.pitcher_patterns
            )
            explanations.append(f"strong {pitcher_explanation.lower()}")
        elif pitcher_factor < 0.9 and current_pitcher_stats:
            pitcher_explanation = self.pitcher_analyzer.get_pitcher_explanation(
                current_pitcher_stats, pitcher_factor, self.pitcher_patterns
            )
            explanations.append(f"concerning {pitcher_explanation.lower()}")
        
        # Stadium factors
        if stadium_factor > 1.1 and stadium_info:
            stadium_explanation = self.stadium_analyzer.get_stadium_explanation(stadium_info, stadium_factor)
            explanations.append(f"favorable {stadium_explanation.lower()}")
        elif stadium_factor < 0.9 and stadium_info:
            stadium_explanation = self.stadium_analyzer.get_stadium_explanation(stadium_info, stadium_factor)
            explanations.append(f"challenging {stadium_explanation.lower()}")
        
        if not explanations:
            explanations.append("Probability based on historical patterns and current conditions")
        
        return "; ".join(explanations)
    
    def is_mlb_season(self, date=None):
        """Check if given date is during MLB season"""
        if date is None:
            date = datetime.now().date()
        elif isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        return 4 <= date.month <= 10

if __name__ == "__main__":
    predictor = NoHitterPredictor()
    result = predictor.predict_probability()
    print(f"Today's no-hitter probability: {result['probability_percent']:.2f}%")
    print(f"Explanation: {result['explanation']}")