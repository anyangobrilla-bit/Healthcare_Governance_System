
from auth import authenticate_user
from database import get_connection

username = "unknown_security_test_user"

print("UNKNOWN USER LOGIN SECURITY TEST")
print("=" * 45)

user = authenticate_user(username, "FakePassword123!")

if user is None:
    print("PASS: Unknown username was rejected.")
else:
    print("FAIL: Unknown username was accepted.")

with get_connection() as connection:
    log = connection.execute(
        """
        SELECT action, details
        FROM audit_logs
        WHERE action = 'Failed login attempt'
          AND details = ?
        ORDER BY log_id DESC
        LIMIT 1
        """,
        (f"Unknown username: {username}",)
    ).fetchone()

if log:
    print("PASS: Unknown username attempt was recorded.")
    print(f"Audit details: {log['details']}")
else:
    print("FAIL: No audit record was found.")

print("\nUNKNOWN USER TEST COMPLETED.")
