import sqlite3
import os
import datetime
from src.utils.logger import log

# Define the path to your SQLite database file
# It will be created in the data directory
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "whitelist.db")

class WhitelistDB:
    def __init__(self, db_path=None):
        """
        Initializes the database connection and creates/updates the table schema.
        """
        if db_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(script_dir, DB_FILE)
        else:
            self.db_path = db_path
            
        self._create_table()

    def _get_connection(self):
        """Helper to get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row # Allows accessing columns by name
        return conn

    def _create_table(self):
        """Creates or updates the whitelisted_devices table schema."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Added new nullable columns for fingerprinting
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS whitelisted_devices (
                    canonical_id TEXT PRIMARY KEY,
                    friendly_name TEXT NOT NULL,
                    device_type TEXT,
                    added_on TEXT NOT NULL,
                    structural_fingerprint TEXT, -- SHA-256 hash of MBR/GPT
                    lockfile_signature TEXT      -- Signature of the hidden lock file
                )
            """)
            # TODO: In a real production app, you would handle migrations here
            # to add the columns if the table already exists. For our purposes,
            # starting with a fresh DB is fine.
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
        finally:
            conn.close()

    def register_device(self, canonical_id, friendly_name, device_type="unknown", structural_fingerprint=None, lockfile_signature=None):
        """
        Registers a device in the whitelist. Can include fingerprint data.
        Returns True on success, False if already exists or on error.
        """
        if not canonical_id or not friendly_name:
            log.error("Failed to register device: canonical_id and friendly_name cannot be empty.")
            return False

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            added_on = datetime.datetime.now().isoformat()
            cursor.execute(
                """INSERT OR IGNORE INTO whitelisted_devices 
                   (canonical_id, friendly_name, device_type, added_on, structural_fingerprint, lockfile_signature) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (canonical_id, friendly_name, device_type, added_on, structural_fingerprint, lockfile_signature)
            )
            if cursor.rowcount > 0:
                conn.commit()
                log.info(f"SUCCESS: Device '{canonical_id}' ({friendly_name}) registered in whitelist.")
                return True
            else:
                log.warning(f"IGNORED: Attempt to register existing device '{canonical_id}'.")
                return False
        except sqlite3.Error as e:
            log.error(f"DATABASE ERROR while registering device '{canonical_id}': {e}")
            return False
        finally:
            conn.close()

    def remove_device(self, canonical_id):
        """
        Removes a device from the whitelist.
        Returns True on success, False if not found or on error.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM whitelisted_devices WHERE canonical_id = ?",
                (canonical_id,)
            )
            if cursor.rowcount > 0:
                conn.commit()
                log.info(f"SUCCESS: Device '{canonical_id}' removed from whitelist.")
                return True
            else:
                log.warning(f"IGNORED: Attempt to remove non-existent device '{canonical_id}'.")
                return False
        except sqlite3.Error as e:
            log.error(f"DATABASE ERROR while removing device '{canonical_id}': {e}")
            return False
        finally:
            conn.close()

    def get_device_details(self, canonical_id):
        """
        Retrieves all details for a device from the whitelist, including fingerprints.
        Returns the device details (as a dict) if found, None otherwise.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM whitelisted_devices WHERE canonical_id = ?",
                (canonical_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            else:
                return None
        except sqlite3.Error as e:
            log.error(f"DATABASE ERROR checking device '{canonical_id}': {e}")
            return None
        finally:
            conn.close()

    def list_devices(self):
        """Lists all devices currently in the whitelist."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM whitelisted_devices ORDER BY friendly_name")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            log.error(f"DATABASE ERROR listing devices: {e}")
            return []
        finally:
            conn.close()

# --- Test / Example Usage (for development) ---
if __name__ == "__main__":
    # For a clean test, delete old database if it exists
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Removed old '{DB_FILE}' for a clean test.")

    db = WhitelistDB()
    
    print(f"\nDatabase path: {db.db_path}")

    # 1. Register a simple device (like a mouse) WITHOUT fingerprint data
    print("\n--- Registering a Simple Device ---")
    registered = db.register_device(
        "VID_046D&PID_C077&SN_NO_SERIAL",
        "Logitech Mouse",
        "input_device"
    )
    print(f"Registered 'Logitech Mouse': {registered}")

    # 2. Register a storage device WITH fingerprint data
    print("\n--- Registering a Fingerprinted Device ---")
    dummy_fingerprint = "a1b2c3d4e5f6..." # This would be a real SHA-256 hash
    dummy_signature = "f6e5d4c3b2a1..." # This would be a real cryptographic signature
    registered = db.register_device(
        "VID_0781&PID_5591&SN_ABCDEF123456",
        "My Secure USB Drive",
        "usb_storage",
        structural_fingerprint=dummy_fingerprint,
        lockfile_signature=dummy_signature
    )
    print(f"Registered 'My Secure USB Drive': {registered}")
    
    # 3. List all devices
    print("\n--- Whitelisted Devices (After Registering) ---")
    all_devices = db.list_devices()
    for dev in all_devices:
        print(dev)
    assert len(all_devices) == 2

    # 4. Get details for the fingerprinted device and check them
    print("\n--- Checking Fingerprinted Device Details ---")
    details = db.get_device_details("VID_0781&PID_5591&SN_ABCDEF123456")
    if details:
        print(f"Found device: {details['friendly_name']}")
        print(f"  Fingerprint from DB: {details['structural_fingerprint']}")
        print(f"  Signature from DB:   {details['lockfile_signature']}")
        assert details['structural_fingerprint'] == dummy_fingerprint
    else:
        print("Could not find the fingerprinted device!")
    
    # 5. Get details for the simple device
    print("\n--- Checking Simple Device Details ---")
    details = db.get_device_details("VID_046D&PID_C077&SN_NO_SERIAL")
    if details:
        print(f"Found device: {details['friendly_name']}")
        print(f"  Fingerprint from DB: {details['structural_fingerprint']}") # Should be None
        assert details['structural_fingerprint'] is None
    else:
        print("Could not find the simple device!")

    print("\nDatabase schema update and tests complete.")