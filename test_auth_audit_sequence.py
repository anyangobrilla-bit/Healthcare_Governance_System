
import time
import secrets
import pyotp

from auth import create_user, authenticate_user
from database import get_connection, record_audit
from mfa import (
    begin_mfa_enrollment,
    confirm_mfa_enrollment,
    verify_mfa_code,
)


TEST_PASSWORD = f"AuditTest_{secrets.token_urlsafe(16)}"

TEST_ACCOUNTS = [
    (
        f"audit_mfa_success_{secrets.token_hex(4)}",
        "Audit MFA Success Test",
    ),
    (
        f"audit_mfa_failure_{secrets.token_hex(4)}",
        "Audit MFA Failure Test",
    ),
]

created_accounts = []


def cleanup_test_accounts():
    """Deactivate temporary accounts and preserve security records."""

    for user_id, username in created_accounts:

        with get_connection() as connection:
            connection.execute(
                """
                UPDATE users
                SET is_active = 0
                WHERE user_id = ?
                """,
                (user_id,),
            )

    if created_accounts:
        print("\nTemporary test accounts deactivated.")
        print("MFA settings and audit history preserved.")


def create_authenticated_test_user(username, full_name):
    """Create a temporary account and verify its password."""

    user_id = create_user(
        full_name,
        username,
        TEST_PASSWORD,
        "Doctor",
        "Audit Test Branch",
    )

    # Track the account immediately so cleanup can deactivate it
    # even if a later authentication step fails.
    created_accounts.append((user_id, username))

    user = authenticate_user(username, TEST_PASSWORD)

    if not user:
        raise RuntimeError(
            f"Password authentication failed for {username}."
        )

    return user


def enroll_test_user(user):
    """Enable MFA for a temporary test account."""

    secret, _ = begin_mfa_enrollment(user)

    totp = pyotp.TOTP(secret)

    enrolled = confirm_mfa_enrollment(
        user,
        totp.now(),
    )

    if not enrolled:
        raise RuntimeError("MFA enrollment failed.")

    return totp


def get_user_audit_logs(user_id):
    """Retrieve audit events for one test account."""

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT log_id, action, details
            FROM audit_logs
            WHERE user_id = ?
            ORDER BY log_id ASC
        """, (user_id,)).fetchall()

    return [dict(row) for row in rows]


def wait_for_fresh_code(totp):
    """Wait until the next TOTP interval."""

    current_counter = int(time.time() // totp.interval)
    next_counter = current_counter + 1

    wait_seconds = (
        next_counter * totp.interval - time.time()
    ) + 1

    print("Waiting for a fresh MFA code...")
    time.sleep(wait_seconds)

    return totp.now()


def test_successful_mfa_audit_sequence():

    username, full_name = TEST_ACCOUNTS[0]

    user = create_authenticated_test_user(
        username,
        full_name,
    )

    totp = enroll_test_user(user)

    print("Password verification: PASS")
    print("MFA enrollment: PASS")

    valid_code = wait_for_fresh_code(totp)

    mfa_verified = verify_mfa_code(
        user,
        valid_code,
    )

    if not mfa_verified:
        raise RuntimeError("Valid MFA verification failed.")

    # Record successful login only after MFA succeeds.
    record_audit(
        user["user_id"],
        "Successful login",
        "User",
        user["user_id"],
        (
            f"Role: {user['role']}; "
            "Authentication: password and MFA."
        ),
    )

    logs = get_user_audit_logs(user["user_id"])

    password_log = next(
        (
            log for log in logs
            if log["action"] == "Password verified"
        ),
        None,
    )

    mfa_log = next(
        (
            log for log in logs
            if log["action"] == "MFA verification successful"
        ),
        None,
    )

    login_log = next(
        (
            log for log in logs
            if log["action"] == "Successful login"
        ),
        None,
    )

    if not all((password_log, mfa_log, login_log)):
        raise RuntimeError(
            "One or more expected authentication audit events are missing."
        )

    if not (
        password_log["log_id"]
        < mfa_log["log_id"]
        < login_log["log_id"]
    ):
        raise RuntimeError(
            "Authentication audit events are in the wrong order."
        )

    if "Authentication: password and MFA." not in login_log["details"]:
        raise RuntimeError(
            "Successful login audit does not identify both factors."
        )

    print("Password verification audit: PASS")
    print("MFA verification audit: PASS")
    print("Successful login audit: PASS")
    print("Authentication audit sequence: PASS")


def test_failed_mfa_does_not_record_successful_login():

    username, full_name = TEST_ACCOUNTS[1]

    user = create_authenticated_test_user(
        username,
        full_name,
    )

    totp = enroll_test_user(user)

    print("Password verification: PASS")
    print("MFA enrollment: PASS")

    # Generate a code that cannot match the current,
    # previous, or next accepted TOTP interval.
    current_counter = int(time.time() // totp.interval)

    valid_window_codes = {
        totp.at(counter * totp.interval)
        for counter in range(
            current_counter - 1,
            current_counter + 2,
        )
        if counter >= 0
    }

    invalid_code = next(
        f"{number:06d}"
        for number in range(1000000)
        if f"{number:06d}" not in valid_window_codes
    )

    mfa_verified = verify_mfa_code(
        user,
        invalid_code,
    )

    if mfa_verified:
        raise RuntimeError(
            "An invalid MFA code was unexpectedly accepted."
        )

    logs = get_user_audit_logs(user["user_id"])

    successful_login_logs = [
        log for log in logs
        if log["action"] == "Successful login"
    ]

    if successful_login_logs:
        raise RuntimeError(
            "A successful login was recorded despite failed MFA."
        )

    print("Invalid MFA code rejected: PASS")
    print("Failed MFA did not produce successful login audit: PASS")


def run_audit_sequence_tests():

    failures = []

    try:
        print("\nTEST 1: SUCCESSFUL MFA AUDIT SEQUENCE")
        test_successful_mfa_audit_sequence()

        print("\nTEST 2: FAILED MFA AUDIT SEQUENCE")
        test_failed_mfa_does_not_record_successful_login()

    except Exception as error:
        failures.append(type(error).__name__)
        print("\nTEST ERROR:", type(error).__name__)

    finally:
        try:
            cleanup_test_accounts()
        except Exception as error:
            failures.append(
                f"Cleanup error: {type(error).__name__}"
            )
            print("CLEANUP ERROR:", type(error).__name__)

    print("\nTEST SUMMARY")
    print("=" * 45)

    if failures:
        for failure in failures:
            print("FAIL:", failure)

        raise SystemExit(1)

    print("All authentication audit sequence tests passed.")


if __name__ == "__main__":
    run_audit_sequence_tests()
