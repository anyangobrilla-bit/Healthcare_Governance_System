
import sqlite3

connection = sqlite3.connect("healthcare.db")
connection.row_factory = sqlite3.Row

records = connection.execute("""
    SELECT log_id, user_id, action, record_type,
           details, timestamp
    FROM audit_logs
    WHERE action = 'ACCESS_DENIED'
    ORDER BY log_id DESC
    LIMIT 10
""").fetchall()

print("=" * 60)
print("UNAUTHORIZED ACCESS AUDIT VERIFICATION")
print("=" * 60)

if records:
    for record in records:
        print("\nAudit ID:", record["log_id"])
        print("User ID:", record["user_id"])
        print("Action:", record["action"])
        print("Record Type:", record["record_type"])
        print("Details:", record["details"])
        print("Timestamp:", record["timestamp"])
        print("-" * 60)

    print("\nPASS: Denied access attempts were recorded.")

else:
    print("No denied access attempts found.")

connection.close()
