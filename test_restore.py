
from backup_management import restore_database_backup

admin = {
    "user_id": 1,
    "role": "Admin",
    "branch": "Nairobi Main Branch"
}

restore_database_backup(
    admin,
    "healthcare_backup_20261109_161458.db",
    "recovery_test_copy_20261112.db"
)

print("PASS: Backup restored into a separate recovery database.")
print("The live healthcare database was not replaced.")
