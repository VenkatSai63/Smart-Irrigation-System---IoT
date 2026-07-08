import os
import joblib
import numpy as np

CROP_MAP = {'Wheat': 0, 'Rice': 1, 'Maize': 2, 'Cotton': 3, 'Sugarcane': 4}

class IrrigationPredictor:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(base_dir, 'model', 'model.pkl')
        self.model = None
        self.load_model()
        
    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("ML Model loaded successfully.")
            except Exception as e:
                print(f"Error loading ML model: {e}")
                self.model = None
        else:
            print(f"ML Model not found at {self.model_path}. It will be trained on startup.")

    def train_if_missing(self):
        if self.model is None:
            print("Model missing, running train_model.py...")
            from ml.train_model import train_and_save_model
            train_and_save_model()
            self.load_model()

    def predict(self, moisture, temperature, humidity, rain, crop_type):
        """
        Predicts if pump should be ON or OFF
        Parameters:
        - moisture: float (Soil moisture percentage 0-100)
        - temperature: float (°C)
        - humidity: float (Humidity percentage 0-100)
        - rain: int (0 for no rain, 1 for rain)
        - crop_type: str ('Wheat', 'Rice', 'Maize', 'Cotton', 'Sugarcane')
        
        Returns:
        - tuple: (prediction_str, confidence_percentage)
        """
        self.train_if_missing()
        
        if self.model is None:
            # Fallback heuristic if ML fails to load/train
            print("Fallback to heuristic decision logic.")
            thresholds = {'Wheat': 40, 'Rice': 60, 'Maize': 45, 'Cotton': 35, 'Sugarcane': 50}
            thresh = thresholds.get(crop_type, 40)
            if rain == 1:
                return "Pump OFF", 100.0
            elif moisture < thresh:
                return "Pump ON", 90.0
            return "Pump OFF", 90.0

        # Encode crop type
        crop_encoded = CROP_MAP.get(crop_type, 0)
        
        # Feature array: [Soil Moisture, Temperature, Humidity, Rain, Crop Type]
        features = np.array([[moisture, temperature, humidity, rain, crop_encoded]])
        
        try:
            pred = self.model.predict(features)[0]
            probs = self.model.predict_proba(features)[0]
            confidence = float(probs[pred] * 100)
            
            prediction_str = "Pump ON" if pred == 1 else "Pump OFF"
            return prediction_str, confidence
        except Exception as e:
            print(f"Prediction error: {e}")
            # Fallback heuristic
            return "Pump OFF", 50.0

# Singleton instance
predictor = IrrigationPredictor()
