from backup_retention import cleanup_expired_backups

admin = {
    "user_id": 1,
    "username": "healthadmin",
    "role": "Admin",
    "branch": "Nairobi Main Branch"
}

print("ADMIN BACKUP RETENTION TEST")
print("---------------------------")

try:
    cleanup_expired_backups(admin)
    print("\nPASS: Admin access was accepted.")

except Exception as error:
    print("\nFAIL:", error)