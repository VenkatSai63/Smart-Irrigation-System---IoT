import requests
import random
from config import Config

def get_weather_data(city=None):
    if not city:
        city = Config.DEFAULT_CITY
        
    api_key = Config.OPENWEATHER_API_KEY
    
    # If API key is not configured, fall back to simulated weather
    if not api_key:
        return get_simulated_weather(city)
        
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Extract current weather
            current = data['list'][0]
            temp = current['main']['temp']
            humidity = current['main']['humidity']
            wind_speed = current['wind']['speed'] * 3.6 # convert m/s to km/h
            condition = current['weather'][0]['main']
            
            # OpenWeather 5 day / 3 hour forecast doesn't give a direct probability of rain,
            # but we can check if rain is in the forecast list
            rain_prob = 0.0
            is_rainy_forecast = False
            
            # Simple heuristic: scan next 24 hours (8 steps of 3h) for rain
            forecast_items = []
            for item in data['list'][:8]:
                w_main = item['weather'][0]['main']
                if w_main.lower() == 'rain':
                    rain_prob = max(rain_prob, 80.0)
                    is_rainy_forecast = True
                elif w_main.lower() == 'clouds':
                    rain_prob = max(rain_prob, 30.0)
                
                forecast_items.append({
                    'time': item['dt_txt'].split(' ')[1][:5], # HH:MM
                    'temp': round(item['main']['temp'], 1),
                    'condition': w_main,
                    'humidity': item['main']['humidity']
                })
                
            return {
                'city': data['city']['name'],
                'temperature': round(temp, 1),
                'humidity': humidity,
                'wind_speed': round(wind_speed, 1),
                'rain_prob': rain_prob,
                'condition': condition,
                'is_rainy': is_rainy_forecast or condition.lower() == 'rain',
                'forecast': forecast_items
            }
        else:
            print(f"Weather API returned status code {response.status_code}. Using simulation fallback.")
            return get_simulated_weather(city)
    except Exception as e:
        print(f"Weather API request error: {e}. Using simulation fallback.")
        return get_simulated_weather(city)

def get_simulated_weather(city):
    """
    Returns realistic simulated weather data based on standard patterns.
    """
    # Deterministic simulation based on current hour to prevent wild fluctuations
    from datetime import datetime
    hour = datetime.now().hour
    
    # Simple temperature cycle
    if 5 <= hour < 14:
        temp = 20.0 + (hour - 5) * 1.5 # warming up
    elif 14 <= hour < 20:
        temp = 33.5 - (hour - 14) * 1.5 # cooling down
    else:
        temp = 24.5 - ((hour - 20) % 24) * 0.5 # cool night
        
    temp += random.uniform(-1, 1)
    
    # Humidity behaves opposite to temperature
    humidity = max(10, min(100, int(100 - temp * 1.8 + random.uniform(-5, 5))))
    wind_speed = round(8.0 + random.uniform(0, 10), 1)
    
    # Decide if it's rainy
    is_rainy = random.choice([True, False, False, False]) # 25% chance of simulated rain prediction
    
    if is_rainy:
        condition = "Rain"
        rain_prob = round(random.uniform(70, 95), 1)
    else:
        conditions = ["Clear", "Sunny", "Cloudy", "Haze"]
        condition = random.choice(conditions)
        rain_prob = round(random.uniform(5, 35), 1)
        
    # Generate 4-interval forecast
    forecast = []
    current_hour = hour
    for i in range(4):
        f_hour = (current_hour + (i + 1) * 3) % 24
        f_temp = temp + random.uniform(-2, 2)
        f_cond = "Rain" if is_rainy and i < 2 else random.choice(["Clear", "Cloudy", "Sunny"])
        forecast.append({
            'time': f"{f_hour:02d}:00",
            'temp': round(f_temp, 1),
            'condition': f_cond,
            'humidity': max(20, min(95, int(humidity + random.uniform(-10, 10))))
        })
        
    return {
        'city': city,
        'temperature': round(temp, 1),
        'humidity': humidity,
        'wind_speed': wind_speed,
        'rain_prob': rain_prob,
        'condition': condition,
        'is_rainy': is_rainy,
        'forecast': forecast
    }
