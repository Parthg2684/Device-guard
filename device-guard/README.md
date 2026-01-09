# Device Guard - USB Security Management System

A comprehensive USB device security management tool that provides real-time device monitoring, automatic blocking of unauthorized devices, and secure device registration capabilities.

## Features

- **Real-time USB Monitoring**: Continuously monitors USB device connections
- **Automatic Device Blocking**: Blocks unauthorized devices before they can access the system
- **Device Registration**: Secure registration with password protection
- **Device Fingerprinting**: Structural fingerprinting for storage devices
- **Background Service**: Runs as Windows service for continuous protection
- **Security Logs**: Comprehensive logging and audit trail
- **Database Management**: Export and manage device whitelist
- **User Management**: Admin password controls
- **Settings Management**: Configure security policies

## How It Works

1. **Background Monitoring**: The service runs continuously in the background
2. **Device Detection**: Automatically detects when USB devices are connected
3. **Authorization Check**: Verifies if the device is registered in the whitelist
4. **Automatic Blocking**: Blocks unauthorized devices immediately
5. **Device Fingerprinting**: Verifies registered storage devices for authenticity
6. **Logging**: Records all device events for audit trail

## Project Structure

```
device-guard/
├── main.py                 # Main application entry point
├── agent.py                # Background enforcement agent
├── usb_guard_service.py    # Core USB monitoring service
├── windows_service.py      # Windows service wrapper
├── install_service.bat     # Service installation script
├── run_background.bat      # Standalone background runner
├── requirements.txt        # Python dependencies
├── backend/                # Backend modules
│   ├── db.py              # Database operations
│   ├── detector.py        # USB device detection
│   ├── fingerprinter.py    # Device fingerprinting
│   ├── logger.py          # Logging system
│   ├── enforcer.py        # Device enforcement
│   ├── firewall_manager.py # Windows Firewall management
│   ├── remote_access_manager.py # RDP management
│   ├── security_audit_manager.py # Security auditing
│   ├── host_key.pem       # RSA host key
│   └── whitelist.db       # SQLite database
├── static/                 # Frontend assets
│   └── app.js            # JavaScript application logic
├── templates/              # HTML templates
│   └── index.html        # Main web interface
└── logs/                  # Application logs
    └── app_log.log       # Runtime log file
```

## Installation

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run as Application** (Recommended for testing):
```bash
python main.py
```
This will start both the GUI and background monitoring service.

3. **Run Background Only**:
```bash
run_background.bat
```

4. **Install as Windows Service** (Production):
```bash
install_service.bat
```

## Usage Methods

### Method 1: GUI Application (Recommended)
- Run `python main.py`
- Opens desktop GUI with full management capabilities
- Background monitoring starts automatically
- Manage devices, settings, and view logs

### Method 2: Background Service Only
- Run `run_background.bat`
- Runs in command prompt window
- Continuous USB monitoring
- Close window to stop service

### Method 3: Windows Service (Production)
- Run `install_service.bat` as Administrator
- Service runs automatically on system startup
- Use GUI separately for management
- Service continues running even when GUI is closed

## Security Features

- **Real-time Protection**: Blocks unauthorized devices immediately upon connection
- **Device Fingerprinting**: Structural verification for storage devices
- **Password Protection**: Admin password required for device registration/removal
- **Access Control**: Multiple blocking methods (drive hiding, ejection, WMI disable)
- **Audit Logging**: Complete activity logging and monitoring
- **Secure Storage**: Encrypted device fingerprints and signatures

## Blocking Methods

The service uses multiple methods to block unauthorized devices:

1. **Drive Hiding**: Hides drive letters from Windows Explorer
2. **Drive Ejection**: Ejects USB storage devices
3. **WMI Disable**: Disables devices through Windows Management Instrumentation
4. **Registry Policies**: Applies system policies to restrict access

## Default Credentials

- **Admin Password**: `admin123` (change in Settings tab)

## Service Management

### Windows Service Commands:
```bash
# Install service
python windows_service.py install

# Start service
python windows_service.py start

# Stop service
python windows_service.py stop

# Restart service
python windows_service.py restart

# Remove service
python windows_service.py remove

# Check status
python windows_service.py status
```

## Technical Details

- **Backend**: Flask web server with SQLite database
- **Frontend**: Bootstrap 5 with vanilla JavaScript
- **Security**: RSA encryption for device signatures
- **Platform**: Windows (WMI for device detection)
- **Database**: SQLite for device whitelist storage
- **Service**: Windows Service with pywin32-service

## API Endpoints

- `GET /api/usb_devices` - Get detected USB devices
- `POST /api/devices/register` - Register new device
- `POST /api/devices/remove` - Remove registered device
- `POST /api/devices/verify` - Verify device fingerprint
- `GET /api/registered_devices` - Get registered devices
- `GET /api/settings/logs` - Get system logs
- `POST /api/settings/clear_logs` - Clear system logs
- `GET /api/settings/export_db` - Export database
- `POST /api/settings/clear_db` - Clear database

## Dependencies

- Flask - Web framework
- pywebview - Desktop application window
- wmi - Windows Management Instrumentation
- cryptography - Encryption and signing
- pywin32 - Windows API access
- pywin32-service - Windows service framework

## Security Notes

- Run as Administrator for full device blocking capabilities
- The service requires elevated privileges for device control
- All device events are logged for security auditing
- Unauthorized devices are blocked before system access

## License

This project is proprietary software for USB device security management.
