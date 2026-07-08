import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Add parent directory to path to import Config if needed, or just hardcode configuration mapping
CROP_MAP = {'Wheat': 0, 'Rice': 1, 'Maize': 2, 'Cotton': 3, 'Sugarcane': 4}

def generate_realistic_dataset(num_records=5000):
    np.random.seed(42)
    crops = list(CROP_MAP.keys())
    
    # Generate random features
    soil_moisture = np.random.uniform(10.0, 95.0, num_records)
    temperature = np.random.uniform(15.0, 48.0, num_records)
    humidity = np.random.uniform(20.0, 95.0, num_records)
    rain = np.random.choice([0, 1], size=num_records, p=[0.75, 0.25]) # 25% chance of rain
    crop_type = np.random.choice(crops, size=num_records)
    
    pump = []
    
    for i in range(num_records):
        sm = soil_moisture[i]
        temp = temperature[i]
        hum = humidity[i]
        rn = rain[i]
        crop = crop_type[i]
        
        # Base logical rules for pump status
        if rn == 1:
            pump_status = 0 # No need to water if it is raining
        else:
            # Check crop thresholds
            if crop == 'Rice' and sm < 60:
                pump_status = 1
            elif crop == 'Wheat' and sm < 40:
                pump_status = 1
            elif crop == 'Maize' and sm < 45:
                pump_status = 1
            elif crop == 'Cotton' and sm < 35:
                pump_status = 1
            elif crop == 'Sugarcane' and sm < 50:
                pump_status = 1
            else:
                pump_status = 0
                
        pump.append(pump_status)
        
    # Introduce 5% noise to make ML learning more realistic
    pump = np.array(pump)
    noise_mask = np.random.rand(num_records) < 0.05
    pump[noise_mask] = 1 - pump[noise_mask]
    
    df = pd.DataFrame({
        'Soil Moisture': np.round(soil_moisture, 2),
        'Temperature': np.round(temperature, 2),
        'Humidity': np.round(humidity, 2),
        'Rain': rain,
        'Crop Type': crop_type,
        'Pump': pump
    })
    
    return df

def train_and_save_model():
    print("Generating dataset...")
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_dir = os.path.join(base_dir, 'dataset')
    model_dir = os.path.join(base_dir, 'model')
    
    os.makedirs(dataset_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)
    
    csv_path = os.path.join(dataset_dir, 'crop_data.csv')
    model_path = os.path.join(model_dir, 'model.pkl')
    
    df = generate_realistic_dataset(5000)
    df.to_csv(csv_path, index=False)
    print(f"Dataset generated and saved to: {csv_path}")
    
    # Preprocess
    df_train = df.copy()
    df_train['Crop Type'] = df_train['Crop Type'].map(CROP_MAP)
    
    X = df_train[['Soil Moisture', 'Temperature', 'Humidity', 'Rain', 'Crop Type']]
    y = df_train['Pump']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model trained successfully. Accuracy: {acc*100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save the model
    joblib.dump(model, model_path)
    print(f"Model saved to: {model_path}")

if __name__ == "__main__":
    train_and_save_model()
