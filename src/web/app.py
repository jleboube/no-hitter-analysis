import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
from datetime import datetime, timedelta

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.collector import NoHitterDataCollector
from src.algorithm.predictor import NoHitterPredictor

st.set_page_config(
    page_title="No-Hitter Forecaster",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    """Load and cache the no-hitter data"""
    collector = NoHitterDataCollector()
    return collector.load_data()

@st.cache_data
def get_prediction(date_str=None):
    """Get prediction for a specific date"""
    predictor = NoHitterPredictor()
    return predictor.predict_probability(date_str)

def main():
    st.title("⚾ No-Hitter Forecaster")
    st.markdown("*Predicting the daily probability of MLB no-hitters using historical trends*")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Trends", "History", "About"])
    
    if page == "Home":
        show_home_page()
    elif page == "Trends":
        show_trends_page()
    elif page == "History":
        show_history_page()
    elif page == "About":
        show_about_page()

def show_home_page():
    """Display the main prediction page"""
    st.header("Today's No-Hitter Forecast")
    
    # Check if in season
    today = datetime.now().date()
    predictor = NoHitterPredictor()
    
    if not predictor.is_mlb_season(today):
        st.warning("⚠️ MLB is currently in the off-season. Predictions are available during the regular season (April-October).")
        st.info("You can still explore historical trends and data using the navigation menu.")
        return
    
    # Get today's prediction
    try:
        prediction = get_prediction()
        
        # Display main prediction
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.metric(
                label=f"Probability for {prediction['date']}",
                value=f"{prediction['probability_percent']:.2f}%",
                delta=f"±{(prediction['confidence_interval']['upper'] - prediction['confidence_interval']['lower'])/2:.1f}%"
            )
        
        with col2:
            if prediction['probability_percent'] > 3:
                st.success("High")
            elif prediction['probability_percent'] > 1.5:
                st.warning("Medium")
            else:
                st.info("Low")
            st.caption("Risk Level")
        
        with col3:
            st.metric(
                label="Confidence Interval",
                value=f"{prediction['confidence_interval']['lower']:.1f}% - {prediction['confidence_interval']['upper']:.1f}%"
            )
        
        # Explanation
        st.subheader("Why this percentage?")
        st.write(prediction['explanation'])
        
        # Factor breakdown
        st.subheader("Enhanced Factor Breakdown")
        factors = prediction['factors']
        
        # Enhanced factors including stadium
        factor_df = pd.DataFrame({
            'Factor': ['Base Rate', 'Monthly', 'Date-Specific', 'Decadal', 'Recency', 'Weather', 'Pitcher Form', 'Stadium Environment'],
            'Value': [
                factors['base_rate'],
                factors['monthly_factor'],
                factors['date_factor'],
                factors['decadal_factor'],
                factors['recency_adjustment'],
                factors.get('weather_factor', 1.0),
                factors.get('pitcher_factor', 1.0),
                factors.get('stadium_factor', 1.0)
            ],
            'Impact': [
                'Baseline',
                'Higher' if factors['monthly_factor'] > 1.05 else 'Lower' if factors['monthly_factor'] < 0.95 else 'Neutral',
                'Higher' if factors['date_factor'] > 1.05 else 'Neutral',
                'Higher' if factors['decadal_factor'] > 1.05 else 'Lower' if factors['decadal_factor'] < 0.95 else 'Neutral',
                'Higher' if factors['recency_adjustment'] > 1.05 else 'Neutral',
                'Favorable' if factors.get('weather_factor', 1.0) > 1.1 else 'Unfavorable' if factors.get('weather_factor', 1.0) < 0.9 else 'Neutral',
                'Strong Form' if factors.get('pitcher_factor', 1.0) > 1.2 else 'Weak Form' if factors.get('pitcher_factor', 1.0) < 0.8 else 'Average',
                'Pitcher-Friendly' if factors.get('stadium_factor', 1.0) > 1.1 else 'Hitter-Friendly' if factors.get('stadium_factor', 1.0) < 0.9 else 'Neutral'
            ]
        })
        
        st.dataframe(factor_df, use_container_width=True)
        
        # Current conditions details
        if 'current_conditions' in prediction:
            st.subheader("Current Conditions Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            # Weather conditions
            with col1:
                st.write("**Weather Conditions**")
                weather = prediction['current_conditions'].get('weather')
                if weather:
                    st.write(f"🌡️ Temperature: {weather['temperature']:.0f}°F")
                    st.write(f"💧 Humidity: {weather['humidity']:.0f}%")
                    st.write(f"💨 Wind Speed: {weather['wind_speed']:.0f} mph")
                    st.write(f"☁️ Conditions: {weather['conditions']}")
                    if weather['precipitation'] == 0:
                        st.write("☀️ No precipitation")
                    else:
                        st.write("🌧️ Precipitation present")
                else:
                    st.write("Weather data unavailable")
            
            # Pitcher form
            with col2:
                st.write("**Pitcher Performance Indicators**")
                pitcher_stats = prediction['current_conditions'].get('pitcher_stats')
                if pitcher_stats:
                    st.write(f"📊 Recent ERA: {pitcher_stats.get('recent_era', 'N/A'):.2f}")
                    st.write(f"📈 Recent WHIP: {pitcher_stats.get('recent_whip', 'N/A'):.2f}")
                    st.write(f"⚾ K/9 Rate: {pitcher_stats.get('k_per_nine', 'N/A'):.1f}")
                    st.write(f"✅ Quality Starts: {pitcher_stats.get('quality_starts', 'N/A')}/3")
                    
                    # Form indicator
                    recent_era = pitcher_stats.get('recent_era', 4.0)
                    if recent_era <= 2.5:
                        st.write("🔥 **Hot streak form**")
                    elif recent_era <= 3.5:
                        st.write("✅ **Good form**")
                    else:
                        st.write("📉 **Average form**")
                else:
                    st.write("Pitcher data simulated for analysis")
            
            # Stadium environment
            with col3:
                st.write("**Stadium Environment**")
                stadium_info = prediction['current_conditions'].get('stadium_info')
                if stadium_info:
                    st.write(f"🏟️ {stadium_info.get('stadium', 'Unknown Stadium')}")
                    st.write(f"🏢 Type: {stadium_info.get('type', 'Unknown').replace('_', ' ').title()}")
                    st.write(f"⛰️ Altitude: {stadium_info.get('altitude', 0):,} ft")
                    st.write(f"📊 Pitcher Friendliness: {stadium_info.get('pitcher_friendliness_score', 5.0):.1f}/10")
                    
                    # Stadium characteristics
                    characteristics = stadium_info.get('characteristics', [])
                    if characteristics:
                        char_display = []
                        for char in characteristics[:3]:  # Show top 3 characteristics
                            if 'pitcher_friendly' in char:
                                char_display.append("⚾ Pitcher-friendly")
                            elif 'hitter_friendly' in char:
                                char_display.append("🎯 Hitter-friendly")
                            elif 'dome' in char:
                                char_display.append("🏢 Domed")
                            elif 'altitude' in char:
                                char_display.append("⛰️ High altitude")
                            elif 'marine_layer' in char:
                                char_display.append("🌊 Marine layer")
                            elif 'large_foul_territory' in char:
                                char_display.append("📏 Large foul territory")
                        
                        for char in char_display:
                            st.write(char)
                    
                    # Environment assessment
                    altitude_cat = stadium_info.get('altitude_category', 'moderate')
                    if altitude_cat == 'extreme':
                        st.write("🚨 **Extreme altitude effects**")
                    elif altitude_cat == 'high':
                        st.write("⬆️ **High altitude conditions**")
                    elif stadium_info.get('type') == 'dome':
                        st.write("🏢 **Controlled environment**")
                    else:
                        st.write("🌤️ **Natural conditions**")
                else:
                    st.write("Stadium analysis for sample venue")
        
        # Historical context
        st.subheader("Historical Context")
        data = load_data()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total No-Hitters in Database", len(data))
        with col2:
            last_no_hitter = data['date'].max()
            days_since = (pd.Timestamp.now() - last_no_hitter).days
            st.metric("Days Since Last No-Hitter", days_since)
        
    except Exception as e:
        st.error(f"Error generating prediction: {str(e)}")

def show_trends_page():
    """Display trends and visualizations"""
    st.header("Historical Trends")
    
    try:
        data = load_data()
        
        # Monthly distribution
        st.subheader("No-Hitters by Month")
        data['month'] = data['date'].dt.month
        monthly_counts = data.groupby('month').size()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
        month_nums = range(4, 11)
        counts = [monthly_counts.get(m, 0) for m in month_nums]
        
        bars = ax.bar(months, counts, color='skyblue', edgecolor='navy')
        ax.set_title('No-Hitters by Month')
        ax.set_ylabel('Number of No-Hitters')
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                   str(count), ha='center', va='bottom')
        
        st.pyplot(fig)
        
        # Yearly distribution
        st.subheader("No-Hitters by Decade")
        data['decade'] = (data['date'].dt.year // 10) * 10
        decade_counts = data.groupby('decade').size().sort_index()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(decade_counts.index.astype(str), decade_counts.values, 
               color='lightcoral', edgecolor='darkred')
        ax.set_title('No-Hitters by Decade')
        ax.set_ylabel('Number of No-Hitters')
        ax.set_xlabel('Decade')
        plt.xticks(rotation=45)
        
        st.pyplot(fig)
        
        # High-frequency dates
        st.subheader("High-Frequency Dates")
        data['month_day'] = data['date'].dt.strftime('%m-%d')
        date_counts = data.groupby('month_day').size().sort_values(ascending=False)
        
        if len(date_counts) > 0:
            top_dates = date_counts.head(10)
            st.write("Dates with multiple no-hitters in history:")
            
            for date_str, count in top_dates.items():
                if count > 1:
                    month, day = date_str.split('-')
                    month_name = datetime.strptime(month, '%m').strftime('%B')
                    st.write(f"• {month_name} {int(day)}: {count} no-hitters")
        
        # NEW: Stadium Environment Analysis
        st.subheader("🏟️ Stadium Environment Trends")
        
        # Import stadium analyzer for trends
        try:
            from src.data.stadium_analysis import StadiumEnvironmentAnalyzer
            stadium_analyzer = StadiumEnvironmentAnalyzer()
            stadium_patterns, stadium_analysis = stadium_analyzer.analyze_stadium_no_hitter_patterns(data)
            
            if stadium_patterns:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**No-Hitters by Stadium Type**")
                    stadium_types = stadium_patterns['stadium_type_distribution']
                    
                    fig, ax = plt.subplots(figsize=(8, 6))
                    types = list(stadium_types.keys())
                    counts = list(stadium_types.values())
                    colors = ['lightblue', 'lightgreen', 'lightcoral']
                    
                    bars = ax.bar(types, counts, color=colors[:len(types)])
                    ax.set_title('No-Hitters by Stadium Type')
                    ax.set_ylabel('Number of No-Hitters')
                    
                    for bar, count in zip(bars, counts):
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                               str(count), ha='center', va='bottom')
                    
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
                
                with col2:
                    st.write("**No-Hitters by Altitude Category**")
                    altitude_dist = stadium_patterns['altitude_distribution']
                    
                    fig, ax = plt.subplots(figsize=(8, 6))
                    altitudes = list(altitude_dist.keys())
                    alt_counts = list(altitude_dist.values())
                    
                    bars = ax.bar(altitudes, alt_counts, color='gold')
                    ax.set_title('No-Hitters by Altitude Category')
                    ax.set_ylabel('Number of No-Hitters')
                    
                    for bar, count in zip(bars, alt_counts):
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                               str(count), ha='center', va='bottom')
                    
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
                
                # Stadium insights
                st.write("**Stadium Environment Insights**")
                avg_friendliness = stadium_patterns['pitcher_friendliness']['average']
                dome_pct = stadium_patterns['dome_preference']['dome_pct']
                
                st.write(f"📊 Average pitcher friendliness score: {avg_friendliness:.1f}/10")
                st.write(f"🏢 {dome_pct:.1f}% of no-hitters occurred in domed/retractable stadiums")
                
                # Foul territory analysis
                foul_stats = stadium_patterns['foul_territory_impact']
                large_foul_pct = foul_stats['large_or_massive'] / sum(foul_stats.values()) * 100
                st.write(f"📏 {large_foul_pct:.1f}% of no-hitters occurred in stadiums with large foul territory")
                
        except Exception as e:
            st.write("Stadium trend analysis unavailable")
        
        # NEW: Weather Pattern Analysis
        st.subheader("🌤️ Weather Pattern Trends")
        
        try:
            from src.data.weather import WeatherAnalyzer
            weather_analyzer = WeatherAnalyzer()
            weather_patterns, weather_analysis = weather_analyzer.analyze_no_hitter_weather_patterns(data)
            
            if weather_patterns:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Optimal Weather Conditions**")
                    ideal = weather_patterns['ideal_conditions']
                    st.write(f"🌡️ Ideal temperature: {ideal['temperature'][0]}°F - {ideal['temperature'][1]}°F")
                    st.write(f"💧 Ideal humidity: {ideal['humidity'][0]}% - {ideal['humidity'][1]}%")
                    st.write(f"💨 Ideal wind: {ideal['wind_speed'][0]} - {ideal['wind_speed'][1]} mph")
                    st.write(f"☀️ Clear weather preference: {weather_patterns['clear_weather_pct']:.1f}% had no precipitation")
                
                with col2:
                    st.write("**Historical Weather Averages**")
                    st.write(f"🌡️ Average temperature: {weather_patterns['avg_temperature']:.1f}°F")
                    st.write(f"💧 Average humidity: {weather_patterns['avg_humidity']:.1f}%")
                    st.write(f"💨 Average wind speed: {weather_patterns['avg_wind_speed']:.1f} mph")
                    
                    temp_range = weather_patterns['temperature_range']
                    st.write(f"📊 Temperature range: {temp_range['min']:.0f}°F to {temp_range['max']:.0f}°F")
                
        except Exception as e:
            st.write("Weather trend analysis unavailable")
        
        # NEW: Pitcher Performance Patterns
        st.subheader("⚾ Pitcher Performance Trends")
        
        try:
            from src.data.pitcher_analysis import PitcherPerformanceAnalyzer
            pitcher_analyzer = PitcherPerformanceAnalyzer()
            pitcher_patterns, pitcher_analysis = pitcher_analyzer.analyze_no_hitter_pitcher_patterns(data)
            
            if pitcher_patterns:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Pre-No-Hitter Form (Last 3 Starts)**")
                    recent_3 = pitcher_patterns['recent_3_starts_avg']
                    st.write(f"📊 Average ERA: {recent_3['era']:.2f}")
                    st.write(f"📈 Average WHIP: {recent_3['whip']:.2f}")
                    st.write(f"⚾ Average K/9: {recent_3['k_per_nine']:.1f}")
                    st.write(f"✅ Average Quality Starts: {recent_3['quality_starts']:.1f}/3")
                
                with col2:
                    st.write("**Hot Streak Indicators**")
                    hot_streak = pitcher_patterns['hot_streak_indicators']
                    st.write(f"🔥 {hot_streak['pct_era_under_2_50']:.1f}% had ERA ≤ 2.50")
                    st.write(f"🎯 {hot_streak['pct_whip_under_1_00']:.1f}% had WHIP ≤ 1.00")
                    st.write(f"⚾ {hot_streak['pct_high_k_rate']:.1f}% had K/9 ≥ 8.5")
                    st.write(f"✅ {hot_streak['pct_2_plus_quality_starts']:.1f}% had 2+ quality starts")
                
                st.write("**Key Insight**: Most no-hitter pitchers show strong recent form, suggesting the importance of 'hot streaks' in achieving this rare feat.")
                
        except Exception as e:
            st.write("Pitcher trend analysis unavailable")
        
    except Exception as e:
        st.error(f"Error loading trends: {str(e)}")

