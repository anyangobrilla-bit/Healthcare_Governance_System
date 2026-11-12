import sqlite3
from pathlib import Path

database_path = (
    Path(__file__).resolve().parent
    / "backups"
    / "restored_copies"
    / "encrypted_restore_test.db"
)

connection = sqlite3.connect(database_path)

try:
    print("RESTORED DATABASE TABLES")
    print("------------------------")

    tables = connection.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type = ? ORDER BY name",
        ("table",)
    ).fetchall()

    for table in tables:
        print("-", table[0])

    print("\nTotal tables:", len(tables))

finally:
    connection.close()