
import secrets
from datetime import datetime, timedelta, timezone

from auth import create_user
from database import get_connection
from mfa import (
    record_failed_mfa_attempt,
    check_mfa_lockout,
    MFA_MAX_FAILED_ATTEMPTS,
    MFA_LOCKOUT_MINUTES,
)


USERNAME = f"mfa_lockout_test_{secrets.token_hex(4)}"
TEST_PASSWORD = f"TestOnly_{secrets.token_urlsafe(16)}"


def run_test():
    user_id = None
    failures = []

    print("MFA LOCKOUT SECURITY TEST")
    print("=" * 45)

    try:
        user_id = create_user(
            "MFA Lockout Test",
            USERNAME,
            TEST_PASSWORD,
            "Doctor",
            "MFA Test Branch",
        )

        user = {
            "user_id": user_id,
            "full_name": "MFA Lockout Test",
            "username": USERNAME,
            "role": "Doctor",
            "branch": "MFA Test Branch",
        }

        print("\nTemporary test account created.")

        print("\nTEST 1: Failed MFA attempts")

        for attempt in range(1, MFA_MAX_FAILED_ATTEMPTS + 1):
            attempts, locked_until = record_failed_mfa_attempt(user)

            print(
                f"Attempt {attempt}: "
                f"{'Lockout triggered' if locked_until else 'Recorded'}"
            )

        if attempts == MFA_MAX_FAILED_ATTEMPTS:
            print("PASS: Five failed attempts recorded.")
        else:
            print("FAIL: Incorrect failed-attempt count.")
            failures.append("Failed-attempt count")

        print("\nTEST 2: Fifteen-minute lockout")

        if locked_until:
            expiry = datetime.fromisoformat(locked_until)
            now = datetime.now(timezone.utc)
            remaining = expiry - now

            if (
                timedelta(minutes=14) < remaining
                <= timedelta(minutes=15, seconds=1)
            ):
                print("PASS: Lockout expiry is approximately 15 minutes.")
            else:
                print("FAIL: Lockout duration is not as expected.")
                failures.append("Lockout duration")
        else:
            print("FAIL: No lockout expiry was assigned.")
            failures.append("Missing lockout expiry")

        print("\nTEST 3: Database persistence")

        with get_connection() as connection:
            saved_record = connection.execute("""
                SELECT failed_attempts, locked_until
                FROM mfa_login_attempts
                WHERE user_id = ?
            """, (user_id,)).fetchone()

        persistent = (
            saved_record is not None
            and saved_record["failed_attempts"] == MFA_MAX_FAILED_ATTEMPTS
            and saved_record["locked_until"] is not None
        )

        if persistent:
            print("PASS: Lockout details persisted in the database.")
        else:
            print("FAIL: Lockout details were not persisted.")
            failures.append("Database persistence")

        print("\nTEST 4: Blocked MFA access")

        blocked = check_mfa_lockout(user)

        if blocked:
            print("PASS: Account blocked during active lockout.")
        else:
            print("FAIL: Account was not blocked.")
            failures.append("Active lockout enforcement")

        print("\nTEST 5: Audit logging")

        with get_connection() as connection:
            audit_rows = connection.execute("""
                SELECT action
                FROM audit_logs
                WHERE user_id = ?
                  AND action IN (
                      'MFA verification failed',
                      'MFA account temporarily locked',
                      'MFA login blocked - temporary lockout'
                  )
            """, (user_id,)).fetchall()

        audit_actions = {row["action"] for row in audit_rows}

        expected_actions = {
            "MFA account temporarily locked",
            "MFA login blocked - temporary lockout",
        }

        if expected_actions.issubset(audit_actions):
            print("PASS: Lockout and blocked-login events audited.")
        else:
            print("FAIL: Required MFA audit events are missing.")
            failures.append("MFA audit logging")

    except Exception as error:
        failures.append(f"Unexpected test error: {type(error).__name__}")
        print("\nTEST ERROR:", type(error).__name__)

    finally:
        if user_id is not None:
            with get_connection() as connection:
                connection.execute("""
                    UPDATE users
                    SET is_active = 0
                    WHERE user_id = ?
                """, (user_id,))

            print("\nTemporary test account deactivated.")
            print("MFA attempt records and audit history preserved.")

    print("\nTEST SUMMARY")
    print("=" * 45)

    if failures:
        for failure in failures:
            print("FAIL:", failure)

        raise SystemExit(1)

    print("All MFA lockout tests passed.")


if __name__ == "__main__":
    run_test()
