
from backup_management import create_database_backup
from database import get_connection

doctor = {
    "user_id": 2,
    "role": "Doctor",
    "branch": "Nairobi Main Branch"
}

print("=" * 60)
print("DOCTOR BACKUP PERMISSION TEST")
print("=" * 60)

try:
    create_database_backup(doctor)

    print("\nFAIL: Doctor was allowed to create a backup.")

except PermissionError as error:
    print("\nPASS: Doctor was denied backup permission.")
    print("Reason:", error)

    connection = get_connection()

    try:
        audit = connection.execute("""
            SELECT action, details
            FROM audit_logs
            WHERE user_id = ?
              AND action = 'ACCESS_DENIED'
              AND details LIKE ?
            ORDER BY log_id DESC
            LIMIT 1
        """, (2, "%backup.manage%")).fetchone()

        if audit:
            print("\nPASS: Denied attempt was recorded in audit logs.")
            print("Action:", audit["action"])
            print("Details:", audit["details"])
        else:
            print("\nFAIL: Denied attempt was not found in audit logs.")

    finally:
        connection.close()
