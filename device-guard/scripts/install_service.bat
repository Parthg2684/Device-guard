@echo off
echo USB Guard Service Installer
echo ==========================

echo.
echo Installing USB Guard Service...
python src\services\windows_service.py install

echo.
echo Starting USB Guard Service...
python src\services\windows_service.py start

echo.
echo Checking service status...
python src\services\windows_service.py status

echo.
echo Service installation complete!
echo.
echo To manage the service:
echo   Start:   python src\services\windows_service.py start
echo   Stop:    python src\services\windows_service.py stop
echo   Restart: python src\services\windows_service.py restart
echo   Remove:  python src\services\windows_service.py remove
echo.
pause
