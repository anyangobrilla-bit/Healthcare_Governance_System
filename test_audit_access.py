import sqlite3
from it_management import view_audit_logs

doctor = {
    "user_id": 2,
    "role": "Doctor",
    "branch": "Nairobi Main Branch"
}

print("=" * 60)
print("AUDIT LOG ACCESS CONTROL TEST")
print("=" * 60)

try:
    view_audit_logs(doctor)
    print("FAIL: Doctor was able to access audit logs.")

except PermissionError as error:
    print("PASS: Doctor was denied access.")
    print("Reason:", error)

connection = sqlite3.connect("healthcare.db")
connection.row_factory = sqlite3.Row

record = connection.execute("""
    SELECT user_id, action, details
    FROM audit_logs
    WHERE action = 'ACCESS_DENIED'
    ORDER BY log_id DESC
    LIMIT 1
""").fetchone()

if record and record["user_id"] == 2:
    print("\nPASS: Denied audit access was recorded.")
    print("Action:", record["action"])
    print("Details:", record["details"])
else:
    print("\nCHECK: No matching denial record was found.")

connection.close()