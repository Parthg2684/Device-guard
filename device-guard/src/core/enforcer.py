import subprocess
from src.utils.logger import log

def block_device(device_id_wmi):
    """
    Disables a PnP device using PowerShell. Requires Administrator rights.
    """
    try:
        log.warning(f"ENFORCEMENT: Blocking unregistered device: {device_id_wmi}")
        # Sanitize the ID for the command line
        safe_device_id = device_id_wmi.replace("'", "''")
        
        # PowerShell command to get the device by its instance ID and disable it
        command = f"""
        $device = Get-PnpDevice -InstanceId '{safe_device_id}';
        if ($device -and $device.Status -ne 'Error') {{
            Disable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false;
        }}
        """
        
        # We use powershell.exe -Command for this complex command
        result = subprocess.run(
            ["powershell.exe", "-Command", command],
            capture_output=True, text=True, check=True
        )
        log.info(f"Block command for '{device_id_wmi}' executed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to block device '{device_id_wmi}'. Error: {e.stderr}")
        return False
    except Exception as e:
        log.error(f"An unexpected error occurred while blocking device: {e}")
        return False