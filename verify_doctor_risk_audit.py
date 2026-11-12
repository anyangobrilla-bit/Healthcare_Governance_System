from database import get_connection

print("DOCTOR RISK ACCESS DENIAL AUDIT CHECK")
print("--------------------------------------")

with get_connection() as connection:
    logs = connection.execute(
        """
        SELECT log_id, user_id, action, record_type, details, timestamp
        FROM audit_logs
        WHERE action = 'ACCESS_DENIED'
          AND details LIKE '%risk.manage%'
        ORDER BY log_id DESC
        LIMIT 10
        """
    ).fetchall()

if logs:
    for log in logs:
        print(f"\nLog ID: {log['log_id']}")
        print(f"User ID: {log['user_id']}")
        print(f"Action: {log['action']}")
        print(f"Record Type: {log['record_type']}")
        print(f"Details: {log['details']}")
        print(f"Timestamp: {log['timestamp']}")

    print("\nPASS: Risk access denials were recorded.")
else:
    print("No risk access denial records found.")