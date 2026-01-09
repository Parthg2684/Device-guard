# Device Guard - Installation Guide

## System Requirements

- **Operating System**: Windows 10/11 (64-bit)
- **Python**: 3.8 or higher
- **Administrator Privileges**: Required for device blocking functionality
- **RAM**: Minimum 4GB
- **Storage**: Minimum 100MB free space

## Quick Installation

### 1. Clone or Download the Project
```bash
git clone https://github.com/yourusername/device-guard.git
cd device-guard
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python main.py
```

## Detailed Installation

### Step 1: Python Environment Setup
1. Install Python 3.8+ from [python.org](https://python.org)
2. Verify installation:
   ```bash
   python --version
   pip --version
   ```

### Step 2: Virtual Environment (Recommended)
```bash
python -m venv device-guard-env
device-guard-env\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Database Initialization
The database is automatically created on first run. No manual setup required.

### Step 5: Run as Administrator
**Important**: Run as Administrator for full device blocking capabilities:
- Right-click on Command Prompt/PowerShell
- Select "Run as administrator"
- Navigate to project directory
- Run `python main.py`

## Installation Methods

### Method 1: GUI Application (Recommended)
```bash
python main.py
```
- Opens desktop GUI with full management capabilities
- Background monitoring starts automatically
- Best for first-time users and testing

### Method 2: Background Service Only
```bash
run_background.bat
```
- Runs in command prompt window
- Continuous USB monitoring
- Close window to stop service

### Method 3: Windows Service (Production)
```bash
# Run as Administrator
install_service.bat
```
- Installs as Windows service
- Runs automatically on system startup
- Best for production environments

## Verification

### 1. Check Application Launch
- GUI window should open with "Device Guard" title
- Web interface should load at http://127.0.0.1:5000

### 2. Check Background Service
- Look for "USB Guard background service started" in logs
- Connect a USB device to test monitoring

### 3. Check Device Detection
- Go to "Device Detection" tab
- Connected USB devices should appear in tables

## Troubleshooting

### Common Issues

#### 1. "Access Denied" Errors
**Solution**: Run as Administrator
- Right-click Command Prompt/PowerShell
- Select "Run as administrator"
- Navigate to project directory
- Run application

#### 2. "Module Not Found" Errors
**Solution**: Install missing dependencies
```bash
pip install -r requirements.txt --upgrade
```

#### 3. "Service Installation Failed"
**Solution**: Run installer as Administrator
```bash
# Open Command Prompt as Administrator
cd path\to\device-guard
install_service.bat
```

#### 4. "Device Not Detected"
**Solution**: Check WMI service
- Open Services (services.msc)
- Ensure "Windows Management Instrumentation" is running
- Restart the service if needed

#### 5. "Port 5000 Already in Use"
**Solution**: Change port in main.py
```python
server.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
```

### Log Files
Check application logs for detailed error information:
- Location: `logs/app_log.log`
- Contains: Device detection events, errors, and system messages

### Performance Issues
1. **High CPU Usage**: Reduce monitoring frequency in `usb_guard_service.py`
2. **Memory Usage**: Restart application periodically
3. **Disk Space**: Clear old logs from logs/ directory

## Uninstallation

### Remove Windows Service
```bash
# Run as Administrator
python windows_service.py remove
```

### Remove Application Files
1. Stop any running instances
2. Delete the project directory
3. Remove desktop shortcuts if created

## Security Considerations

1. **Default Password**: Change admin password from "admin123"
2. **Network Access**: Application runs locally only (127.0.0.1)
3. **Data Storage**: Database and logs stored locally
4. **Encryption**: Device fingerprints use RSA encryption

## Support

For issues and support:
1. Check the troubleshooting section above
2. Review log files in `logs/` directory
3. Ensure all dependencies are properly installed
4. Verify administrator privileges

## Next Steps

After successful installation:
1. Register your USB devices in the application
2. Configure security settings
3. Test device blocking with unauthorized devices
4. Set up Windows service for continuous protection
