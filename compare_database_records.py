import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASES = {
    "LIVE DATABASE": BASE_DIR / "healthcare.db",
    "RESTORED DATABASE": (
        BASE_DIR
        / "backups"
        / "restored_copies"
        / "encrypted_restore_test.db"
    )
}

TABLES = [
    "users",
    "patients",
    "incidents",
    "risks",
    "audit_logs"
]

print("HEALTHCARE DATABASE RECORD COMPARISON")
print("--------------------------------------")

for label, database_path in DATABASES.items():
    print(f"\n{label}")

    if not database_path.exists():
        print("ERROR: Database file not found.")
        continue

    connection = sqlite3.connect(database_path)

    try:
        for table in TABLES:
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"{table}: {count}")

    finally:
        connection.close()