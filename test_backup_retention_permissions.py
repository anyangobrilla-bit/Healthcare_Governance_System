
from backup_retention import cleanup_expired_backups

it_officer = {
    "user_id": 5,
    "username": "ittest",
    "role": "IT Officer",
    "branch": "Nairobi Main Branch"
}

print("BACKUP RETENTION PERMISSION TEST")
print("--------------------------------")

try:
    cleanup_expired_backups(it_officer)
    print("FAIL: IT Officer was allowed to clean up backups.")

except PermissionError as error:
    print("PASS: IT Officer cleanup was denied.")
    print("Reason:", error)
