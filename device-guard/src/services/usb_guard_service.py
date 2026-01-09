import os
import sys
import time
import threading
import wmi
import pythoncom
from datetime import datetime

# Add project root to path
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if APP_ROOT not in sys.path:
    sys.path.append(APP_ROOT)

from src.core.db import WhitelistDB
from src.core.detector import get_separated_usb_devices
from src.security.fingerprinter import Fingerprinter
from src.utils.logger import log

class USBGuardService:
    """Background service that monitors USB devices and blocks unauthorized ones"""
    
    def __init__(self):
        self.db = WhitelistDB()
        self.fingerprinter = Fingerprinter()
        self.running = False
        self.monitor_thread = None
        self.last_known_devices = set()
        
    def start(self):
        """Start the USB monitoring service"""
        if self.running:
            log.warning("USB Guard Service is already running")
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_devices, daemon=True)
        self.monitor_thread.start()
        log.info("USB Guard Service started - monitoring USB devices")
        
    def stop(self):
        """Stop the USB monitoring service"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        log.info("USB Guard Service stopped")
        
    def _monitor_devices(self):
        """Main monitoring loop"""
        log.info("Starting USB device monitoring loop")
        
        while self.running:
            try:
                pythoncom.CoInitialize()  # Initialize COM for WMI
                self._check_device_changes()
                pythoncom.CoUninitialize()
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                log.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait longer on error
                
    def _check_device_changes(self):
        """Check for device changes and take action"""
        try:
            # Get current devices
            storage_devices, other_devices = get_separated_usb_devices()
            all_devices = storage_devices + other_devices
            
            current_device_ids = set()
            unauthorized_devices = []
            
            for device in all_devices:
                device_id = device['canonical_id']
                current_device_ids.add(device_id)
                
                # Check if device is registered
                is_registered = self.db.get_device_details(device_id) is not None
                
                if not is_registered:
                    unauthorized_devices.append(device)
                    
                    # Block the device if it's storage
                    if device.get('drive_letter'):
                        self._block_storage_device(device)
                    else:
                        self._block_peripheral_device(device)
                        
                # Check if device is newly connected
                if device_id not in self.last_known_devices:
                    if is_registered:
                        log.info(f"Authorized device connected: {device['friendly_name']} ({device_id})")
                        
                        # Verify fingerprint for storage devices
                        if device.get('drive_letter'):
                            self._verify_device_fingerprint(device)
                    else:
                        log.warning(f"Unauthorized device blocked: {device['friendly_name']} ({device_id})")
                        
            # Check for disconnected devices
            disconnected_devices = self.last_known_devices - current_device_ids
            for device_id in disconnected_devices:
                log.info(f"Device disconnected: {device_id}")
                
            self.last_known_devices = current_device_ids
            
        except Exception as e:
            log.error(f"Error checking device changes: {e}")
            
    def _block_storage_device(self, device):
        """Block a USB storage device"""
        try:
            drive_letter = device.get('drive_letter')
            if not drive_letter:
                return
                
            log.warning(f"Blocking unauthorized storage device: {device['friendly_name']} ({drive_letter})")
            
            # Method 1: Hide the drive
            self._hide_drive(drive_letter)
            
            # Method 2: Eject the drive
            self._eject_drive(drive_letter)
            
            # Method 3: Disable the device via WMI
            self._disable_wmi_device(device)
            
        except Exception as e:
            log.error(f"Error blocking storage device: {e}")
            
    def _block_peripheral_device(self, device):
        """Block a USB peripheral device"""
        try:
            log.warning(f"Blocking unauthorized peripheral device: {device['friendly_name']}")
            
            # Disable the device via WMI
            self._disable_wmi_device(device)
            
        except Exception as e:
            log.error(f"Error blocking peripheral device: {e}")
            
    def _hide_drive(self, drive_letter):
        """Hide a drive letter from Windows Explorer"""
        try:
            import winreg
            
            # Add drive to NoDrives registry key
            drive_num = ord(drive_letter.upper()) - ord('A')
            no_drives_value = 1 << drive_num
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                             r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", 
                             0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "NoDrives", 0, winreg.REG_DWORD, no_drives_value)
                
            # Refresh Windows Explorer
            os.system("rundll32.exe user32.dll,UpdatePerUserSystemParameters")
            
            log.info(f"Hidden drive {drive_letter} from Explorer")
            
        except Exception as e:
            log.error(f"Error hiding drive {drive_letter}: {e}")
            
    def _eject_drive(self, drive_letter):
        """Eject a USB drive"""
        try:
            import win32api
            import win32con
            
            # Send eject command
            drive_path = f"\\\\.\\{drive_letter}:"
            handle = win32api.CreateFile(drive_path, 
                                       win32con.GENERIC_READ, 
                                       win32con.FILE_SHARE_READ, 
                                       None, 
                                       win32con.OPEN_EXISTING, 
                                       0, 
                                       None)
            
            if handle != win32api.INVALID_HANDLE_VALUE:
                # IOCTL_STORAGE_EJECT_MEDIA
                win32api.DeviceIoControl(handle, 0x2D4808, "", 0, None, 0, None, None)
                win32api.CloseHandle(handle)
                log.info(f"Ejected drive {drive_letter}")
                
        except Exception as e:
            log.error(f"Error ejecting drive {drive_letter}: {e}")
            
    def _disable_wmi_device(self, device):
        """Disable device using WMI"""
        try:
            c = wmi.WMI()
            
            # Find the device by PnP ID
            for pnp_device in c.Win32_PnPEntity():
                if pnp_device.DeviceID == device.get('device_id_wmi'):
                    # Try to disable the device
                    if pnp_device.Disable():
                        log.info(f"Disabled WMI device: {device['friendly_name']}")
                    else:
                        log.warning(f"Failed to disable WMI device: {device['friendly_name']}")
                    break
                    
        except Exception as e:
            log.error(f"Error disabling WMI device: {e}")
            
    def _verify_device_fingerprint(self, device):
        """Verify device fingerprint for registered storage devices"""
        try:
            drive_letter = device.get('drive_letter')
            if not drive_letter:
                return
                
            details = self.db.get_device_details(device['canonical_id'])
            if not details or not details.get('structural_fingerprint'):
                return
                
            # Verify the device
            is_valid = self.fingerprinter.verify_device(
                drive_letter, 
                details['structural_fingerprint'], 
                details['lockfile_signature']
            )
            
            if is_valid:
                log.info(f"Device fingerprint verified: {device['friendly_name']}")
            else:
                log.warning(f"Device fingerprint INVALID - blocking: {device['friendly_name']}")
                self._block_storage_device(device)
                
        except Exception as e:
            log.error(f"Error verifying device fingerprint: {e}")

def main():
    """Main entry point for the background service"""
    log.info("Starting USB Guard Background Service")
    
    service = USBGuardService()
    
    try:
        service.start()
        
        # Keep the service running
        while True:
            time.sleep(60)  # Sleep for 1 minute
            
    except KeyboardInterrupt:
        log.info("Received shutdown signal")
        service.stop()
    except Exception as e:
        log.error(f"Service error: {e}")
        service.stop()

if __name__ == "__main__":
    main()
