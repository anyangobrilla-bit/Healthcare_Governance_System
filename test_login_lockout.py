
import secrets

from auth import create_user, authenticate_user
from database import get_connection


print("LOGIN LOCKOUT SECURITY TEST")
print("=" * 45)

# Generate unique temporary test credentials.
suffix = secrets.token_hex(4)

lockout_username = f"lockout_test_{suffix}"
reset_username = f"reset_test_{suffix}"

test_password = secrets.token_urlsafe(16)

created_accounts = []
failures = []


def audit_count(action):
    """Count audit records for a particular action."""

    with get_connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE action = ?",
            (action,)
        ).fetchone()[0]


# Capture existing audit counts before testing.
locked_before = audit_count("Account temporarily locked")
blocked_before = audit_count(
    "Login blocked - temporary lockout"
)

try:
    # Create two temporary fictional staff accounts.
    create_user(
        "Lockout Security Test",
        lockout_username,
        test_password,
        "Doctor",
        "Test Branch"
    )
    created_accounts.append(lockout_username)

    create_user(
        "Reset Security Test",
        reset_username,
        test_password,
        "Doctor",
        "Test Branch"
    )
    created_accounts.append(reset_username)

    print("\nTEST 1: Five consecutive incorrect passwords")

    for attempt in range(1, 6):
        result = authenticate_user(
            lockout_username,
            "Wrong_Test_Password!"
        )

        print(
            f"Attempt {attempt}: "
            f"{'UNEXPECTED LOGIN' if result else 'Rejected'}"
        )

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT failed_attempts, locked_until
            FROM login_attempts
            WHERE username = ?
            """,
            (lockout_username,)
        ).fetchone()

    if row and row["failed_attempts"] == 5 and row["locked_until"]:
        print("PASS: Lockout applied after five failed attempts.")
    else:
        print("FAIL: Expected five attempts and an active lockout.")
        failures.append("Five-attempt lockout")

    print("\nTEST 2: Correct password during lockout")

    result = authenticate_user(
        lockout_username,
        test_password
    )

    if result is None:
        print("PASS: Correct password rejected during lockout.")
    else:
        print("FAIL: Login was allowed during lockout.")
        failures.append("Password accepted during lockout")

    print("\nTEST 3: Successful password verification resets attempts")

    authenticate_user(
        reset_username,
        "Wrong_Test_Password!"
    )

    authenticate_user(
        reset_username,
        "Wrong_Test_Password!"
    )

    result = authenticate_user(
        reset_username,
        test_password
    )

    with get_connection() as connection:
        reset_row = connection.execute(
            """
            SELECT failed_attempts
            FROM login_attempts
            WHERE username = ?
            """,
            (reset_username,)
        ).fetchone()

    if result is not None and reset_row is None:
        print("PASS: Successful password verification cleared attempts.")
    else:
        print("FAIL: Failed-attempt counter was not cleared.")
        failures.append("Failed-attempt reset")

    print("\nTEST 4: Lockout audit logging")

    locked_after = audit_count("Account temporarily locked")
    blocked_after = audit_count(
        "Login blocked - temporary lockout"
    )

    if locked_after > locked_before:
        print("PASS: Account lockout event was audited.")
    else:
        print("FAIL: Account lockout event was not found.")
        failures.append("Lockout audit event")

    if blocked_after > blocked_before:
        print("PASS: Blocked login event was audited.")
    else:
        print("FAIL: Blocked login event was not found.")
        failures.append("Blocked-login audit event")

finally:
    # Deactivate only accounts created by this test.
    if created_accounts:
        with get_connection() as connection:
            for username in created_accounts:
                connection.execute(
                    """
                    UPDATE users
                    SET is_active = 0
                    WHERE username = ?
                    """,
                    (username,)
                )

    print("\nTemporary test accounts deactivated.")
    print("Existing staff accounts and historical test records preserved.")

print("\nTEST SUMMARY")
print("=" * 45)

if failures:
    print("Some tests need attention:")

    for failure in failures:
        print("-", failure)

    raise SystemExit(1)

print("All login lockout tests passed.")
