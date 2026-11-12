
import secrets

from database import get_connection
from auth import create_user, authenticate_user


print("SUCCESSFUL PASSWORD AUTHENTICATION TEST")
print("=" * 45)

username = f"active_test_{secrets.token_hex(6)}"
test_password = secrets.token_urlsafe(16)

user_id = None
failures = []

try:
    # Create a temporary active test account.
    user_id = create_user(
        "Active Security Test",
        username,
        test_password,
        "Doctor",
        "Test Branch"
    )

    print("PASS: Temporary active test account created.")

    # Authenticate using the correct password.
    user = authenticate_user(username, test_password)

    if user is not None:
        print("PASS: Correct password was accepted.")
    else:
        print("FAIL: Correct password was rejected.")
        failures.append("Password authentication")

    # Verify that password verification was recorded.
    with get_connection() as connection:
        log = connection.execute(
            """
            SELECT action, details
            FROM audit_logs
            WHERE user_id = ?
              AND action = 'Password verified'
            ORDER BY log_id DESC
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()

    if log:
        print("PASS: Password verification was recorded in the audit log.")
        print(f"Audit details: {log['details']}")
    else:
        print("FAIL: Password verification audit record was not found.")
        failures.append("Password verification audit")

finally:
    # Deactivate only the temporary account created by this test.
    if user_id is not None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE users
                SET is_active = 0
                WHERE user_id = ?
                """,
                (user_id,)
            )

        print("\nTemporary test account deactivated.")
        print("Audit history preserved.")

print("\nTEST SUMMARY")
print("=" * 45)

if failures:
    for failure in failures:
        print("FAIL:", failure)

    raise SystemExit(1)

print("All password authentication tests passed.")
print("Note: Full login completion still requires MFA verification.")
