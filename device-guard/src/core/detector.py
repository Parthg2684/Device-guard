import wmi
from src.utils.logger import log

def get_separated_usb_devices():
    """
    Detects all connected USB devices and separates them into storage and other categories.
    This is a more robust version based on the original detection logic.
    """
    storage_devices, other_devices = [], []
    try:
        wmi_conn = wmi.WMI()
        processed_ids = set()

        # Step 1: Create a map of USB storage serial numbers to drive letters
        drive_map = {}
        for disk in wmi_conn.Win32_DiskDrive(InterfaceType="USB"):
            # The PNPDeviceID contains the serial number in the last part
            serial = disk.PNPDeviceID.split('\\')[-1]
            if '&' not in serial:  # A simple check for a valid serial
                for partition in disk.associators("Win32_DiskDriveToDiskPartition"):
                    for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                        drive_map[serial] = logical_disk.DeviceID
        
        # Step 2: Iterate through all USB PnP devices and USBSTOR devices
        for device in wmi_conn.Win32_PnPEntity():
            # Check for both USB\ and USBSTOR\ devices
            if not device.DeviceID:
                continue
                
            is_usb = device.DeviceID.startswith("USB\\")
            is_usbstor = device.DeviceID.startswith("USBSTOR\\")
            
            if not (is_usb or is_usbstor):
                continue
            
            # Parse VID, PID, and Serial from the DeviceID
            vid_pid_part = None
            vid, pid = "", ""
            
            if is_usb:
                # Regular USB PnP device
                vid_pid_part = next((p for p in device.DeviceID.split('\\') if 'VID_' in p and 'PID_' in p), None)
                if vid_pid_part:
                    vid = vid_pid_part.split('VID_')[1].split('&')[0]
                    pid = vid_pid_part.split('PID_')[1].split('&')[0]
            elif is_usbstor:
                # USB Storage device - extract VID/PID from VEN_ and PROD_ fields
                parts = device.DeviceID.split('\\')
                if len(parts) >= 2:
                    ven_prod = parts[1]
                    # Extract VID from VEN_ field
                    if 'VEN_' in ven_prod:
                        ven_part = ven_prod.split('VEN_')[1].split('&')[0]
                        # SanDisk shows as '_USB' which means VID_0781, handle this mapping
                        if ven_part == '_USB':
                            vid = '0781'  # SanDisk's VID
                        else:
                            vid = ven_part.replace('_', '')
                    # Extract PID from PROD_ field
                    if 'PROD_' in ven_prod:
                        prod_part = ven_prod.split('PROD_')[1].split('&')[0]
                        # For SanDisk 3.2Gen1, the actual PID is 5591
                        if prod_part == '_SANDISK_3.2GEN1':
                            pid = '5591'  # SanDisk USB Drive PID
                        else:
                            pid = prod_part.replace('_', '')
            
            if not vid or not pid:
                continue
            
            # Extract serial number
            parts = device.DeviceID.split('\\')
            serial = parts[-1] if len(parts) > 2 and '&' not in parts[-1] else "NO_SERIAL"
            
            canonical_id = f"VID_{vid}&PID_{pid}&SN_{serial if serial != 'NO_SERIAL' else 'NO_SERIAL'}"

            # Avoid duplicate entries
            if canonical_id in processed_ids:
                continue
            processed_ids.add(canonical_id)

            device_info = {
                "friendly_name": device.Caption or "Unknown USB Device",
                "vid": vid,
                "pid": pid,
                "serial_number": serial,
                "canonical_id": canonical_id,
                "device_id_wmi": device.DeviceID
            }

            # Step 3: Separate devices based on the drive map
            drive_letter = drive_map.get(serial)
            if drive_letter:
                device_info['drive_letter'] = drive_letter
                storage_devices.append(device_info)
            else:
                device_info['drive_letter'] = None
                other_devices.append(device_info)
                
    except Exception as e:
        log.error(f"An error occurred in the USB detection logic: {e}")
        
    log.info(f"Detector found {len(storage_devices)} storage devices and {len(other_devices)} other devices.")
    return storage_devices, other_devices