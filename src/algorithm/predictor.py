import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
import json
import logging
import os
import sys
from typing import Dict, Tuple
import statsapi

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
        
        # MLB teams and their probable starters (simulated for demo)
        self.mlb_teams = [
            'NYY', 'BOS', 'TOR', 'TB', 'BAL',
            'HOU', 'LAA', 'OAK', 'SEA', 'TEX',
            'CLE', 'CWS', 'DET', 'KC', 'MIN',
            'ATL', 'MIA', 'NYM', 'PHI', 'WSN',
            'CHC', 'CIN', 'MIL', 'PIT', 'STL',
            'ARI', 'COL', 'LAD', 'SD', 'SF'
        ]
        
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
        """Predict no-hitter probability by selecting the pitcher with highest probability for given date"""
        if target_date is None:
            target_date = datetime.now().date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # Get the best pitcher prediction for the date
        best_pitcher_prediction = self.select_best_pitcher_for_date(target_date)
        return best_pitcher_prediction
    
    def select_best_pitcher_for_date(self, target_date):
        """Select the single pitcher with highest no-hitter probability for the given date"""
        
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
        
        # Simulate today's probable pitchers and their matchups
        probable_pitchers = self.get_probable_pitchers_for_date(target_date)
        
        best_pitcher = None
        best_probability = 0
        best_result = None
        
        # Evaluate each probable pitcher
        for pitcher_info in probable_pitchers:
            # Calculate pitcher-specific factors
            pitcher_specific_factor = self.calculate_pitcher_specific_factor(pitcher_info)
            stadium_factor_specific = self.calculate_pitcher_stadium_factor(pitcher_info)
            
            # Enhanced Bayesian formula for this specific pitcher
            pitcher_probability = (base_rate * monthly_factor * date_factor * decadal_factor * 
                                 recency_adjustment * weather_factor * pitcher_specific_factor * stadium_factor_specific)
            
            # Ensure probability stays within reasonable bounds
            pitcher_probability = min(pitcher_probability, 0.25)  # Higher cap for individual pitchers
            pitcher_probability = max(pitcher_probability, 0.0001)  # Floor at 0.01%
            
            # Track the best pitcher
            if pitcher_probability > best_probability:
                best_probability = pitcher_probability
                best_pitcher = pitcher_info
                
                # Monte Carlo confidence interval for best pitcher
                confidence_interval = self.calculate_confidence_interval(pitcher_probability)
                
                best_result = {
                    'date': target_date.strftime('%Y-%m-%d'),
                    'probability': pitcher_probability,
                    'probability_percent': pitcher_probability * 100,
                    'confidence_interval': confidence_interval,
                    'selected_pitcher': {
                        'name': pitcher_info['name'],
                        'team': pitcher_info['team'],
                        'opponent': pitcher_info['opponent'],
                        'stadium': pitcher_info['stadium']
                    },
                    'factors': {
                        'base_rate': base_rate,
                        'monthly_factor': monthly_factor,
                        'date_factor': date_factor,
                        'decadal_factor': decadal_factor,
                        'recency_adjustment': recency_adjustment,
                        'weather_factor': weather_factor,
                        'pitcher_factor': pitcher_specific_factor,
                        'stadium_factor': stadium_factor_specific
                    },
                    'current_conditions': {
                        'weather': current_weather,
                        'pitcher_stats': pitcher_info['stats'],
                        'stadium_info': stadium_info
                    },
                    'explanation': self.generate_pitcher_specific_explanation(
                        target_date, pitcher_probability, monthly_factor, date_factor, 
                        recency_adjustment, weather_factor, pitcher_specific_factor, stadium_factor_specific,
                        current_weather, pitcher_info, stadium_info
                    )
                }
        
        if best_result is None:
            # Fallback to general prediction if no pitchers found
            logger.warning("No probable pitchers found, using general prediction")
            probability = (base_rate * monthly_factor * date_factor * decadal_factor * 
                          recency_adjustment * weather_factor * pitcher_factor * stadium_factor)
            probability = min(probability, 0.15)
            probability = max(probability, 0.0005)
            confidence_interval = self.calculate_confidence_interval(probability)
            
            best_result = {
                'date': target_date.strftime('%Y-%m-%d'),
                'probability': probability,
                'probability_percent': probability * 100,
                'confidence_interval': confidence_interval,
                'selected_pitcher': {
                    'name': 'General Day Forecast',
                    'team': 'MLB',
                    'opponent': 'Various',
                    'stadium': 'Multiple Venues'
                },
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
        
        logger.info(f"Best pitcher prediction for {target_date}: {best_pitcher['name'] if best_pitcher else 'General'} - {best_result['probability_percent']:.2f}%")
        return best_result
    
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
    
    def get_probable_pitchers_for_date(self, target_date):
        """Get actual probable starting pitchers for the given date from MLB API"""
        try:
            # Format date for MLB API
            date_str = target_date.strftime('%Y-%m-%d')
            
            # Get today's schedule from MLB API
            schedule = statsapi.schedule(date=date_str)
            
            if not schedule:
                logger.warning(f"No MLB games scheduled for {date_str}")
                return []
            
            probable_pitchers = []
            
            for game in schedule:
                # Get game details including probable pitchers
                game_id = game['game_id']
                
                try:
                    # Get detailed game info with probable pitchers
                    game_info = statsapi.get('game', {'gamePk': game_id})
                    
                    home_team = game['home_name']
                    away_team = game['away_name']
                    home_team_abbr = self.get_team_abbreviation(home_team)
                    away_team_abbr = self.get_team_abbreviation(away_team)
                    
                    # Extract probable pitchers
                    probable_pitchers_data = game_info.get('gameData', {}).get('probablePitchers', {})
                    
                    # Get home pitcher (primary focus for no-hitter predictions)
                    home_pitcher = probable_pitchers_data.get('home')
                    if home_pitcher:
                        pitcher_info = self.get_real_pitcher_info(
                            home_pitcher, home_team_abbr, away_team_abbr, target_date, True, game
                        )
                        if pitcher_info:
                            probable_pitchers.append(pitcher_info)
                    
                    # Also get away pitcher
                    away_pitcher = probable_pitchers_data.get('away')
                    if away_pitcher:
                        pitcher_info = self.get_real_pitcher_info(
                            away_pitcher, away_team_abbr, home_team_abbr, target_date, False, game
                        )
                        if pitcher_info:
                            probable_pitchers.append(pitcher_info)
                            
                except Exception as e:
                    logger.warning(f"Error getting pitcher info for game {game_id}: {e}")
                    continue
            
            logger.info(f"Found {len(probable_pitchers)} probable pitchers for {date_str}")
            return probable_pitchers
            
        except Exception as e:
            logger.error(f"Error fetching MLB schedule for {target_date}: {e}")
            # Try MySportsFeeds API as backup
            logger.info("Trying MySportsFeeds API as backup")
            mysportsfeeds_pitchers = self.get_mysportsfeeds_pitchers(target_date)
            if mysportsfeeds_pitchers:
                return mysportsfeeds_pitchers
            
            # Final fallback to simulated data if both APIs fail
            logger.info("Both APIs failed, falling back to simulated data")
            return self.get_simulated_pitchers_for_date(target_date)
    
    def get_team_abbreviation(self, team_name):
        """Convert full team name to abbreviation"""
        team_mapping = {
            'Los Angeles Angels': 'LAA', 'Houston Astros': 'HOU', 'Oakland Athletics': 'OAK',
            'Seattle Mariners': 'SEA', 'Texas Rangers': 'TEX', 'Los Angeles Dodgers': 'LAD',
            'San Diego Padres': 'SD', 'San Francisco Giants': 'SF', 'Colorado Rockies': 'COL',
            'Arizona Diamondbacks': 'ARI', 'Minnesota Twins': 'MIN', 'Kansas City Royals': 'KC',
            'Detroit Tigers': 'DET', 'Chicago White Sox': 'CWS', 'Cleveland Guardians': 'CLE',
            'Milwaukee Brewers': 'MIL', 'St. Louis Cardinals': 'STL', 'Chicago Cubs': 'CHC',
            'Cincinnati Reds': 'CIN', 'Pittsburgh Pirates': 'PIT', 'Atlanta Braves': 'ATL',
            'Miami Marlins': 'MIA', 'New York Mets': 'NYM', 'Philadelphia Phillies': 'PHI',
            'Washington Nationals': 'WSN', 'Boston Red Sox': 'BOS', 'New York Yankees': 'NYY',
            'Tampa Bay Rays': 'TB', 'Toronto Blue Jays': 'TOR', 'Baltimore Orioles': 'BAL'
        }
        return team_mapping.get(team_name, team_name[:3].upper())
    
    def get_real_pitcher_info(self, pitcher_data, team, opponent, target_date, is_home, game_info):
        """Get real pitcher information from MLB API"""
        try:
            pitcher_id = pitcher_data.get('id')
            pitcher_name = pitcher_data.get('fullName', 'Unknown Pitcher')
            
            if not pitcher_id:
                return None
            
            # Get pitcher's current season stats
            try:
                player_stats = statsapi.player_stat_data(pitcher_id, group="[pitching]", type="season")
                
                # Extract relevant stats
                stats = {}
                if player_stats and 'stats' in player_stats:
                    season_stats = player_stats['stats'][0]['stats'] if player_stats['stats'] else {}
                    
                    stats = {
                        'recent_era': float(season_stats.get('era', 4.0)),
                        'recent_whip': float(season_stats.get('whip', 1.3)),
                        'k_per_nine': float(season_stats.get('strikeoutsPer9Inn', 8.0)),
                        'quality_starts': int(season_stats.get('qualityStarts', 5)),
                        'wins': int(season_stats.get('wins', 5)),
                        'losses': int(season_stats.get('losses', 5)),
                        'innings_pitched': float(season_stats.get('inningsPitched', 50.0)),
                        'strikeouts': int(season_stats.get('strikeOuts', 50)),
                        'walks': int(season_stats.get('baseOnBalls', 20)),
                        'hits_allowed': int(season_stats.get('hits', 60))
                    }
                else:
                    # Fallback stats if API doesn't return data
                    stats = {
                        'recent_era': 3.8, 'recent_whip': 1.25, 'k_per_nine': 8.5,
                        'quality_starts': 8, 'wins': 6, 'losses': 4,
                        'innings_pitched': 75.0, 'strikeouts': 70, 'walks': 25, 'hits_allowed': 65
                    }
                    
            except Exception as e:
                logger.warning(f"Error getting stats for pitcher {pitcher_name}: {e}")
                # Use default stats
                stats = {
                    'recent_era': 3.8, 'recent_whip': 1.25, 'k_per_nine': 8.5,
                    'quality_starts': 8, 'wins': 6, 'losses': 4,
                    'innings_pitched': 75.0, 'strikeouts': 70, 'walks': 25, 'hits_allowed': 65
                }
            
            # Get stadium info
            venue = game_info.get('gameData', {}).get('venue', {})
            stadium_name = venue.get('name', f'{team} Stadium')
            
            return {
                'name': pitcher_name,
                'team': team,
                'opponent': opponent,
                'is_home': is_home,
                'stadium': stadium_name,
                'stats': stats,
                'pitcher_id': pitcher_id
            }
            
        except Exception as e:
            logger.error(f"Error processing pitcher data: {e}")
            return None
    
    def get_mysportsfeeds_pitchers(self, target_date):
        """Backup method using MySportsFeeds API"""
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            # MySportsFeeds API credentials
            api_key = "8651000e-1a9a-4e64-9bf2-69025a"
            password = "MYSPORTSFEEDS"
            
            # Format date
            date_str = target_date.strftime('%Y%m%d')
            season = target_date.year
            
            # Get daily schedule
            url = f"https://api.mysportsfeeds.com/v2.1/pull/mlb/{season}/date/{date_str}/games.json"
            
            response = requests.get(
                url, 
                auth=HTTPBasicAuth(api_key, password),
                headers={'User-Agent': 'NoHitterForecaster/1.0'}
            )
            
            if response.status_code != 200:
                logger.warning(f"MySportsFeeds API returned status {response.status_code}")
                return []
            
            data = response.json()
            games = data.get('games', [])
            
            if not games:
                logger.warning(f"No games found in MySportsFeeds for {target_date}")
                return []
            
            probable_pitchers = []
            
            for game in games:
                try:
                    home_team = game['schedule']['homeTeam']['abbreviation']
                    away_team = game['schedule']['awayTeam']['abbreviation']
                    venue = game['schedule']['venue']['name']
                    
                    # MySportsFeeds doesn't always have probable pitchers in schedule
                    # So we'll create entries for both teams and use season stats
                    
                    # Get season stats for probable pitchers (this is a simplified approach)
                    # In a full implementation, you'd need to track probable pitchers separately
                    
                    # For now, create placeholder pitcher info that will use season averages
                    home_pitcher_info = {
                        'name': f'{home_team} Probable Starter',
                        'team': home_team,
                        'opponent': away_team,
                        'is_home': True,
                        'stadium': venue,
                        'stats': {
                            'recent_era': 3.8, 'recent_whip': 1.25, 'k_per_nine': 8.5,
                            'quality_starts': 8, 'wins': 6, 'losses': 4,
                            'innings_pitched': 75.0, 'strikeouts': 70, 'walks': 25, 'hits_allowed': 65
                        },
                        'pitcher_id': f'msf_{home_team}_home'
                    }
                    
                    away_pitcher_info = {
                        'name': f'{away_team} Probable Starter',
                        'team': away_team,
                        'opponent': home_team,
                        'is_home': False,
                        'stadium': venue,
                        'stats': {
                            'recent_era': 3.9, 'recent_whip': 1.27, 'k_per_nine': 8.3,
                            'quality_starts': 7, 'wins': 5, 'losses': 5,
                            'innings_pitched': 72.0, 'strikeouts': 68, 'walks': 27, 'hits_allowed': 68
                        },
                        'pitcher_id': f'msf_{away_team}_away'
                    }
                    
                    probable_pitchers.extend([home_pitcher_info, away_pitcher_info])
                    
                except Exception as e:
                    logger.warning(f"Error processing MySportsFeeds game data: {e}")
                    continue
            
            logger.info(f"Found {len(probable_pitchers)} pitchers from MySportsFeeds for {target_date}")
            return probable_pitchers
            
        except Exception as e:
            logger.error(f"Error with MySportsFeeds API: {e}")
            return []
    
    def get_simulated_pitchers_for_date(self, target_date):
        """Fallback method - get simulated pitchers if MLB API fails"""
        import random
        
        # Seed random for consistent results per date
        random.seed(target_date.toordinal())
        
        # Simulate 8-12 games on a typical day
        num_games = random.randint(8, 12)
        probable_pitchers = []
        
        available_teams = self.mlb_teams.copy()
        random.shuffle(available_teams)
        
        for i in range(min(num_games, len(available_teams) // 2)):
            if len(available_teams) < 2:
                break
                
            # Pick two teams for a matchup
            team1 = available_teams.pop()
            team2 = available_teams.pop()
            
            # Determine home team (randomly for simulation)
            if random.choice([True, False]):
                home_team, away_team = team1, team2
            else:
                home_team, away_team = team2, team1
            
            # Generate pitcher for home team
            pitcher_info = self.generate_pitcher_info(home_team, away_team, target_date, True)
            probable_pitchers.append(pitcher_info)
        
        return probable_pitchers
    
    def generate_pitcher_info(self, team, opponent, target_date, is_home=True):
        """Generate pitcher information with simulated stats"""
        import random
        
        # Seed based on team and date for consistency
        random.seed(hash(team + str(target_date)))
        
        # Generate realistic pitcher names (simplified for demo)
        first_names = ['Jake', 'Mike', 'Carlos', 'Tyler', 'Alex', 'Ryan', 'David', 'Chris', 'Matt', 'Luis']
        last_names = ['Johnson', 'Smith', 'Rodriguez', 'Williams', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor']
        
        pitcher_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Generate recent form stats
        stats = {
            'recent_era': random.uniform(1.8, 5.2),
            'recent_whip': random.uniform(0.85, 1.75),
            'k_per_nine': random.uniform(6.0, 13.5),
            'quality_starts': random.randint(0, 3),
            'last_5_starts_era': random.uniform(2.0, 5.5),
            'career_era': random.uniform(3.0, 4.8),
            'season_record': f"{random.randint(4, 15)}-{random.randint(2, 12)}"
        }
        
        # Get stadium info
        stadium_info = self.stadium_analyzer.get_stadium_characteristics(team)
        
        return {
            'name': pitcher_name,
            'team': team,
            'opponent': opponent,
            'is_home': is_home,
            'stadium': stadium_info.get('stadium', f'{team} Stadium'),
            'stats': stats
        }
    
    def calculate_pitcher_specific_factor(self, pitcher_info):
        """Calculate pitcher-specific performance factor"""
        stats = pitcher_info['stats']
        factor = 1.0
        
        # Recent ERA factor (lower is better)
        recent_era = stats.get('recent_era', 4.0)
        if recent_era <= 2.5:
            factor *= 1.5  # Excellent recent form
        elif recent_era <= 3.5:
            factor *= 1.2  # Good recent form
        elif recent_era >= 5.0:
            factor *= 0.7  # Poor recent form
        
        # WHIP factor (lower is better)
        recent_whip = stats.get('recent_whip', 1.3)
        if recent_whip <= 1.0:
            factor *= 1.4  # Excellent control
        elif recent_whip <= 1.2:
            factor *= 1.1  # Good control
        elif recent_whip >= 1.5:
            factor *= 0.8  # Control issues
        
        # Strikeout rate factor (higher is better)
        k_per_nine = stats.get('k_per_nine', 8.0)
        if k_per_nine >= 10.0:
            factor *= 1.3  # Dominant strikeout rate
        elif k_per_nine >= 8.5:
            factor *= 1.1  # Good strikeout rate
        elif k_per_nine <= 6.5:
            factor *= 0.9  # Low strikeout rate
        
        # Quality starts factor
        quality_starts = stats.get('quality_starts', 1)
        if quality_starts >= 2:
            factor *= 1.2  # Consistent quality
        elif quality_starts == 0:
            factor *= 0.9  # Inconsistent
        
        # Hot streak bonus
        if recent_era <= 2.5 and recent_whip <= 1.0 and quality_starts >= 2:
            factor *= 1.3  # Pitcher is on fire
        
        # Cap the factor
        factor = max(0.5, min(3.0, factor))
        return factor
    
    def calculate_pitcher_stadium_factor(self, pitcher_info):
        """Calculate stadium-specific factor for the pitcher"""
        try:
            team = pitcher_info['team']
            stadium_chars = self.stadium_analyzer.get_stadium_characteristics(team)
            
            factor = 1.0
            
            # Altitude factor
            altitude = stadium_chars.get('altitude', 0)
            if altitude > 3000:  # High altitude (like Coors Field)
                factor *= 0.8  # Harder to pitch at altitude
            elif stadium_chars.get('type') == 'dome':
                factor *= 1.1  # Controlled environment helps
            
            # Pitcher friendliness
            friendliness = self.stadium_analyzer.calculate_pitcher_friendliness(stadium_chars)
            if friendliness >= 7:
                factor *= 1.15  # Very pitcher-friendly
            elif friendliness >= 6:
                factor *= 1.05  # Somewhat pitcher-friendly
            elif friendliness <= 4:
                factor *= 0.9   # Hitter-friendly
            
            return max(0.7, min(1.4, factor))
        except:
            return 1.0
    
    def generate_pitcher_specific_explanation(self, target_date, probability, monthly_factor, 
                                           date_factor, recency_adjustment, weather_factor, 
                                           pitcher_factor, stadium_factor, current_weather, 
                                           pitcher_info, stadium_info):
        """Generate explanation specific to the selected pitcher"""
        explanations = []
        
        month_names = {4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October'}
        month_name = month_names.get(target_date.month, 'Unknown')
        
        # Pitcher-specific explanation
        pitcher_name = pitcher_info['name']
        team = pitcher_info['team']
        opponent = pitcher_info['opponent']
        stats = pitcher_info['stats']
        
        explanations.append(f"{pitcher_name} ({team} vs {opponent}) selected as highest probability pitcher")
        
        # Pitcher form analysis
        recent_era = stats.get('recent_era', 4.0)
        if recent_era <= 2.5:
            explanations.append(f"excellent recent form (ERA {recent_era:.2f})")
        elif recent_era <= 3.5:
            explanations.append(f"solid recent form (ERA {recent_era:.2f})")
        elif recent_era >= 5.0:
            explanations.append(f"struggling recently (ERA {recent_era:.2f})")
        
        # Quality starts
        quality_starts = stats.get('quality_starts', 1)
        if quality_starts >= 2:
            explanations.append(f"consistent with {quality_starts}/3 quality starts")
        
        # Traditional factors
        if monthly_factor > 1.1:
            explanations.append(f"{month_name} historically favors no-hitters")
        elif monthly_factor < 0.9:
            explanations.append(f"{month_name} historically less favorable")
        
        if date_factor > 1.1:
            explanations.append(f"{month_name} {target_date.day} is historically significant")
        
        if recency_adjustment > 1.1:
            explanations.append("longer than average since last no-hitter")
        
        # Weather factors
        if weather_factor > 1.1 and current_weather:
            explanations.append("favorable weather conditions")
        elif weather_factor < 0.9 and current_weather:
            explanations.append("challenging weather conditions")
        
        # Stadium factors
        if stadium_factor > 1.1:
            explanations.append("pitcher-friendly stadium environment")
        elif stadium_factor < 0.9:
            explanations.append("hitter-friendly stadium environment")
        
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