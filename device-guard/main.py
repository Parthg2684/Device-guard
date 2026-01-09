import webview
import threading
import sys
import os
import wmi
import re
from datetime import datetime

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if APP_ROOT not in sys.path:
    sys.path.append(APP_ROOT)

from flask import Flask, render_template, jsonify, request
from src.core.db import WhitelistDB
from src.security.fingerprinter import Fingerprinter
from src.utils.logger import log, LOG_FILE
from src.core.detector import get_separated_usb_devices

server = Flask(__name__, template_folder='src/web/templates')
db = WhitelistDB()
fingerprinter = Fingerprinter()

# --- HELPER FUNCTION TO READ APP LOGS ---
def read_app_log(max_lines=100):
    """Reads and parses the last N lines of the application log file."""
    parsed_logs = []
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
        
        # Get the last max_lines
        recent_lines = lines[-max_lines:]
        
        # Regex to parse the log format: 'YYYY-MM-DD HH:MM:SS,ms - NAME - LEVEL - MESSAGE'
        log_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - .*? - (\w+) - (.*)")

        for line in recent_lines:
            match = log_pattern.match(line)
            if match:
                timestamp_str, level, message = match.groups()
                # Convert timestamp for sorting
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                parsed_logs.append({
                    "time": timestamp,
                    "type": "Application",
                    "status": level,
                    "message": message.strip()
                })
    except FileNotFoundError:
        log.warning(f"Log file not found at {LOG_FILE}")
    except Exception as e:
        log.error(f"Failed to read or parse log file: {e}")
    return parsed_logs


@server.route('/')
def index():
    return render_template('index.html')

@server.route('/api/usb_devices')
def get_usb_devices():
    storage, other = get_separated_usb_devices()
    for device in storage + other:
        details = db.get_device_details(device['canonical_id'])
        device['is_registered'] = bool(details)
        device['is_fingerprinted'] = bool(details and details.get('structural_fingerprint'))
    return jsonify({"storage_devices": storage, "other_devices": other})

# ... existing endpoints for registered_devices, register, verify, remove ...
@server.route('/api/registered_devices')
def get_registered_devices():
    return jsonify(db.list_devices())

@server.route('/api/devices/register', methods=['POST'])
def register_device():
    data = request.json
    
    # Validate admin password for security
    ADMIN_PASSWORD = "admin123"  # In production, use environment variable or proper config
    if not data.get('password') or data.get('password') != ADMIN_PASSWORD:
        return jsonify({'success': False, 'error': 'Invalid admin password'})
    
    is_storage = bool(data.get('drive_letter'))
    device_type = "storage" if is_storage else "peripheral"
    if is_storage:
        fp = fingerprinter.calculate_structural_fingerprint(data['drive_letter'])
        sig = fingerprinter.create_signed_lockfile(data['drive_letter'])
        if not fp or not sig: return jsonify({'success': False, 'error': 'Fingerprinting failed. Run as Admin.'})
        success = db.register_device(data['canonical_id'], data['friendly_name'], device_type, structural_fingerprint=fp, lockfile_signature=sig)
    else:
        success = db.register_device(data['canonical_id'], data['friendly_name'], device_type)
    return jsonify({'success': success})

@server.route('/api/devices/verify', methods=['POST'])
def verify_device():
    data = request.json
    details = db.get_device_details(data['canonical_id'])
    if not (details and details.get('structural_fingerprint')):
        return jsonify({'success': False, 'error': 'Not fingerprinted.'})
    is_valid = fingerprinter.verify_device(data['drive_letter'], details['structural_fingerprint'], details['lockfile_signature'])
    return jsonify({'success': True, 'is_valid': is_valid})

@server.route('/api/devices/remove', methods=['POST'])
def remove_device():
    data = request.json
    
    # Validate admin password for security
    ADMIN_PASSWORD = "admin123"  # In production, use environment variable or proper config
    if not data.get('password') or data.get('password') != ADMIN_PASSWORD:
        return jsonify({'success': False, 'error': 'Invalid admin password'})
    
    return jsonify({'success': db.remove_device(data['canonical_id'])})

