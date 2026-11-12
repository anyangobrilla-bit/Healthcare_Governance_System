import sqlite3
from pathlib import Path

from encryption import ENCRYPTION_PREFIX, decrypt_value

BACKUP_PATH = (
    Path(__file__).resolve().parent
    / "backups"
    / "healthcare_backup_20261110_105921.db"
)

print("ENCRYPTED BACKUP VERIFICATION")
print("--------------------------------")

if not BACKUP_PATH.exists():
    raise FileNotFoundError("Backup file not found.")

connection = sqlite3.connect(BACKUP_PATH)

try:
    integrity = connection.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    rows = connection.execute("""
        SELECT full_name, date_of_birth, gender,
               phone_number, medical_history, care_notes
        FROM patients
    """).fetchall()

    encrypted = 0
    plaintext = 0
    verified = 0

    for row in rows:
        for value in row:
            if value is None or value == "":
                continue

            if value.startswith(ENCRYPTION_PREFIX):
                encrypted += 1
                decrypt_value(value)
                verified += 1
            else:
                plaintext += 1

    print("Backup exists: True")
    print("Integrity:", integrity)
    print("Patient records:", len(rows))
    print("Encrypted fields:", encrypted)
    print("Plaintext fields:", plaintext)
    print("Successful decryption checks:", verified)

    if integrity == "ok" and plaintext == 0 and encrypted == verified:
        print("\nPASS: Encrypted backup verified successfully.")
    else:
        print("\nWARNING: Backup verification requires investigation.")

finally:
    connection.close()