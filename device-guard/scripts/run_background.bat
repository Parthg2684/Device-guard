@echo off
echo Starting USB Guard Background Service...
echo ========================================
echo.
echo This will run the USB Guard in the background.
echo Close this window to stop the service.
echo.
echo Press Ctrl+C to stop monitoring
echo.

python src\services\usb_guard_service.py

pause
