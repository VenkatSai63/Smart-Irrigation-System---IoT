from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

from database.models import db, User, SensorData, Predictions, PumpLogs, Weather
from utils import process_new_sensor_reading, export_csv, export_excel, generate_pdf_report
from config import Config

main_bp = Blueprint('main', __name__)

# IoT Global System State
system_state = {
    'pump_status': 'OFF',  # 'ON' or 'OFF'
    'mode': 'AUTO',        # 'AUTO' or 'MANUAL'
    'crop': 'Wheat',       # Active crop
    'weather_city': None,  # Lazy initialized via detect_local_city() on load
    'last_active_time': datetime.utcnow()
}

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        # Check if form data is application/json or urlencoded
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('main.dashboard')})
            return redirect(url_for('main.dashboard'))
            
        if request.is_json:
            return jsonify({'success': False, 'message': 'Invalid username or password'})
        flash('Invalid username or password', 'danger')
        
    return render_template('login.html')

@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
        else:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
        # Check if user exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Username or Email already registered'})
            flash('Username or Email already registered', 'danger')
            return render_template('signup.html')
            
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('main.dashboard')})
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('signup.html')

@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            # Simulated reset password process
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash('reset123')
            db.session.commit()
            flash('Your password has been reset to "reset123". Please login and update it.', 'success')
            return redirect(url_for('main.login'))
        else:
            flash('Email not found in our records', 'danger')
            
    return render_template('login.html', show_forgot=True)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('main.login'))

# ==========================================
# DASHBOARD & PAGES
# ==========================================

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Detect local city if not set
    if not system_state.get('weather_city'):
        from weather import detect_local_city
        system_state['weather_city'] = detect_local_city()
        
    # Fetch recent sensor logs
    recent_logs = SensorData.query.order_by(SensorData.timestamp.desc()).limit(10).all()
    # Fetch current weather cache
    weather = Weather.query.filter(Weather.city.ilike(system_state['weather_city'])).order_by(Weather.timestamp.desc()).first()
    
    # Calculate water usage mock stats
    # (Pump ON duration * mock flow rate of 12 Liters/Min)
    # Let's count how many times pump was turned ON today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    pump_on_logs = PumpLogs.query.filter(PumpLogs.action == 'Pump ON', PumpLogs.timestamp >= today_start).count()
    # Mock flow calculation: each activation is simulated as running for 2 minutes on average
    today_water_usage = round(pump_on_logs * 2 * 12.5, 1) # Liters
    
    # Total farms monitoring mock
    total_farms = 3
    
    return render_template(
        'dashboard.html',
        recent_logs=recent_logs,
        weather=weather,
        system_state=system_state,
        today_water_usage=today_water_usage,
        total_farms=total_farms,
        crop_types=Config.CROP_TYPES
    )

@main_bp.route('/charts')
@login_required
def charts():
    return render_template('charts.html')

@main_bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Unauthorized Access! Admin rights required.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    users = User.query.all()
    sensor_logs = SensorData.query.order_by(SensorData.timestamp.desc()).limit(50).all()
    predictions = Predictions.query.order_by(Predictions.timestamp.desc()).limit(50).all()
    pump_logs = PumpLogs.query.order_by(PumpLogs.timestamp.desc()).limit(50).all()
    
    return render_template(
        'admin.html',
        users=users,
        sensor_logs=sensor_logs,
        predictions=predictions,
        pump_logs=pump_logs
    )

# ==========================================
# API ENDPOINTS
# ==========================================

# GET /sensor-data -> Returns JSON logs
@main_bp.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    limit = request.args.get('limit', 20, type=int)
    logs = SensorData.query.order_by(SensorData.timestamp.desc()).limit(limit).all()
    return jsonify([l.to_dict() for l in logs])

