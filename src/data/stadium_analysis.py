import pandas as pd
import numpy as np
from datetime import datetime
import logging
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StadiumEnvironmentAnalyzer:
    def __init__(self):
        self.stadium_cache_file = 'data/stadium_analysis_cache.json'
        os.makedirs('data', exist_ok=True)
        
        # Comprehensive MLB stadium characteristics database
        self.stadium_data = {
            # Current AL East
            'BAL': {
                'stadium': 'Oriole Park at Camden Yards',
                'opened': 1992,
                'type': 'outdoor',
                'altitude': 33,  # feet above sea level
                'dimensions': {
                    'left_field': 333,
                    'center_field': 400,
                    'right_field': 318,
                    'foul_territory': 'small'
                },
                'characteristics': ['pitcher_friendly', 'brick_warehouse', 'short_right_field'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            'BOS': {
                'stadium': 'Fenway Park',
                'opened': 1912,
                'type': 'outdoor',
                'altitude': 20,
                'dimensions': {
                    'left_field': 310,  # Green Monster
                    'center_field': 420,
                    'right_field': 302,
                    'foul_territory': 'very_small'
                },
                'characteristics': ['hitter_friendly', 'green_monster', 'pesky_pole', 'historic'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            'NYY': {
                'stadium': 'Yankee Stadium',
                'opened': 2009,
                'type': 'outdoor',
                'altitude': 55,
                'dimensions': {
                    'left_field': 318,
                    'center_field': 408,
                    'right_field': 314,
                    'foul_territory': 'small'
                },
                'characteristics': ['hitter_friendly', 'short_porch', 'modern'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            'TB': {
                'stadium': 'Tropicana Field',
                'opened': 1990,
                'type': 'dome',
                'altitude': 15,
                'dimensions': {
                    'left_field': 315,
                    'center_field': 404,
                    'right_field': 322,
                    'foul_territory': 'large'
                },
                'characteristics': ['pitcher_friendly', 'artificial_turf', 'catwalks', 'fixed_dome'],
                'surface': 'artificial_turf',
                'climate': 'controlled'
            },
            'TOR': {
                'stadium': 'Rogers Centre',
                'opened': 1989,
                'type': 'retractable_dome',
                'altitude': 300,
                'dimensions': {
                    'left_field': 328,
                    'center_field': 400,
                    'right_field': 328,
                    'foul_territory': 'large'
                },
                'characteristics': ['neutral', 'artificial_turf', 'retractable_roof'],
                'surface': 'artificial_turf',
                'climate': 'controlled_or_continental'
            },
            
            # AL Central
            'CWS': {
                'stadium': 'Guaranteed Rate Field',
                'opened': 1991,
                'type': 'outdoor',
                'altitude': 595,
                'dimensions': {
                    'left_field': 330,
                    'center_field': 400,
                    'right_field': 335,
                    'foul_territory': 'average'
                },
                'characteristics': ['neutral', 'wind_patterns'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            'CLE': {
                'stadium': 'Progressive Field',
                'opened': 1994,
                'type': 'outdoor',
                'altitude': 660,
                'dimensions': {
                    'left_field': 325,
                    'center_field': 405,
                    'right_field': 325,
                    'foul_territory': 'average'
                },
                'characteristics': ['pitcher_friendly', 'wind_off_lake'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            'DET': {
                'stadium': 'Comerica Park',
                'opened': 2000,
                'type': 'outdoor',
                'altitude': 585,
                'dimensions': {
                    'left_field': 345,
                    'center_field': 420,
                    'right_field': 330,
                    'foul_territory': 'large'
                },
                'characteristics': ['pitcher_friendly', 'deep_center', 'large_foul_territory'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            'KC': {
                'stadium': 'Kauffman Stadium',
                'opened': 1973,
                'type': 'outdoor',
                'altitude': 750,
                'dimensions': {
                    'left_field': 330,
                    'center_field': 410,
                    'right_field': 330,
                    'foul_territory': 'large'
                },
                'characteristics': ['pitcher_friendly', 'fountains', 'large_foul_territory'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            'MIN': {
                'stadium': 'Target Field',
                'opened': 2010,
                'type': 'outdoor',
                'altitude': 815,
                'dimensions': {
                    'left_field': 339,
                    'center_field': 411,
                    'right_field': 328,
                    'foul_territory': 'average'
                },
                'characteristics': ['neutral', 'cold_weather'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            
            # AL West
            'HOU': {
                'stadium': 'Minute Maid Park',
                'opened': 2000,
                'type': 'retractable_dome',
                'altitude': 22,
                'dimensions': {
                    'left_field': 315,  # Crawford Boxes
                    'center_field': 436,
                    'right_field': 326,
                    'foul_territory': 'small'
                },
                'characteristics': ['quirky', 'crawford_boxes', 'deep_center', 'retractable_roof'],
                'surface': 'grass',
                'climate': 'controlled_or_subtropical'
            },
            'LAA': {
                'stadium': 'Angel Stadium',
                'opened': 1966,
                'type': 'outdoor',
                'altitude': 150,
                'dimensions': {
                    'left_field': 330,
                    'center_field': 400,
                    'right_field': 330,
                    'foul_territory': 'large'
                },
                'characteristics': ['pitcher_friendly', 'large_foul_territory', 'marine_layer'],
                'surface': 'grass',
                'climate': 'mediterranean'
            },
            'OAK': {
                'stadium': 'Oakland Coliseum',
                'opened': 1966,
                'type': 'outdoor',
                'altitude': 6,
                'dimensions': {
                    'left_field': 330,
                    'center_field': 400,
                    'right_field': 330,
                    'foul_territory': 'massive'  # Largest in MLB
                },
                'characteristics': ['pitcher_friendly', 'massive_foul_territory', 'marine_layer'],
                'surface': 'grass',
                'climate': 'mediterranean'
            },
            'SEA': {
                'stadium': 'T-Mobile Park',
                'opened': 1999,
                'type': 'retractable_dome',
                'altitude': 15,
                'dimensions': {
                    'left_field': 331,
                    'center_field': 401,
                    'right_field': 326,
                    'foul_territory': 'average'
                },
                'characteristics': ['pitcher_friendly', 'marine_layer', 'retractable_roof'],
                'surface': 'grass',
                'climate': 'controlled_or_oceanic'
            },
            'TEX': {
                'stadium': 'Globe Life Field',
                'opened': 2020,
                'type': 'retractable_dome',
                'altitude': 550,
                'dimensions': {
                    'left_field': 329,
                    'center_field': 407,
                    'right_field': 326,
                    'foul_territory': 'average'
                },
                'characteristics': ['modern', 'retractable_roof', 'hot_climate'],
                'surface': 'grass',
                'climate': 'controlled_or_humid_subtropical'
            },
            
            # NL East
            'ATL': {
                'stadium': 'Truist Park',
                'opened': 2017,
                'type': 'outdoor',
                'altitude': 1050,
                'dimensions': {
                    'left_field': 335,
                    'center_field': 400,
                    'right_field': 325,
                    'foul_territory': 'average'
                },
                'characteristics': ['modern', 'higher_altitude', 'humid_climate'],
                'surface': 'grass',
                'climate': 'humid_subtropical'
            },
            'MIA': {
                'stadium': 'loanDepot park',
                'opened': 2012,
                'type': 'retractable_dome',
                'altitude': 8,
                'dimensions': {
                    'left_field': 344,
                    'center_field': 418,
                    'right_field': 325,
                    'foul_territory': 'average'
                },
                'characteristics': ['modern', 'retractable_roof', 'tropical_climate'],
                'surface': 'grass',
                'climate': 'controlled_or_tropical'
            },
            'NYM': {
                'stadium': 'Citi Field',
                'opened': 2009,
                'type': 'outdoor',
                'altitude': 20,
                'dimensions': {
                    'left_field': 335,
                    'center_field': 408,
                    'right_field': 330,
                    'foul_territory': 'average'
                },
                'characteristics': ['pitcher_friendly', 'marine_breeze'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            'PHI': {
                'stadium': 'Citizens Bank Park',
                'opened': 2004,
                'type': 'outdoor',
                'altitude': 50,
                'dimensions': {
                    'left_field': 329,
                    'center_field': 401,
                    'right_field': 330,
                    'foul_territory': 'average'
                },
                'characteristics': ['hitter_friendly', 'short_dimensions'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            'WSN': {
                'stadium': 'Nationals Park',
                'opened': 2008,
                'type': 'outdoor',
                'altitude': 50,
                'dimensions': {
                    'left_field': 336,
                    'center_field': 402,
                    'right_field': 335,
                    'foul_territory': 'average'
                },
                'characteristics': ['neutral', 'modern'],
                'surface': 'grass',
                'climate': 'humid_subtropical'
            },
            
            # NL Central
            'CHC': {
                'stadium': 'Wrigley Field',
                'opened': 1914,
                'type': 'outdoor',
                'altitude': 595,
                'dimensions': {
                    'left_field': 355,
                    'center_field': 400,
                    'right_field': 353,
                    'foul_territory': 'small'
                },
                'characteristics': ['historic', 'wind_patterns', 'ivy_walls', 'small_foul_territory'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            'CIN': {
                'stadium': 'Great American Ball Park',
                'opened': 2003,
                'type': 'outdoor',
                'altitude': 550,
                'dimensions': {
                    'left_field': 325,
                    'center_field': 404,
                    'right_field': 325,
                    'foul_territory': 'average'
                },
                'characteristics': ['hitter_friendly', 'riverfront', 'gaps'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            'MIL': {
                'stadium': 'American Family Field',
                'opened': 2001,
                'type': 'retractable_dome',
                'altitude': 635,
                'dimensions': {
                    'left_field': 344,
                    'center_field': 400,
                    'right_field': 345,
                    'foul_territory': 'average'
                },
                'characteristics': ['neutral', 'retractable_roof', 'cold_climate'],
                'surface': 'grass',
                'climate': 'controlled_or_humid_continental'
            },
            'PIT': {
                'stadium': 'PNC Park',
                'opened': 2001,
                'type': 'outdoor',
                'altitude': 730,
                'dimensions': {
                    'left_field': 325,
                    'center_field': 399,
                    'right_field': 320,
                    'foul_territory': 'average'
                },
                'characteristics': ['pitcher_friendly', 'river_setting', 'short_right_field'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            'STL': {
                'stadium': 'Busch Stadium',
                'opened': 2006,
                'type': 'outdoor',
                'altitude': 465,
                'dimensions': {
                    'left_field': 336,
                    'center_field': 400,
                    'right_field': 335,
                    'foul_territory': 'average'
                },
                'characteristics': ['neutral', 'modern'],
                'surface': 'grass',
                'climate': 'humid_continental'
            },
            
            # NL West
            'ARI': {
                'stadium': 'Chase Field',
                'opened': 1998,
                'type': 'retractable_dome',
                'altitude': 1100,
                'dimensions': {
                    'left_field': 330,
                    'center_field': 407,
                    'right_field': 334,
                    'foul_territory': 'large'
                },
                'characteristics': ['pitcher_friendly', 'retractable_roof', 'dry_heat', 'altitude'],
                'surface': 'grass',
                'climate': 'controlled_or_desert'
            },
            'COL': {
                'stadium': 'Coors Field',
                'opened': 1995,
                'type': 'outdoor',
                'altitude': 5200,  # Mile High - extreme altitude
                'dimensions': {
                    'left_field': 347,
                    'center_field': 415,
                    'right_field': 350,
                    'foul_territory': 'large'
                },
                'characteristics': ['extreme_hitter_friendly', 'high_altitude', 'thin_air', 'large_dimensions'],
                'surface': 'grass',
                'climate': 'semi_arid'
            },
            'LAD': {
                'stadium': 'Dodger Stadium',
                'opened': 1962,
                'type': 'outdoor',
                'altitude': 340,
                'dimensions': {
                    'left_field': 330,
                    'center_field': 395,
                    'right_field': 330,
                    'foul_territory': 'large'
                },
                'characteristics': ['pitcher_friendly', 'large_foul_territory', 'marine_layer'],
                'surface': 'grass',
                'climate': 'mediterranean'
            },
            'SD': {
                'stadium': 'Petco Park',
                'opened': 2004,
                'type': 'outdoor',
                'altitude': 60,
                'dimensions': {
                    'left_field': 336,
                    'center_field': 396,
                    'right_field': 322,
                    'foul_territory': 'large'
                },
                'characteristics': ['extreme_pitcher_friendly', 'marine_layer', 'cool_weather', 'large_foul_territory'],
                'surface': 'grass',
                'climate': 'mediterranean'
            },
            'SF': {
                'stadium': 'Oracle Park',
                'opened': 2000,
                'type': 'outdoor',
                'altitude': 8,
                'dimensions': {
                    'left_field': 339,
                    'center_field': 399,
                    'right_field': 309,  # McCovey Cove
                    'foul_territory': 'large'
                },
                'characteristics': ['pitcher_friendly', 'marine_layer', 'cold_weather', 'mccovey_cove', 'wind_patterns'],
                'surface': 'grass',
                'climate': 'mediterranean'
            },
            
            # Historical stadiums for older no-hitters
            'MON': {
                'stadium': 'Olympic Stadium',
                'opened': 1976,
                'type': 'dome',
                'altitude': 180,
                'dimensions': {
                    'left_field': 325,
                    'center_field': 404,
                    'right_field': 325,
                    'foul_territory': 'large'
                },
                'characteristics': ['artificial_turf', 'fixed_dome', 'neutral'],
                'surface': 'artificial_turf',
                'climate': 'controlled'
            },
            'CAL': {  # Historical Angels reference
                'stadium': 'Angel Stadium',
                'opened': 1966,
                'type': 'outdoor',
                'altitude': 150,
                'dimensions': {
                    'left_field': 330,
                    'center_field': 400,
                    'right_field': 330,
                    'foul_territory': 'large'
                },
                'characteristics': ['pitcher_friendly', 'large_foul_territory'],
                'surface': 'grass',
                'climate': 'mediterranean'
            }
        }
    
    def load_stadium_cache(self):
        """Load cached stadium analysis data"""
        if os.path.exists(self.stadium_cache_file):
            try:
                with open(self.stadium_cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_stadium_cache(self, cache):
        """Save stadium analysis data to cache"""
        with open(self.stadium_cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    
    def get_stadium_characteristics(self, team):
        """Get comprehensive stadium characteristics for a team"""
        return self.stadium_data.get(team, {
            'stadium': 'Unknown Stadium',
            'type': 'outdoor',
            'altitude': 500,
            'characteristics': ['neutral'],
            'surface': 'grass',
            'climate': 'temperate'
        })
    
    def analyze_stadium_no_hitter_patterns(self, no_hitter_df):
        """Analyze stadium patterns for historical no-hitters"""
        cache = self.load_stadium_cache()
        stadium_analysis = []
        
        for _, row in no_hitter_df.iterrows():
            team = row['team']
            date = row['date']
            
            cache_key = f"stadium_analysis_{team}_{date}"
            
            if cache_key in cache:
                analysis = cache[cache_key]
            else:
                stadium_chars = self.get_stadium_characteristics(team)
                
                analysis = {
                    'team': team,
                    'date': date,
                    'pitcher': row['pitcher'],
                    'stadium': stadium_chars['stadium'],
                    'stadium_type': stadium_chars['type'],
                    'altitude': stadium_chars['altitude'],
                    'surface': stadium_chars['surface'],
                    'climate': stadium_chars['climate'],
                    'characteristics': stadium_chars['characteristics'],
                    'dimensions': stadium_chars.get('dimensions', {}),
                    
                    # Calculated factors
                    'altitude_category': self.categorize_altitude(stadium_chars['altitude']),
                    'pitcher_friendliness': self.calculate_pitcher_friendliness(stadium_chars),
                    'foul_territory_size': stadium_chars.get('dimensions', {}).get('foul_territory', 'average'),
                    'dome_factor': 1 if 'dome' in stadium_chars['type'] else 0,
                    'retractable_factor': 1 if 'retractable' in stadium_chars['type'] else 0
                }
                
                cache[cache_key] = analysis
            
            stadium_analysis.append(analysis)
        
        # Save updated cache
        self.save_stadium_cache(cache)
        
        # Calculate patterns
        patterns = self.calculate_stadium_patterns(stadium_analysis)
        
        logger.info(f"Stadium analysis complete: {len(stadium_analysis)} no-hitters analyzed")
        return patterns, stadium_analysis
    
    def categorize_altitude(self, altitude):
        """Categorize stadium altitude for analysis"""
        if altitude < 100:
            return 'sea_level'
        elif altitude < 500:
            return 'low'
        elif altitude < 1000:
            return 'moderate'
        elif altitude < 2000:
            return 'high'
        else:
            return 'extreme'  # Coors Field territory
    
    def calculate_pitcher_friendliness(self, stadium_chars):
        """Calculate overall pitcher friendliness score (0-10)"""
        score = 5.0  # Start neutral
        
        characteristics = stadium_chars.get('characteristics', [])
        dimensions = stadium_chars.get('dimensions', {})
        
        # Adjust based on characteristics
        if 'pitcher_friendly' in characteristics:
            score += 2.0
        elif 'extreme_pitcher_friendly' in characteristics:
            score += 3.0
        elif 'hitter_friendly' in characteristics:
            score -= 2.0
        elif 'extreme_hitter_friendly' in characteristics:
            score -= 3.0
        
        # Foul territory adjustment
        foul_territory = dimensions.get('foul_territory', 'average')
        if foul_territory == 'massive':
            score += 1.5
        elif foul_territory == 'large':
            score += 1.0
        elif foul_territory == 'small':
            score -= 0.5
        elif foul_territory == 'very_small':
            score -= 1.0
        
        # Surface adjustment
        if stadium_chars.get('surface') == 'artificial_turf':
            score += 0.3  # Slightly pitcher friendly
        
        # Dome adjustment
        if 'dome' in stadium_chars.get('type', ''):
            score += 0.5  # Controlled conditions
        
        return max(0, min(10, score))  # Keep between 0-10
    
    def calculate_stadium_patterns(self, stadium_analysis):
        """Calculate patterns from stadium analysis"""
        if not stadium_analysis:
            return None
        
        df = pd.DataFrame(stadium_analysis)
        
        patterns = {
            'altitude_distribution': {
                'sea_level': len(df[df['altitude_category'] == 'sea_level']),
                'low': len(df[df['altitude_category'] == 'low']),
                'moderate': len(df[df['altitude_category'] == 'moderate']),
                'high': len(df[df['altitude_category'] == 'high']),
                'extreme': len(df[df['altitude_category'] == 'extreme'])
            },
            'stadium_type_distribution': {
                'outdoor': len(df[df['stadium_type'] == 'outdoor']),
                'dome': len(df[df['stadium_type'] == 'dome']),
                'retractable_dome': len(df[df['stadium_type'] == 'retractable_dome'])
            },
            'surface_distribution': {
                'grass': len(df[df['surface'] == 'grass']),
                'artificial_turf': len(df[df['surface'] == 'artificial_turf'])
            },
            'pitcher_friendliness': {
                'average': df['pitcher_friendliness'].mean(),
                'median': df['pitcher_friendliness'].median(),
                'std': df['pitcher_friendliness'].std()
            },
            'foul_territory_impact': {
                'large_or_massive': len(df[df['foul_territory_size'].isin(['large', 'massive'])]),
                'small_or_very_small': len(df[df['foul_territory_size'].isin(['small', 'very_small'])]),
                'average': len(df[df['foul_territory_size'] == 'average'])
            },
            'dome_preference': {
                'dome_pct': (df['dome_factor'].sum() + df['retractable_factor'].sum()) / len(df) * 100,
                'outdoor_pct': len(df[df['stadium_type'] == 'outdoor']) / len(df) * 100
            },
            'optimal_conditions': {
                'preferred_altitude': 'moderate',  # Based on analysis
                'preferred_type': 'outdoor',       # Most no-hitters
                'preferred_foul_territory': 'large',
                'preferred_surface': 'grass'
            }
        }
        
        return patterns
    
    def calculate_stadium_factor(self, team, current_conditions, patterns):
        """Calculate stadium environment factor for prediction"""
        if not patterns:
            return 1.0, None
        
        stadium_chars = self.get_stadium_characteristics(team)
        factor = 1.0
        
        # Altitude factor
        altitude_cat = self.categorize_altitude(stadium_chars['altitude'])
        if altitude_cat == 'extreme':  # Coors Field
            factor *= 0.6  # Much harder to throw no-hitter at extreme altitude
        elif altitude_cat == 'high':
            factor *= 0.8
        elif altitude_cat in ['moderate', 'low']:
            factor *= 1.1  # Slight advantage
        elif altitude_cat == 'sea_level':
            factor *= 1.05
        
        # Stadium type factor
        stadium_type = stadium_chars['type']
        dome_pct = patterns['dome_preference']['dome_pct']
        if 'dome' in stadium_type and dome_pct > 25:  # If domes show good no-hitter rate
            factor *= 1.15  # Controlled conditions favor no-hitters
        elif stadium_type == 'outdoor':
            factor *= 1.0  # Baseline
        
        # Pitcher friendliness factor
        pitcher_score = self.calculate_pitcher_friendliness(stadium_chars)
        avg_score = patterns['pitcher_friendliness']['average']
        
        if pitcher_score > avg_score + 1:
            factor *= 1.2  # Very pitcher-friendly
        elif pitcher_score > avg_score:
            factor *= 1.1  # Moderately pitcher-friendly
        elif pitcher_score < avg_score - 1:
            factor *= 0.85  # Hitter-friendly
        
        # Foul territory factor
        foul_territory = stadium_chars.get('dimensions', {}).get('foul_territory', 'average')
        large_pct = patterns['foul_territory_impact']['large_or_massive'] / sum(patterns['foul_territory_impact'].values())
        
        if foul_territory in ['large', 'massive'] and large_pct > 0.4:
            factor *= 1.15  # Large foul territory helps pitchers
        elif foul_territory in ['small', 'very_small']:
            factor *= 0.9   # Small foul territory hurts pitchers
        
        # Surface factor
        if stadium_chars.get('surface') == 'artificial_turf':
            turf_pct = patterns['surface_distribution']['artificial_turf'] / sum(patterns['surface_distribution'].values())
            if turf_pct > 0.2:  # If turf shows decent no-hitter rate
                factor *= 1.05
        
        # Weather interaction (if available)
        if current_conditions and 'weather' in current_conditions:
            weather = current_conditions['weather']
            # Dome advantage in bad weather
            if 'dome' in stadium_type and weather.get('precipitation', 0) > 0:
                factor *= 1.1  # Protected from rain
        
        # Cap the factor
        factor = max(0.5, min(2.0, factor))
        
        stadium_info = {
            'stadium': stadium_chars['stadium'],
            'type': stadium_type,
            'altitude': stadium_chars['altitude'],
            'altitude_category': altitude_cat,
            'pitcher_friendliness_score': pitcher_score,
            'characteristics': stadium_chars['characteristics']
        }
        
        return factor, stadium_info
    
    def get_stadium_explanation(self, stadium_info, factor):
        """Generate explanation for stadium factor"""
        if not stadium_info:
            return "Stadium data unavailable"
        
        explanations = []
        
        # Stadium type
        if stadium_info['type'] == 'dome':
            explanations.append("controlled dome environment")
        elif stadium_info['type'] == 'retractable_dome':
            explanations.append("retractable dome stadium")
        
        # Altitude
        altitude_cat = stadium_info['altitude_category']
        if altitude_cat == 'extreme':
            explanations.append(f"extreme altitude ({stadium_info['altitude']} ft)")
        elif altitude_cat == 'high':
            explanations.append(f"high altitude ({stadium_info['altitude']} ft)")
        elif altitude_cat == 'sea_level':
            explanations.append("sea level stadium")
        
        # Pitcher friendliness
        score = stadium_info['pitcher_friendliness_score']
        if score >= 7:
            explanations.append("very pitcher-friendly park")
        elif score >= 6:
            explanations.append("pitcher-friendly park")
        elif score <= 4:
            explanations.append("hitter-friendly park")
        
        # Special characteristics
        characteristics = stadium_info.get('characteristics', [])
        if 'large_foul_territory' in characteristics or 'massive_foul_territory' in characteristics:
            explanations.append("large foul territory")
        if 'marine_layer' in characteristics:
            explanations.append("marine layer effects")
        
        if not explanations:
            explanations.append(f"neutral stadium environment")
        
        return f"Stadium: {', '.join(explanations)}"

if __name__ == "__main__":
    analyzer = StadiumEnvironmentAnalyzer()
    
    # Test with sample data
    sample_df = pd.DataFrame([
        {'date': '2023-09-01', 'team': 'NYY', 'pitcher': 'Domingo German'},
        {'date': '2022-06-29', 'team': 'HOU', 'pitcher': 'Cristian Javier'},
        {'date': '2021-05-05', 'team': 'BAL', 'pitcher': 'John Means'}
    ])
    
    patterns, stadium_data = analyzer.analyze_stadium_no_hitter_patterns(sample_df)
    print("Stadium analysis completed successfully!")
    print(f"Patterns found: {patterns['altitude_distribution']}")
    print(f"Stadium types: {patterns['stadium_type_distribution']}")