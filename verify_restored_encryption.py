import sqlite3
from pathlib import Path

from encryption import ENCRYPTION_PREFIX, decrypt_value

RESTORED_DB = (
    Path(__file__).resolve().parent
    / "backups"
    / "restored_copies"
    / "encrypted_restore_test.db"
)

print("RESTORED DATABASE ENCRYPTION TEST")
print("-----------------------------------")

if not RESTORED_DB.exists():
    raise FileNotFoundError("Restored database was not found.")

connection = sqlite3.connect(RESTORED_DB)

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
    decrypted = 0

    for row in rows:
        for value in row:
            if value is None or value == "":
                continue

            if value.startswith(ENCRYPTION_PREFIX):
                encrypted += 1
                decrypt_value(value)
                decrypted += 1
            else:
                plaintext += 1

    print("Integrity:", integrity)
    print("Patient records:", len(rows))
    print("Encrypted fields:", encrypted)
    print("Plaintext fields:", plaintext)
    print("Successful decryption checks:", decrypted)

    if integrity == "ok" and plaintext == 0 and encrypted == decrypted:
        print("\nPASS: Restored database encryption verified.")
    else:
        print("\nWARNING: Verification requires investigation.")

finally:
    connection.close()