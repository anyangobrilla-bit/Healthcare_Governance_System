
import time
import secrets
import pyotp

from auth import create_user
from database import get_connection
from mfa import (
    begin_mfa_enrollment,
    confirm_mfa_enrollment,
    verify_mfa_code,
    is_mfa_enabled,
)


USERNAME = f"mfa_security_test_{secrets.token_hex(4)}"
TEST_PASSWORD = f"TestOnly_{secrets.token_urlsafe(16)}"


def cleanup_test_account(user_id):
    """Deactivate the temporary account and preserve its records."""

    if user_id is None:
        return

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET is_active = 0
            WHERE user_id = ?
            """,
            (user_id,),
        )

    print("Temporary test account deactivated.")
    print("MFA settings and audit history preserved.")


def run_mfa_test():

    user_id = None
    failures = []

    print("MFA SECURITY TEST")
    print("=" * 45)

    try:
        # 1. Create a temporary fictional staff account.
        user_id = create_user(
            "MFA Security Test",
            USERNAME,
            TEST_PASSWORD,
            "Doctor",
            "MFA Test Branch",
        )

        user = {
            "user_id": user_id,
            "full_name": "MFA Security Test",
            "username": USERNAME,
            "role": "Doctor",
            "branch": "MFA Test Branch",
        }

        print("Temporary account creation: PASS")

        # 2. Begin MFA enrollment.
        secret, provisioning_uri = begin_mfa_enrollment(user)

        totp = pyotp.TOTP(secret)

        print("MFA enrollment started: PASS")

        # 3. Confirm MFA enrollment.
        enrollment_code = totp.now()

        enrolled = confirm_mfa_enrollment(
            user,
            enrollment_code,
        )

        if enrolled:
            print("MFA enrollment confirmation: PASS")
        else:
            print("MFA enrollment confirmation: FAIL")
            failures.append("MFA enrollment confirmation")

        if not enrolled:
            raise RuntimeError("MFA enrollment failed.")

        # 4. Check MFA enabled status.
        enabled = is_mfa_enabled(user_id)

        if enabled:
            print("MFA enabled status: PASS")
        else:
            print("MFA enabled status: FAIL")
            failures.append("MFA enabled status")

        if not enabled:
            raise RuntimeError("MFA was not enabled.")

        # 5. Wait for a fresh authentication code.
        print("\nWaiting for a fresh MFA code...")

        current_counter = int(time.time() // totp.interval)
        next_counter = current_counter + 1

        wait_seconds = (
            next_counter * totp.interval - time.time()
        ) + 1

        time.sleep(wait_seconds)

        # Generate a fresh code without displaying it.
        valid_code = totp.now()

        # 6. Verify the fresh MFA code.
        verified = verify_mfa_code(
            user,
            valid_code,
        )

        if verified:
            print("Valid MFA code verification: PASS")
        else:
            print("Valid MFA code verification: FAIL")
            failures.append("Valid MFA code verification")

        if not verified:
            raise RuntimeError("Valid MFA code was rejected.")

        # 7. Attempt to reuse the same code.
        replay_rejected = not verify_mfa_code(
            user,
            valid_code,
        )

        if replay_rejected:
            print("MFA replay protection: PASS")
        else:
            print("MFA replay protection: FAIL")
            failures.append("MFA replay protection")

        if not replay_rejected:
            raise RuntimeError("MFA replay protection failed.")

    except Exception as error:
        if not failures:
            failures.append(
                f"Unexpected test error: {type(error).__name__}"
            )

        print("\nTEST ERROR:", type(error).__name__)

    finally:
        cleanup_test_account(user_id)

    print("\nTEST SUMMARY")
    print("=" * 45)

    if failures:
        for failure in failures:
            print("FAIL:", failure)

        raise SystemExit(1)

    print("All MFA security tests passed.")


if __name__ == "__main__":
    run_mfa_test()
