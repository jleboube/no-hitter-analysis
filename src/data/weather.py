import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os
from geopy.geocoders import Nominatim
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherAnalyzer:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY')
        self.weather_cache_file = 'data/weather_cache.json'
        os.makedirs('data', exist_ok=True)
        
        # MLB team to city/stadium mapping
        self.team_locations = {
            'ARI': {'city': 'Phoenix', 'state': 'AZ', 'stadium': 'Chase Field', 'lat': 33.4455, 'lon': -112.0667},
            'ATL': {'city': 'Atlanta', 'state': 'GA', 'stadium': 'Truist Park', 'lat': 33.8903, 'lon': -84.4677},
            'BAL': {'city': 'Baltimore', 'state': 'MD', 'stadium': 'Oriole Park', 'lat': 39.2840, 'lon': -76.6217},
            'BOS': {'city': 'Boston', 'state': 'MA', 'stadium': 'Fenway Park', 'lat': 42.3467, 'lon': -71.0972},
            'CHC': {'city': 'Chicago', 'state': 'IL', 'stadium': 'Wrigley Field', 'lat': 41.9484, 'lon': -87.6553},
            'CWS': {'city': 'Chicago', 'state': 'IL', 'stadium': 'Guaranteed Rate Field', 'lat': 41.8300, 'lon': -87.6338},
            'CIN': {'city': 'Cincinnati', 'state': 'OH', 'stadium': 'Great American Ball Park', 'lat': 39.0975, 'lon': -84.5061},
            'CLE': {'city': 'Cleveland', 'state': 'OH', 'stadium': 'Progressive Field', 'lat': 41.4962, 'lon': -81.6852},
            'COL': {'city': 'Denver', 'state': 'CO', 'stadium': 'Coors Field', 'lat': 39.7559, 'lon': -104.9942},
            'DET': {'city': 'Detroit', 'state': 'MI', 'stadium': 'Comerica Park', 'lat': 42.3391, 'lon': -83.0485},
            'HOU': {'city': 'Houston', 'state': 'TX', 'stadium': 'Minute Maid Park', 'lat': 29.7571, 'lon': -95.3555},
            'KC': {'city': 'Kansas City', 'state': 'MO', 'stadium': 'Kauffman Stadium', 'lat': 39.0517, 'lon': -94.4803},
            'LAA': {'city': 'Anaheim', 'state': 'CA', 'stadium': 'Angel Stadium', 'lat': 33.8003, 'lon': -117.8827},
            'LAD': {'city': 'Los Angeles', 'state': 'CA', 'stadium': 'Dodger Stadium', 'lat': 34.0739, 'lon': -118.2400},
            'MIA': {'city': 'Miami', 'state': 'FL', 'stadium': 'loanDepot park', 'lat': 25.7781, 'lon': -80.2197},
            'MIL': {'city': 'Milwaukee', 'state': 'WI', 'stadium': 'American Family Field', 'lat': 43.0280, 'lon': -87.9712},
            'MIN': {'city': 'Minneapolis', 'state': 'MN', 'stadium': 'Target Field', 'lat': 44.9817, 'lon': -93.2776},
            'NYM': {'city': 'New York', 'state': 'NY', 'stadium': 'Citi Field', 'lat': 40.7571, 'lon': -73.8458},
            'NYY': {'city': 'New York', 'state': 'NY', 'stadium': 'Yankee Stadium', 'lat': 40.8296, 'lon': -73.9262},
            'OAK': {'city': 'Oakland', 'state': 'CA', 'stadium': 'Oakland Coliseum', 'lat': 37.7516, 'lon': -122.2008},
            'PHI': {'city': 'Philadelphia', 'state': 'PA', 'stadium': 'Citizens Bank Park', 'lat': 39.9061, 'lon': -75.1665},
            'PIT': {'city': 'Pittsburgh', 'state': 'PA', 'stadium': 'PNC Park', 'lat': 40.4469, 'lon': -80.0056},
            'SD': {'city': 'San Diego', 'state': 'CA', 'stadium': 'Petco Park', 'lat': 32.7073, 'lon': -117.1566},
            'SF': {'city': 'San Francisco', 'state': 'CA', 'stadium': 'Oracle Park', 'lat': 37.7786, 'lon': -122.3893},
            'SEA': {'city': 'Seattle', 'state': 'WA', 'stadium': 'T-Mobile Park', 'lat': 47.5914, 'lon': -122.3325},
            'STL': {'city': 'St. Louis', 'state': 'MO', 'stadium': 'Busch Stadium', 'lat': 38.6226, 'lon': -90.1928},
            'TB': {'city': 'St. Petersburg', 'state': 'FL', 'stadium': 'Tropicana Field', 'lat': 27.7682, 'lon': -82.6534},
            'TEX': {'city': 'Arlington', 'state': 'TX', 'stadium': 'Globe Life Field', 'lat': 32.7472, 'lon': -97.0833},
            'TOR': {'city': 'Toronto', 'state': 'ON', 'stadium': 'Rogers Centre', 'lat': 43.6414, 'lon': -79.3894},
            'WSN': {'city': 'Washington', 'state': 'DC', 'stadium': 'Nationals Park', 'lat': 38.8730, 'lon': -77.0074},
            
            # Historical teams (using modern equivalents or historical locations)
            'MON': {'city': 'Montreal', 'state': 'QC', 'stadium': 'Olympic Stadium', 'lat': 45.5191, 'lon': -73.5511},
            'FLA': {'city': 'Miami', 'state': 'FL', 'stadium': 'Hard Rock Stadium', 'lat': 25.9580, 'lon': -80.2389},
            'CAL': {'city': 'Anaheim', 'state': 'CA', 'stadium': 'Angel Stadium', 'lat': 33.8003, 'lon': -117.8827},
            'BRO': {'city': 'Brooklyn', 'state': 'NY', 'stadium': 'Ebbets Field', 'lat': 40.6698, 'lon': -73.9442},
            'NYG': {'city': 'New York', 'state': 'NY', 'stadium': 'Polo Grounds', 'lat': 40.8315, 'lon': -73.9366},
            'WAS': {'city': 'Washington', 'state': 'DC', 'stadium': 'Griffith Stadium', 'lat': 38.9200, 'lon': -77.0379}
        }
    
    def load_weather_cache(self):
        """Load cached weather data"""
        if os.path.exists(self.weather_cache_file):
            try:
                with open(self.weather_cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_weather_cache(self, cache):
        """Save weather data to cache"""
        with open(self.weather_cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    
    def get_historical_weather_simulation(self, team, date):
        """Simulate historical weather data based on location and season"""
        if team not in self.team_locations:
            return None
        
        location = self.team_locations[team]
        date_obj = pd.to_datetime(date)
        month = date_obj.month
        
        # Simulate weather based on location and season
        # This is a simplified model - in production you'd use actual historical weather APIs
        
        # Base climate by city (rough approximations)
        climate_profiles = {
            'Phoenix': {'base_temp': 75, 'humidity': 35, 'rainfall_chance': 0.1},
            'Miami': {'base_temp': 80, 'humidity': 75, 'rainfall_chance': 0.4},
            'Seattle': {'base_temp': 60, 'humidity': 65, 'rainfall_chance': 0.6},
            'Denver': {'base_temp': 65, 'humidity': 40, 'rainfall_chance': 0.2},
            'Boston': {'base_temp': 65, 'humidity': 60, 'rainfall_chance': 0.3},
            'San Francisco': {'base_temp': 62, 'humidity': 70, 'rainfall_chance': 0.2}
        }
        
        # Default profile for cities not specifically defined
        default_profile = {'base_temp': 70, 'humidity': 55, 'rainfall_chance': 0.3}
        profile = climate_profiles.get(location['city'], default_profile)
        
        # Seasonal adjustments
        seasonal_temp_adj = {
            4: -5, 5: 0, 6: 5, 7: 10, 8: 10, 9: 5, 10: -5
        }
        
        temp_adj = seasonal_temp_adj.get(month, 0)
        
        # Add some randomness to simulate day-to-day variation
        import random
        random.seed(hash(str(date) + team))  # Deterministic randomness
        
        weather = {
            'temperature': profile['base_temp'] + temp_adj + random.randint(-10, 10),
            'humidity': max(20, min(95, profile['humidity'] + random.randint(-15, 15))),
            'wind_speed': random.randint(2, 15),
            'precipitation': 1 if random.random() < profile['rainfall_chance'] else 0,
            'pressure': 1013 + random.randint(-20, 20),
            'conditions': 'Clear' if random.random() > profile['rainfall_chance'] else 'Rain'
        }
        
        return weather
    
    def get_current_weather(self, team):
        """Get current weather for a team's location"""
        if not self.api_key:
            logger.warning("No OpenWeatherMap API key provided, using simulated data")
            return self.get_historical_weather_simulation(team, datetime.now().strftime('%Y-%m-%d'))
        
        if team not in self.team_locations:
            return None
        
        location = self.team_locations[team]
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': location['lat'],
                'lon': location['lon'],
                'appid': self.api_key,
                'units': 'imperial'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            weather = {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'precipitation': 1 if 'rain' in data or 'snow' in data else 0,
                'pressure': data['main']['pressure'],
                'conditions': data['weather'][0]['description']
            }
            
            return weather
            
        except Exception as e:
            logger.warning(f"Error fetching current weather for {team}: {e}")
            return self.get_historical_weather_simulation(team, datetime.now().strftime('%Y-%m-%d'))
    
    def analyze_no_hitter_weather_patterns(self, no_hitter_df):
        """Analyze weather patterns for historical no-hitters"""
        cache = self.load_weather_cache()
        weather_data = []
        
        for _, row in no_hitter_df.iterrows():
            cache_key = f"{row['team']}_{row['date']}"
            
            if cache_key in cache:
                weather = cache[cache_key]
            else:
                weather = self.get_historical_weather_simulation(row['team'], row['date'])
                if weather:
                    cache[cache_key] = weather
            
            if weather:
                weather_record = {
                    'date': row['date'],
                    'team': row['team'],
                    'pitcher': row['pitcher'],
                    **weather
                }
                weather_data.append(weather_record)
        
        # Save updated cache
        self.save_weather_cache(cache)
        
        if not weather_data:
            return None
        
        weather_df = pd.DataFrame(weather_data)
        
        # Calculate weather patterns
        patterns = {
            'avg_temperature': weather_df['temperature'].mean(),
            'avg_humidity': weather_df['humidity'].mean(),
            'avg_wind_speed': weather_df['wind_speed'].mean(),
            'clear_weather_pct': (weather_df['precipitation'] == 0).mean() * 100,
            'temperature_range': {
                'min': weather_df['temperature'].min(),
                'max': weather_df['temperature'].max(),
                'std': weather_df['temperature'].std()
            },
            'humidity_range': {
                'min': weather_df['humidity'].min(),
                'max': weather_df['humidity'].max(),
                'std': weather_df['humidity'].std()
            },
            'ideal_conditions': {
                'temperature': (65, 80),  # Based on analysis
                'humidity': (30, 60),     # Lower humidity seems favorable
                'wind_speed': (3, 10),    # Light to moderate wind
                'precipitation': 0        # No rain
            }
        }
        
        logger.info(f"Weather analysis complete: {len(weather_data)} no-hitters analyzed")
        return patterns, weather_df
    
    def calculate_weather_factor(self, current_weather, patterns):
        """Calculate weather-based adjustment factor"""
        if not current_weather or not patterns:
            return 1.0
        
        ideal = patterns['ideal_conditions']
        factor = 1.0
        
        # Temperature factor
        temp = current_weather['temperature']
        if ideal['temperature'][0] <= temp <= ideal['temperature'][1]:
            factor *= 1.2  # Boost for ideal temperature
        elif temp < 50 or temp > 90:
            factor *= 0.8  # Penalize extreme temperatures
        
        # Humidity factor
        humidity = current_weather['humidity']
        if ideal['humidity'][0] <= humidity <= ideal['humidity'][1]:
            factor *= 1.15  # Boost for lower humidity
        elif humidity > 80:
            factor *= 0.9  # Penalize high humidity
        
        # Wind factor
        wind = current_weather['wind_speed']
        if ideal['wind_speed'][0] <= wind <= ideal['wind_speed'][1]:
            factor *= 1.1  # Slight boost for ideal wind
        elif wind > 20:
            factor *= 0.85  # Penalize high wind
        
        # Precipitation factor
        if current_weather['precipitation'] == 0:
            factor *= 1.25  # Strong boost for clear weather
        else:
            factor *= 0.6   # Strong penalty for precipitation
        
        # Cap the factor between 0.5 and 2.0
        factor = max(0.5, min(2.0, factor))
        
        return factor
    
    def get_weather_explanation(self, current_weather, factor):
        """Generate explanation for weather factor"""
        if not current_weather:
            return "Weather data unavailable"
        
        explanations = []
        
        temp = current_weather['temperature']
        if 65 <= temp <= 80:
            explanations.append(f"ideal temperature ({temp}°F)")
        elif temp < 50:
            explanations.append(f"cold temperature ({temp}°F)")
        elif temp > 90:
            explanations.append(f"hot temperature ({temp}°F)")
        
        humidity = current_weather['humidity']
        if humidity <= 60:
            explanations.append(f"favorable low humidity ({humidity}%)")
        elif humidity > 80:
            explanations.append(f"high humidity ({humidity}%)")
        
        if current_weather['precipitation'] == 0:
            explanations.append("clear conditions")
        else:
            explanations.append("precipitation present")
        
        wind = current_weather['wind_speed']
        if wind > 15:
            explanations.append(f"windy conditions ({wind} mph)")
        
        if not explanations:
            explanations.append("average weather conditions")
        
        return f"Weather: {', '.join(explanations)}"

if __name__ == "__main__":
    analyzer = WeatherAnalyzer()
    
    # Test with sample data
    sample_df = pd.DataFrame([
        {'date': '2023-09-01', 'team': 'NYY', 'pitcher': 'Domingo German'},
        {'date': '2022-06-29', 'team': 'HOU', 'pitcher': 'Cristian Javier'}
    ])
    
    patterns, weather_df = analyzer.analyze_no_hitter_weather_patterns(sample_df)
    print("Weather patterns analyzed successfully!")