def show_history_page():
    """Display historical no-hitter data"""
    st.header("Historical No-Hitters")
    
    try:
        data = load_data()
        
        # Search and filter options
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("Search by pitcher, team, or opponent:")
        
        with col2:
            year_range = st.slider("Year Range", 
                                 int(data['date'].dt.year.min()), 
                                 int(data['date'].dt.year.max()),
                                 (int(data['date'].dt.year.min()), int(data['date'].dt.year.max())))
        
        # Filter data
        filtered_data = data.copy()
        
        if search_term:
            mask = (
                filtered_data['pitcher'].str.contains(search_term, case=False, na=False) |
                filtered_data['team'].str.contains(search_term, case=False, na=False) |
                filtered_data['opponent'].str.contains(search_term, case=False, na=False)
            )
            filtered_data = filtered_data[mask]
        
        filtered_data = filtered_data[
            (filtered_data['date'].dt.year >= year_range[0]) &
            (filtered_data['date'].dt.year <= year_range[1])
        ]
        
        # Display results
        st.write(f"Showing {len(filtered_data)} of {len(data)} no-hitters")
        
        # Format the display
        display_data = filtered_data.copy()
        display_data['Date'] = display_data['date'].dt.strftime('%Y-%m-%d')
        display_data = display_data[['Date', 'pitcher', 'team', 'opponent', 'notes']]
        display_data.columns = ['Date', 'Pitcher', 'Team', 'Opponent', 'Notes']
        
        st.dataframe(
            display_data.sort_values('Date', ascending=False),
            use_container_width=True,
            hide_index=True
        )
        
        # Enhanced Analysis for History Page
        if len(filtered_data) > 0:
            st.subheader("📊 Analysis of Filtered Data")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total No-Hitters", len(filtered_data))
                
                # Most prolific teams
                team_counts = filtered_data['team'].value_counts().head(5)
                st.write("**Top Teams (Pitching)**")
                for team, count in team_counts.items():
                    st.write(f"• {team}: {count} no-hitters")
            
            with col2:
                # Year analysis
                if len(filtered_data) > 1:
                    date_range = filtered_data['date']
                    years_span = date_range.max().year - date_range.min().year + 1
                    avg_per_year = len(filtered_data) / years_span
                    st.metric("Average per Year", f"{avg_per_year:.1f}")
                
                # Most frequent opponents
                opp_counts = filtered_data['opponent'].value_counts().head(5)
                st.write("**Most Frequent Victims**")
                for opp, count in opp_counts.items():
                    st.write(f"• {opp}: {count} times")
            
            with col3:
                # Notable achievements
                perfect_games = len(filtered_data[filtered_data['notes'].str.contains('Perfect', na=False, case=False)])
                combined_games = len(filtered_data[filtered_data['notes'].str.contains('Combined', na=False, case=False)])
                
                st.metric("Perfect Games", perfect_games)
                st.metric("Combined No-Hitters", combined_games)
                
                # Recent activity
                recent_data = filtered_data[filtered_data['date'] >= '2020-01-01']
                st.write(f"**Since 2020**: {len(recent_data)} no-hitters")
            
            # Enhanced Stadium and Environmental Analysis for History
            try:
                st.subheader("🏟️ Stadium & Environmental Breakdown")
                
                from src.data.stadium_analysis import StadiumEnvironmentAnalyzer
                stadium_analyzer = StadiumEnvironmentAnalyzer()
                
                # Analyze stadiums for filtered data
                stadium_info = []
                for _, row in filtered_data.iterrows():
                    team = row['team']
                    stadium_chars = stadium_analyzer.get_stadium_characteristics(team)
                    stadium_info.append({
                        'team': team,
                        'stadium_type': stadium_chars.get('type', 'outdoor'),
                        'altitude_category': stadium_analyzer.categorize_altitude(stadium_chars.get('altitude', 0)),
                        'pitcher_friendliness': stadium_analyzer.calculate_pitcher_friendliness(stadium_chars)
                    })
                
                if stadium_info:
                    stadium_df = pd.DataFrame(stadium_info)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Stadium type breakdown
                        type_counts = stadium_df['stadium_type'].value_counts()
                        st.write("**By Stadium Type**")
                        for stadium_type, count in type_counts.items():
                            pct = count / len(stadium_df) * 100
                            st.write(f"• {stadium_type.replace('_', ' ').title()}: {count} ({pct:.1f}%)")
                    
                    with col2:
                        # Altitude breakdown
                        alt_counts = stadium_df['altitude_category'].value_counts()
                        st.write("**By Altitude Category**")
                        for alt_cat, count in alt_counts.items():
                            pct = count / len(stadium_df) * 100
                            st.write(f"• {alt_cat.replace('_', ' ').title()}: {count} ({pct:.1f}%)")
                    
                    # Pitcher friendliness analysis
                    avg_friendliness = stadium_df['pitcher_friendliness'].mean()
                    st.write(f"📊 **Average Pitcher Friendliness**: {avg_friendliness:.1f}/10")
                    
                    high_friendly = len(stadium_df[stadium_df['pitcher_friendliness'] >= 6])
                    pct_friendly = high_friendly / len(stadium_df) * 100
                    st.write(f"⚾ **Pitcher-Friendly Venues**: {high_friendly}/{len(stadium_df)} ({pct_friendly:.1f}%)")
                    
            except Exception as e:
                st.write("Enhanced stadium analysis unavailable")
        
    except Exception as e:
        st.error(f"Error loading history: {str(e)}")

