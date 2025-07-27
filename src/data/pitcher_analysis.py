import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PitcherPerformanceAnalyzer:
    def __init__(self):
        self.pitcher_cache_file = 'data/pitcher_performance_cache.json'
        os.makedirs('data', exist_ok=True)
        
        # Simulated pitcher performance patterns based on common no-hitter scenarios
        self.performance_patterns = {
            'hot_streak_indicators': {
                'era_threshold': 2.50,        # ERA in previous 3 starts
                'whip_threshold': 1.00,       # WHIP in previous 3 starts
                'strikeout_rate': 8.5,        # K/9 in previous 3 starts
                'quality_starts': 2           # Quality starts in last 3
            },
            'form_indicators': {
                'recent_shutouts': 1,          # Shutouts in last 5 starts
                'low_hit_games': 2,           # Games with ≤5 hits in last 5 starts
                'walks_per_nine': 3.0,        # BB/9 threshold
                'hits_per_nine': 7.5          # H/9 threshold
            }
        }
    
    def load_pitcher_cache(self):
        """Load cached pitcher performance data"""
        if os.path.exists(self.pitcher_cache_file):
            try:
                with open(self.pitcher_cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_pitcher_cache(self, cache):
        """Save pitcher performance data to cache"""
        with open(self.pitcher_cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    
    def simulate_pitcher_performance(self, pitcher_name, no_hitter_date, team):
        """Simulate pitcher performance leading up to no-hitter"""
        import random
        
        # Use pitcher name and date for consistent "randomness"
        random.seed(hash(pitcher_name + str(no_hitter_date)))
        
        no_hitter_date_obj = pd.to_datetime(no_hitter_date)
        
        # Generate performance for 5 previous starts
        starts = []
        for i in range(1, 6):
            # Simulate start date (roughly every 5 days)
            start_date = no_hitter_date_obj - timedelta(days=5*i)
            
            # Simulate performance - adjust based on "proximity" to no-hitter
            # Closer starts tend to be better (hot streak pattern)
            streak_factor = (6 - i) / 6  # Closer = higher factor
            
            # Generate realistic baseball stats
            innings = random.uniform(5.0, 8.0)
            
            # Better performance closer to no-hitter
            base_era = 3.50 - (streak_factor * 1.5)  # Better ERA when hot
            hits = max(1, int(random.uniform(3, 9) - (streak_factor * 2)))
            walks = max(0, int(random.uniform(1, 4) - (streak_factor * 1)))
            strikeouts = max(3, int(random.uniform(4, 12) + (streak_factor * 2)))
            earned_runs = max(0, int((hits + walks) * random.uniform(0.1, 0.4) - (streak_factor * 0.2)))
            
            # Calculate derived stats
            era = (earned_runs * 9) / innings if innings > 0 else 0
            whip = (hits + walks) / innings if innings > 0 else 0
            k_per_nine = (strikeouts * 9) / innings if innings > 0 else 0
            h_per_nine = (hits * 9) / innings if innings > 0 else 0
            
            quality_start = 1 if innings >= 6 and earned_runs <= 3 else 0
            
            start = {
                'date': start_date.strftime('%Y-%m-%d'),
                'start_number': 6 - i,  # 5 = most recent, 1 = oldest
                'innings': round(innings, 1),
                'hits': hits,
                'walks': walks,
                'strikeouts': strikeouts,
                'earned_runs': earned_runs,
                'era': round(era, 2),
                'whip': round(whip, 2),
                'k_per_nine': round(k_per_nine, 1),
                'h_per_nine': round(h_per_nine, 1),
                'quality_start': quality_start
            }
            
            starts.append(start)
        
        # Calculate aggregated stats for recent performance
        recent_3_starts = starts[:3]  # Most recent 3
        all_5_starts = starts
        
        # Aggregate stats
        total_innings_3 = sum(s['innings'] for s in recent_3_starts)
        total_innings_5 = sum(s['innings'] for s in all_5_starts)
        
        performance_summary = {
            'pitcher': pitcher_name,
            'team': team,
            'no_hitter_date': no_hitter_date,
            'recent_3_starts': {
                'era': round(sum(s['earned_runs'] for s in recent_3_starts) * 9 / total_innings_3, 2) if total_innings_3 > 0 else 0,
                'whip': round(sum(s['hits'] + s['walks'] for s in recent_3_starts) / total_innings_3, 2) if total_innings_3 > 0 else 0,
                'k_per_nine': round(sum(s['strikeouts'] for s in recent_3_starts) * 9 / total_innings_3, 1) if total_innings_3 > 0 else 0,
                'h_per_nine': round(sum(s['hits'] for s in recent_3_starts) * 9 / total_innings_3, 1) if total_innings_3 > 0 else 0,
                'quality_starts': sum(s['quality_start'] for s in recent_3_starts)
            },
            'last_5_starts': {
                'era': round(sum(s['earned_runs'] for s in all_5_starts) * 9 / total_innings_5, 2) if total_innings_5 > 0 else 0,
                'whip': round(sum(s['hits'] + s['walks'] for s in all_5_starts) / total_innings_5, 2) if total_innings_5 > 0 else 0,
                'shutouts': len([s for s in all_5_starts if s['earned_runs'] == 0]),
                'low_hit_games': len([s for s in all_5_starts if s['hits'] <= 5])
            },
            'individual_starts': starts
        }
        
        return performance_summary
    
    def analyze_no_hitter_pitcher_patterns(self, no_hitter_df):
        """Analyze pitcher performance patterns before no-hitters"""
        cache = self.load_pitcher_cache()
        pitcher_data = []
        
        for _, row in no_hitter_df.iterrows():
            cache_key = f"{row['pitcher']}_{row['date']}_{row['team']}"
            
            if cache_key in cache:
                performance = cache[cache_key]
            else:
                performance = self.simulate_pitcher_performance(row['pitcher'], row['date'], row['team'])
                cache[cache_key] = performance
            
            pitcher_data.append(performance)
        
        # Save updated cache
        self.save_pitcher_cache(cache)
        
        if not pitcher_data:
            return None
        
        # Analyze patterns across all no-hitter pitchers
        patterns = self.calculate_pitcher_patterns(pitcher_data)
        
        logger.info(f"Pitcher analysis complete: {len(pitcher_data)} no-hitters analyzed")
        return patterns, pitcher_data
    
    def calculate_pitcher_patterns(self, pitcher_data):
        """Calculate common patterns among no-hitter pitchers"""
        if not pitcher_data:
            return None
        
        # Extract metrics for analysis
        recent_3_stats = [p['recent_3_starts'] for p in pitcher_data]
        last_5_stats = [p['last_5_starts'] for p in pitcher_data]
        
        patterns = {
            'recent_3_starts_avg': {
                'era': np.mean([s['era'] for s in recent_3_stats]),
                'whip': np.mean([s['whip'] for s in recent_3_stats]),
                'k_per_nine': np.mean([s['k_per_nine'] for s in recent_3_stats]),
                'h_per_nine': np.mean([s['h_per_nine'] for s in recent_3_stats]),
                'quality_starts': np.mean([s['quality_starts'] for s in recent_3_stats])
            },
            'last_5_starts_avg': {
                'era': np.mean([s['era'] for s in last_5_stats]),
                'whip': np.mean([s['whip'] for s in last_5_stats]),
                'shutouts': np.mean([s['shutouts'] for s in last_5_stats]),
                'low_hit_games': np.mean([s['low_hit_games'] for s in last_5_stats])
            },
            'hot_streak_indicators': {
                'pct_era_under_2_50': len([s for s in recent_3_stats if s['era'] <= 2.50]) / len(recent_3_stats) * 100,
                'pct_whip_under_1_00': len([s for s in recent_3_stats if s['whip'] <= 1.00]) / len(recent_3_stats) * 100,
                'pct_high_k_rate': len([s for s in recent_3_stats if s['k_per_nine'] >= 8.5]) / len(recent_3_stats) * 100,
                'pct_2_plus_quality_starts': len([s for s in recent_3_stats if s['quality_starts'] >= 2]) / len(recent_3_stats) * 100
            },
            'form_thresholds': {
                'era_threshold': np.percentile([s['era'] for s in recent_3_stats], 75),  # 75th percentile
                'whip_threshold': np.percentile([s['whip'] for s in recent_3_stats], 25), # 25th percentile (lower is better)
                'k_rate_threshold': np.percentile([s['k_per_nine'] for s in recent_3_stats], 60),
                'quality_starts_threshold': np.percentile([s['quality_starts'] for s in recent_3_stats], 70)
            }
        }
        
        return patterns
    
    def calculate_pitcher_form_factor(self, current_pitcher_stats, patterns):
        """Calculate pitcher form adjustment factor"""
        if not current_pitcher_stats or not patterns:
            return 1.0
        
        factor = 1.0
        thresholds = patterns['form_thresholds']
        
        # Recent ERA factor
        if current_pitcher_stats.get('recent_era', 4.0) <= thresholds['era_threshold']:
            factor *= 1.3  # Strong boost for good recent ERA
        elif current_pitcher_stats.get('recent_era', 4.0) > 4.5:
            factor *= 0.8  # Penalty for poor ERA
        
        # WHIP factor
        if current_pitcher_stats.get('recent_whip', 1.4) <= thresholds['whip_threshold']:
            factor *= 1.2  # Boost for low WHIP
        elif current_pitcher_stats.get('recent_whip', 1.4) > 1.5:
            factor *= 0.85  # Penalty for high WHIP
        
        # Strikeout rate factor
        if current_pitcher_stats.get('k_per_nine', 7.0) >= thresholds['k_rate_threshold']:
            factor *= 1.15  # Boost for high K rate
        
        # Quality starts factor
        if current_pitcher_stats.get('quality_starts', 1) >= thresholds['quality_starts_threshold']:
            factor *= 1.1  # Boost for consistent quality starts
        
        # Hot streak bonus
        if (current_pitcher_stats.get('recent_era', 4.0) <= 2.5 and 
            current_pitcher_stats.get('recent_whip', 1.4) <= 1.0 and
            current_pitcher_stats.get('quality_starts', 1) >= 2):
            factor *= 1.4  # Significant boost for hot streak
        
        # Cap the factor
        factor = max(0.6, min(2.5, factor))
        
        return factor
    
    def simulate_current_pitcher_form(self, team_pitchers=None):
        """Simulate current pitcher form for prediction"""
        # In a real implementation, this would fetch current MLB pitcher stats
        # For now, we'll simulate "typical" pitcher performance
        
        import random
        random.seed(int(datetime.now().timestamp()) % 1000)
        
        # Simulate a pitcher having good recent form
        simulated_stats = {
            'recent_era': random.uniform(2.0, 4.5),
            'recent_whip': random.uniform(0.9, 1.6),
            'k_per_nine': random.uniform(6.5, 12.0),
            'quality_starts': random.randint(0, 3),
            'pitcher_name': 'Today\'s Starter'  # Placeholder
        }
        
        return simulated_stats
    
    def get_pitcher_explanation(self, current_stats, factor, patterns):
        """Generate explanation for pitcher form factor"""
        if not current_stats:
            return "Pitcher form data unavailable"
        
        explanations = []
        thresholds = patterns.get('form_thresholds', {})
        
        recent_era = current_stats.get('recent_era', 4.0)
        if recent_era <= thresholds.get('era_threshold', 3.5):
            explanations.append(f"strong recent ERA ({recent_era:.2f})")
        elif recent_era > 4.5:
            explanations.append(f"elevated ERA ({recent_era:.2f})")
        
        recent_whip = current_stats.get('recent_whip', 1.4)
        if recent_whip <= thresholds.get('whip_threshold', 1.2):
            explanations.append(f"excellent control (WHIP {recent_whip:.2f})")
        elif recent_whip > 1.5:
            explanations.append(f"control issues (WHIP {recent_whip:.2f})")
        
        k_rate = current_stats.get('k_per_nine', 7.0)
        if k_rate >= thresholds.get('k_rate_threshold', 8.0):
            explanations.append(f"high strikeout rate ({k_rate:.1f} K/9)")
        
        quality_starts = current_stats.get('quality_starts', 1)
        if quality_starts >= 2:
            explanations.append(f"consistent quality starts ({quality_starts}/3)")
        
        # Check for hot streak
        if (recent_era <= 2.5 and recent_whip <= 1.0 and quality_starts >= 2):
            explanations.append("pitcher on hot streak")
        
        if not explanations:
            explanations.append("average recent form")
        
        return f"Pitcher form: {', '.join(explanations)}"

if __name__ == "__main__":
    analyzer = PitcherPerformanceAnalyzer()
    
    # Test with sample data
    sample_df = pd.DataFrame([
        {'date': '2023-09-01', 'team': 'NYY', 'pitcher': 'Domingo German'},
        {'date': '2022-06-29', 'team': 'HOU', 'pitcher': 'Cristian Javier'}
    ])
    
    patterns, pitcher_data = analyzer.analyze_no_hitter_pitcher_patterns(sample_df)
    print("Pitcher analysis completed successfully!")