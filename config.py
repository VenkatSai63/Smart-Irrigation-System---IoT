import os

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_smart_irrigation_system_9918')
    
    # Database Configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, 'database', 'smart_irrigation.db')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenWeather API Configuration
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '') # Empty string enables Simulator fallback
    DEFAULT_CITY = "Delhi"
    
    # Machine Learning Configuration
    ML_MODEL_PATH = os.path.join(BASE_DIR, 'model', 'model.pkl')
    DATASET_PATH = os.path.join(BASE_DIR, 'dataset', 'crop_data.csv')
    
    # Supported Crops
    CROP_TYPES = ['Wheat', 'Rice', 'Maize', 'Cotton', 'Sugarcane']
    
    # Default Soil Moisture Thresholds for AUTO Mode
    MOISTURE_THRESHOLDS = {
        'Wheat': 40.0,
        'Rice': 60.0,
        'Maize': 45.0,
        'Cotton': 35.0,
        'Sugarcane': 50.0
    }