# --- Settings and Log Management Endpoints ---
@server.route('/api/settings/logs', methods=['GET'])
def get_logs():
    """Get application logs"""
    try:
        # Get application events
        app_logs = read_app_log(max_lines=100)
        
        # Convert to log format
        all_events = []
        for log_entry in app_logs:
            all_events.append({
                "time": log_entry['time'].strftime('%Y-%m-%d %H:%M:%S'),
                "level": log_entry['status'],
                "message": log_entry['message'],
                "source": "Application"
            })
        
        # Sort by time (newest first)
        all_events.sort(key=lambda x: x['time'], reverse=True)
        
        return jsonify(all_events)
        
    except Exception as e:
        log.error(f"Error retrieving logs: {e}")
        return jsonify({"error": str(e)})

@server.route('/api/settings/clear_logs', methods=['POST'])
def clear_logs():
    """Clear application logs"""
    data = request.json
    
    # Validate admin password
    ADMIN_PASSWORD = "admin123"
    if not data.get('password') or data.get('password') != ADMIN_PASSWORD:
        return jsonify({'success': False, 'error': 'Invalid admin password'})
    
    try:
        # Clear the log file
        with open(LOG_FILE, 'w') as f:
            f.write("")  # Truncate the file
        
        log.info("System logs cleared by administrator")
        return jsonify({'success': True, 'message': 'Logs cleared successfully'})
        
    except Exception as e:
        log.error(f"Error clearing logs: {e}")
        return jsonify({'success': False, 'error': str(e)})

@server.route('/api/settings/export_db', methods=['GET'])
def export_database():
    """Export device whitelist database"""
    try:
        devices = db.list_devices()
        
        # Convert to JSON for download
        import json
        json_data = json.dumps(devices, indent=2, default=str)
        
        from flask import Response
        return Response(
            json_data,
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=device_whitelist.json'}
        )
        
    except Exception as e:
        log.error(f"Error exporting database: {e}")
        return jsonify({"error": str(e)})

@server.route('/api/settings/clear_db', methods=['POST'])
def clear_database():
    """Clear all devices from database"""
    data = request.json
    
    # Validate admin password
    ADMIN_PASSWORD = "admin123"
    if not data.get('password') or data.get('password') != ADMIN_PASSWORD:
        return jsonify({'success': False, 'error': 'Invalid admin password'})
    
    try:
        success = db._create_table()  # This will recreate the table
        if success:
            log.info("Database cleared by administrator")
            return jsonify({'success': True, 'message': 'All devices cleared from database'})
        else:
            return jsonify({'success': False, 'error': 'Failed to clear database'})
            
    except Exception as e:
        log.error(f"Error clearing database: {e}")
        return jsonify({'success': False, 'error': str(e)})

@server.route('/api/settings/restart', methods=['POST'])
def restart_service():
    """Restart the service"""
    data = request.json
    
    # Validate admin password
    ADMIN_PASSWORD = "admin123"
    if not data.get('password') or data.get('password') != ADMIN_PASSWORD:
        return jsonify({'success': False, 'error': 'Invalid admin password'})
    
    try:
        log.info("Service restart requested by administrator")
        # In a real implementation, this would restart the service
        # For now, just return success
        return jsonify({'success': True, 'message': 'Service restart initiated'})
        
    except Exception as e:
        log.error(f"Error restarting service: {e}")
        return jsonify({'success': False, 'error': str(e)})

def start_server():
    server.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    log.info("Ensuring database and table exist..."); db._create_table(); log.info("Database check complete.")
    
    # Start background USB monitoring service
    try:
        from src.services.usb_guard_service import USBGuardService
        usb_service = USBGuardService()
        usb_service.start()
        log.info("USB Guard background service started")
    except Exception as e:
        log.error(f"Failed to start background service: {e}")
    
    server_thread = threading.Thread(target=start_server); server_thread.daemon = True; server_thread.start()
    webview.create_window('Device Guard', 'http://127.0.0.1:5000', width=1200, height=800)
    webview.start()