
from database import get_connection

print("IT OFFICER ACCESS DENIAL AUDIT CHECK")
print("=" * 45)

with get_connection() as connection:
    logs = connection.execute(
        """
        SELECT log_id, user_id, action, details, timestamp
        FROM audit_logs
        WHERE action = 'ACCESS_DENIED'
          AND user_id = 5
        ORDER BY log_id DESC
        LIMIT 10
        """
    ).fetchall()

if not logs:
    print("\nNo denied access attempts found for the IT Officer.")
else:
    for log in logs:
        print(f"\nLog ID: {log['log_id']}")
        print(f"User ID: {log['user_id']}")
        print(f"Action: {log['action']}")
        print(f"Details: {log['details']}")
        print(f"Timestamp: {log['timestamp']}")
        print("-" * 45)

    print("\nPASS: IT Officer access denial records retrieved.")
