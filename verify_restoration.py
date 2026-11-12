import sqlite3

files = [
    "healthcare.db",
    "backups/restored_copies/admin_restore_test_2026.db"
]

for file in files:
    connection = sqlite3.connect(file)

    integrity = connection.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    patient_count = connection.execute(
        "SELECT COUNT(*) FROM patients"
    ).fetchone()[0]

    print("\nDatabase:", file)
    print("Integrity:", integrity)
    print("Patient records:", patient_count)

    connection.close()