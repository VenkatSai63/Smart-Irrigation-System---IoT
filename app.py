import os
import threading
import time
from datetime import datetime, timedelta
from flask import Flask
from flask_login import LoginManager

from config import Config
from database.models import db, User
from routes import main_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure folders exist
    os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'model'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'dataset'), exist_ok=True)
    
    # Initialize database
    db.init_app(app)
    
    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # Register Blueprint
    app.register_blueprint(main_bp)
    
    # Initialize database tables and defaults inside application context
    with app.app_context():
        from utils import init_db_defaults
        from ml.predict import predictor
        
        # Verify ML model is ready
        predictor.train_if_missing()
        
        # Build tables & admin
        init_db_defaults()
        
    # Start the IoT/Sensor Background Simulator
    start_simulator_thread(app)
    
    return app

def start_simulator_thread(app):
    def run_simulator():
        print("[SIMULATOR] Thread started.")
        # Give Flask some time to boot
        time.sleep(3)
        
        with app.app_context():
            from routes import system_state
            from utils import generate_simulated_reading, process_new_sensor_reading
            
            while True:
                try:
                    now = datetime.utcnow()
                    last_active = system_state.get('last_active_time', now - timedelta(seconds=10))
                    time_diff = (now - last_active).total_seconds()
                    
                    # If last active is more than 5 seconds ago, run simulation step
                    if time_diff >= 5.0:
                        # Generate simulated reading
                        data = generate_simulated_reading()
                        # Process and update
                        process_new_sensor_reading(data, system_state)
                        
                except Exception as e:
                    print(f"[SIMULATOR] Error in background thread: {e}")
                    
                time.sleep(5) # run simulation loop every 5 seconds

    thread = threading.Thread(target=run_simulator, daemon=True)
    thread.start()

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
