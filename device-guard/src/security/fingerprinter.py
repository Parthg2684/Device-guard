import os
import wmi
import hashlib
from datetime import datetime, timezone
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
from src.utils.logger import log

LOCK_FOLDER_NAME = ".device_guard"
LOCK_FILE_NAME = "lockfile.bin"
HOST_KEY_FILE = "host_key.pem"

class Fingerprinter:
    def __init__(self):
        # NOTE: We no longer initialize wmi.WMI() here to ensure thread safety.
        self.host_key = self._manage_host_key()

    def _manage_host_key(self):
        key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", HOST_KEY_FILE)
        try:
            if os.path.exists(key_path):
                log.info(f"Loading existing host key from {key_path}")
                with open(key_path, "rb") as f:
                    private_key = serialization.load_pem_private_key(f.read(), password=None)
            else:
                log.info(f"No host key found. Generating and saving a new one at {key_path}")
                private_key = ec.generate_private_key(ec.SECP256R1())
                with open(key_path, "wb") as f:
                    f.write(private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ))
            return private_key
        except Exception as e:
            log.error(f"Failed to load or generate host key: {e}")
            return None

    def _get_physical_disk(self, drive_letter):
        try:
            # Create a fresh WMI connection for the current thread
            wmi_conn = wmi.WMI()
            query = f"ASSOCIATORS OF {{Win32_LogicalDisk.DeviceID='{drive_letter}'}} WHERE AssocClass = Win32_LogicalDiskToPartition"
            partitions = wmi_conn.query(query)
            if partitions:
                query = f"ASSOCIATORS OF {{Win32_DiskPartition.DeviceID='{partitions[0].DeviceID}'}} WHERE AssocClass = Win32_DiskDriveToDiskPartition"
                physical_disks = wmi_conn.query(query)
                if physical_disks:
                    return physical_disks[0]
        except Exception as e:
            log.error(f"Failed to get physical disk for {drive_letter}: {e}")
        return None

    def calculate_structural_fingerprint(self, drive_letter):
        disk = self._get_physical_disk(drive_letter)
        if not disk:
            log.error(f"Cannot calculate fingerprint: Could not find physical disk for {drive_letter}.")
            return None
        try:
            source_string = f"Model:{disk.Model}-Size:{disk.Size}-Signature:{disk.Signature}"
            log.info(f"Generating fingerprint from source: {source_string}")
            fingerprint = hashlib.sha256(source_string.encode('utf-8')).hexdigest()
            log.info(f"Calculated stable fingerprint: {fingerprint[:16]}...")
            return fingerprint
        except Exception as e:
            log.error(f"Failed to get hardware properties for fingerprint: {e}")
            return None

    def create_signed_lockfile(self, drive_letter):
        if not self.host_key:
            log.error("Cannot create lockfile: Host key is not available.")
            return None
        try:
            lock_folder_path = os.path.join(drive_letter, LOCK_FOLDER_NAME)
            lockfile_path = os.path.join(lock_folder_path, LOCK_FILE_NAME)
            if not os.path.exists(lock_folder_path):
                os.makedirs(lock_folder_path)
                os.system(f'attrib +h "{lock_folder_path}"')
            payload = f"DeviceGuardLock_RegisteredOn_{datetime.now(timezone.utc).isoformat()}".encode('utf-8')
            signature = self.host_key.sign(payload, ec.ECDSA(hashes.SHA256()))
            with open(lockfile_path, "w") as f:
                f.write(f"{signature.hex()}::{payload.decode('utf-8')}")
            log.info(f"Successfully created lockfile. Signature: {signature.hex()[:16]}...")
            return signature.hex()
        except Exception as e:
            log.error(f"Failed to create signed lockfile on {drive_letter}: {e}")
            return None

    def verify_device(self, drive_letter, expected_fingerprint, expected_signature_hex):
        log.info(f"Performing full verification on drive {drive_letter}.")
        current_fingerprint = self.calculate_structural_fingerprint(drive_letter)
        if not current_fingerprint or current_fingerprint != expected_fingerprint:
            log.warning(f"Verification FAILED for {drive_letter}: Structural fingerprint mismatch.")
            log.debug(f"  Expected: {expected_fingerprint}")
            log.debug(f"  Got:      {current_fingerprint}")
            return False
        log.info(f"Structural fingerprint for {drive_letter} is VALID.")
        if not self.host_key:
            log.error("Cannot verify lockfile: Host key is not available.")
            return False
        lockfile_path = os.path.join(drive_letter, LOCK_FOLDER_NAME, LOCK_FILE_NAME)
        if not os.path.exists(lockfile_path):
            log.warning(f"Verification FAILED for {drive_letter}: Lockfile not found at {lockfile_path}.")
            return False
        try:
            with open(lockfile_path, "r") as f:
                content = f.read()
                signature_hex, payload_str = content.split("::", 1)
            signature = bytes.fromhex(signature_hex)
            payload = payload_str.encode('utf-8')
            public_key = self.host_key.public_key()
            public_key.verify(signature, payload, ec.ECDSA(hashes.SHA256()))
            if signature_hex != expected_signature_hex:
                 log.warning(f"Verification FAILED for {drive_letter}: Lockfile signature does not match database record.")
                 return False
            log.info(f"Lockfile signature for {drive_letter} is VALID.")
            return True
        except InvalidSignature:
            log.warning(f"Verification FAILED for {drive_letter}: Lockfile has an invalid signature (tampered).")
            return False
        except Exception as e:
            log.error(f"An error occurred during lockfile verification for {drive_letter}: {e}")
            return False