# POST /sensor-data & POST /api/sensor-data -> Accept incoming sensor JSON
@main_bp.route('/sensor-data', methods=['POST'])
@main_bp.route('/api/sensor-data', methods=['POST'])
def post_sensor_data():
    try:
        # Support JSON payload
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'moisture': float(request.form.get('moisture')),
                'temperature': float(request.form.get('temperature')),
                'humidity': float(request.form.get('humidity')),
                'rain_value': float(request.form.get('rain_value'))
            }
            
        # Process and save reading, predicting pump status
        process_new_sensor_reading(data, system_state)
        system_state['last_active_time'] = datetime.utcnow()
        
        # Return state back to ESP32
        return jsonify({
            'success': True,
            'pump_status': system_state['pump_status'],
            'mode': system_state['mode'],
            'crop': system_state['crop']
        }), 201
    except Exception as e:
        print(f"Error handling sensor data API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

# GET /predictions -> Returns JSON of prediction logs
@main_bp.route('/predictions', methods=['GET'])
@login_required
def get_predictions():
    limit = request.args.get('limit', 20, type=int)
    preds = Predictions.query.order_by(Predictions.timestamp.desc()).limit(limit).all()
    return jsonify([p.to_dict() for p in preds])

# POST /pump/on -> Manually turn pump ON
@main_bp.route('/pump/on', methods=['POST'])
@login_required
def pump_on():
    if system_state['mode'] == 'AUTO':
        return jsonify({'success': False, 'message': 'Cannot force pump ON in AUTO mode. Switch to MANUAL first.'})
        
    system_state['pump_status'] = 'ON'
    log = PumpLogs(action="Pump ON", source="MANUAL")
    db.session.add(log)
    db.session.commit()
    return jsonify({'success': True, 'pump_status': 'ON'})

# POST /pump/off -> Manually turn pump OFF
@main_bp.route('/pump/off', methods=['POST'])
@login_required
def pump_off():
    if system_state['mode'] == 'AUTO':
        return jsonify({'success': False, 'message': 'Cannot force pump OFF in AUTO mode. Switch to MANUAL first.'})
        
    system_state['pump_status'] = 'OFF'
    log = PumpLogs(action="Pump OFF", source="MANUAL")
    db.session.add(log)
    db.session.commit()
    return jsonify({'success': True, 'pump_status': 'OFF'})

# POST /pump/toggle-mode -> Change AUTO/MANUAL mode
@main_bp.route('/pump/toggle-mode', methods=['POST'])
@login_required
def toggle_mode():
    data = request.get_json() or {}
    new_mode = data.get('mode')
    if new_mode in ['AUTO', 'MANUAL']:
        system_state['mode'] = new_mode
        # When switching to auto, force immediate prediction check based on last sensor log
        if new_mode == 'AUTO':
            last_sensor = SensorData.query.order_by(SensorData.timestamp.desc()).first()
            if last_sensor:
                process_new_sensor_reading(last_sensor.to_dict(), system_state)
        return jsonify({'success': True, 'mode': system_state['mode'], 'pump_status': system_state['pump_status']})
    return jsonify({'success': False, 'message': 'Invalid mode'})

# POST /pump/change-crop -> Change Crop Type
@main_bp.route('/pump/change-crop', methods=['POST'])
@login_required
def change_crop():
    data = request.get_json() or {}
    new_crop = data.get('crop')
    if new_crop in Config.CROP_TYPES:
        system_state['crop'] = new_crop
        # Recalculate automatic pump response based on new crop properties
        if system_state['mode'] == 'AUTO':
            last_sensor = SensorData.query.order_by(SensorData.timestamp.desc()).first()
            if last_sensor:
                process_new_sensor_reading(last_sensor.to_dict(), system_state)
        return jsonify({'success': True, 'crop': system_state['crop'], 'pump_status': system_state['pump_status']})
    return jsonify({'success': False, 'message': 'Invalid crop type'})

# GET /weather -> Current weather details
@main_bp.route('/weather', methods=['GET'])
@login_required
def get_weather():
    if not system_state.get('weather_city'):
        from weather import detect_local_city
        system_state['weather_city'] = detect_local_city()
        
    city = system_state['weather_city']
    w = Weather.query.filter(Weather.city.ilike(city)).order_by(Weather.timestamp.desc()).first()
    if not w:
        from weather import get_weather_data
        w_data = get_weather_data(city)
        w = Weather(
            city=w_data['city'],
            temperature=w_data['temperature'],
            humidity=w_data['humidity'],
            wind_speed=w_data['wind_speed'],
            rain_prob=w_data['rain_prob'],
            condition=w_data['condition']
        )
        db.session.add(w)
        db.session.commit()
    return jsonify(w.to_dict())

# POST /weather/change-city -> Change active weather location
@main_bp.route('/weather/change-city', methods=['POST'])
@login_required
def change_city():
    data = request.get_json() or {}
    new_city = data.get('city', '').strip()
    if new_city:
        system_state['weather_city'] = new_city
        
        # Trigger immediate weather fetch
        from weather import get_weather_data
        w_data = get_weather_data(new_city)
        
        weather_log = Weather(
            city=w_data['city'],
            temperature=w_data['temperature'],
            humidity=w_data['humidity'],
            wind_speed=w_data['wind_speed'],
            rain_prob=w_data['rain_prob'],
            condition=w_data['condition']
        )
        db.session.add(weather_log)
        
        # Re-run prediction if AUTO mode
        if system_state['mode'] == 'AUTO':
            last_sensor = SensorData.query.order_by(SensorData.timestamp.desc()).first()
            if last_sensor:
                process_new_sensor_reading(last_sensor.to_dict(), system_state)
                
        db.session.commit()
        return jsonify({'success': True, 'city': system_state['weather_city'], 'weather': w_data})
        
    return jsonify({'success': False, 'message': 'Invalid city name'})

# GET /logs -> Returns sensor data, pump history, predictions
@main_bp.route('/logs', methods=['GET'])
@login_required
def get_logs():
    sensor_logs = SensorData.query.order_by(SensorData.timestamp.desc()).limit(20).all()
    pump_logs = PumpLogs.query.order_by(PumpLogs.timestamp.desc()).limit(20).all()
    return jsonify({
        'sensor_data': [s.to_dict() for s in sensor_logs],
        'pump_logs': [p.to_dict() for p in pump_logs]
    })

# ==========================================
# ADMIN SUB-ROUTES
# ==========================================

@main_bp.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin privileges required'}), 403
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
        
    if user.username == 'admin' or user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot delete primary admin or current active user'}), 400
        
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'User deleted successfully'})

# Export PDF
@main_bp.route('/admin/export/pdf', methods=['GET'])
@login_required
def admin_export_pdf():
    if not current_user.is_admin:
        return "Unauthorized", 403
    pdf_data = generate_pdf_report()
    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={"Content-disposition": "attachment; filename=Smart_Irrigation_Report.pdf"}
    )

# Export CSV
@main_bp.route('/admin/export/csv/<table_name>', methods=['GET'])
@login_required
def admin_export_csv(table_name):
    if not current_user.is_admin:
        return "Unauthorized", 403
    csv_data = export_csv(table_name)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={table_name}_report.csv"}
    )

# Export Excel
@main_bp.route('/admin/export/excel/<table_name>', methods=['GET'])
@login_required
def admin_export_excel(table_name):
    if not current_user.is_admin:
        return "Unauthorized", 403
    excel_data = export_excel(table_name)
    return Response(
        excel_data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-disposition": f"attachment; filename={table_name}_report.xlsx"}
    )
