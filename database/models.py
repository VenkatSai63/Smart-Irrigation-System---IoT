from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"

class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    
    id = db.Column(db.Integer, primary_key=True)
    moisture = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    rain_value = db.Column(db.Float, nullable=False) # raw sensor value or percentage
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'moisture': self.moisture,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'rain_value': self.rain_value,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

class Predictions(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    moisture = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    rain = db.Column(db.Boolean, nullable=False)
    crop_type = db.Column(db.String(50), nullable=False)
    prediction = db.Column(db.String(20), nullable=False) # "Pump ON" or "Pump OFF"
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'moisture': self.moisture,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'rain': self.rain,
            'crop_type': self.crop_type,
            'prediction': self.prediction,
            'confidence': round(self.confidence, 2),
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

class Weather(db.Model):
    __tablename__ = 'weather'
    
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(80), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    rain_prob = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(80), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'wind_speed': self.wind_speed,
            'rain_prob': self.rain_prob,
            'condition': self.condition,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

class PumpLogs(db.Model):
    __tablename__ = 'pump_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(20), nullable=False) # "Pump ON" or "Pump OFF"
    source = db.Column(db.String(20), nullable=False) # "AUTO", "MANUAL", "ADMIN"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'source': self.source,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
