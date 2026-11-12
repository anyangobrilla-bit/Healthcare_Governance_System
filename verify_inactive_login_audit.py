
from database import get_connection

username = "inactive_security_test"

print("INACTIVE LOGIN AUDIT VERIFICATION")
print("=" * 45)

with get_connection() as connection:
    user = connection.execute(
        "SELECT user_id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if user is None:
        print("FAIL: Test account was not found.")
    else:
        log = connection.execute(
            """
            SELECT action, details, timestamp
            FROM audit_logs
            WHERE user_id = ?
              AND action = 'Blocked login attempt'
            ORDER BY log_id DESC
            LIMIT 1
            """,
            (user["user_id"],)
        ).fetchone()

        if log:
            print("PASS: Blocked login attempt was recorded.")
            print(f"Action: {log['action']}")
            print(f"Details: {log['details']}")
            print(f"Timestamp: {log['timestamp']}")
        else:
            print("FAIL: No blocked login audit record was found.")

print("\nAUDIT VERIFICATION COMPLETED.")
