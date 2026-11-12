from backup_management import restore_database_backup

it_officer = {
    "user_id": 5,
    "role": "IT Officer",
    "branch": "Nairobi Main Branch"
}

try:
    restore_database_backup(
        it_officer,
        "healthcare_backup_20261109_161458.db",
        "unauthorized_it_restore_test.db"
    )

    print("FAIL: IT Officer was allowed to restore a database.")

except PermissionError as error:
    print("PASS: IT Officer restoration was denied.")
    print("Reason:", error)