def show_about_page():
    """Display information about the app"""
    st.header("About No-Hitter Forecaster")
    
    st.markdown("""
    ### What is this app?
    
    The No-Hitter Forecaster uses a novel statistical algorithm to predict the daily probability 
    of at least one no-hitter occurring in Major League Baseball. The prediction is based on 
    historical patterns and trends in no-hitter data.
    
    ### How does it work?
    
    Our enhanced algorithm combines multiple factors:
    
    **Historical Factors:**
    1. **Base Rate**: Historical frequency of no-hitters across all MLB history
    2. **Monthly Patterns**: Some months show higher no-hitter frequency than others
    3. **Date-Specific Patterns**: Certain calendar dates have seen multiple no-hitters
    4. **Decadal Trends**: Modern baseball shows different patterns than historical eras
    5. **Recency Effects**: Time since the last no-hitter affects probability
    
    **Current Conditions (NEW):**
    6. **Weather Factors**: Temperature, humidity, wind, and precipitation conditions
    7. **Pitcher Performance**: Recent form and statistical trends of starting pitchers
    8. **Stadium Environment**: Altitude, dome/outdoor, dimensions, and ballpark characteristics
    
    ### Enhanced Algorithm
    
    We use a Bayesian-updated Poisson model that treats no-hitters as rare events. The base 
    probability is adjusted by historical patterns AND current game-day conditions including:
    
    - **Weather Analysis**: Clear, cool weather with low humidity historically favors no-hitters
    - **Pitcher Form**: Recent ERA, WHIP, strikeout rates, and quality start streaks
    - **Stadium Analysis**: Altitude effects, dome vs outdoor conditions, foul territory size
    - **Environmental Integration**: Multi-factor analysis of conditions that historically correlate with no-hitters
    
    ### Data Sources
    
    Historical no-hitter data is collected from reliable baseball statistics sources and 
    includes information about the date, pitcher, teams involved, and game details.
    
    ### Accuracy & Limitations
    
    This enhanced statistical model incorporates both historical patterns and current conditions.
    
    **What we now capture:**
    - ✅ Pitcher recent form and performance trends
    - ✅ Weather conditions (temperature, humidity, wind, precipitation)
    - ✅ Stadium environment (altitude, dome/outdoor, dimensions, foul territory)
    - ✅ Historical seasonal and date-specific patterns
    - ✅ Multi-factor environmental analysis
    
    **Still not captured:**
    - Team offensive matchups and defensive alignment
    - Specific pitcher vs. batter historical performance
    - Injury reports and roster changes
    - Game-specific strategies and bullpen usage
    - Umpire strike zone tendencies
    
    While significantly more sophisticated than simple historical averages, predictions should 
    still be viewed as statistical analysis and entertainment rather than definitive forecasts.
    
    **Model Performance:** The enhanced algorithm provides more nuanced predictions by 
    incorporating real-time conditions that historically correlate with no-hitter occurrences.
    """)

if __name__ == "__main__":
    main()