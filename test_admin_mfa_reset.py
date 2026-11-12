
import secrets
import pyotp

from auth import create_user
from database import get_connection
from mfa import (
    admin_reset_mfa,
    prepare_mfa_table,
    begin_mfa_enrollment,
    confirm_mfa_enrollment,
)
from security import verify_password


ADMIN_USERNAME = f"admin_reset_{secrets.token_hex(4)}"
TARGET_USERNAME = f"doctor_reset_{secrets.token_hex(4)}"

ADMIN_PASSWORD = f"AdminTest_{secrets.token_urlsafe(16)}"
TARGET_PASSWORD = f"DoctorTest_{secrets.token_urlsafe(16)}"

created_accounts = []


def check(condition, message):
    print(f"{message}: {'PASS' if condition else 'FAIL'}")

    if not condition:
        raise RuntimeError(message)


def cleanup_test_accounts():
    """Deactivate temporary accounts and preserve security records."""

    for user_id in created_accounts:
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
        print("Audit history and security records preserved.")


def enroll_test_user(user):
    """Create a genuine MFA enrollment for a temporary account."""

    secret, _ = begin_mfa_enrollment(user)

    totp = pyotp.TOTP(secret)

    enrolled = confirm_mfa_enrollment(
        user,
        totp.now(),
    )

    if not enrolled:
        raise RuntimeError("MFA enrollment failed.")

    return totp


def run_admin_mfa_reset_test():

    failures = []

    try:
        prepare_mfa_table()

        print("\nADMINISTRATOR MFA RESET TEST")
        print("=" * 45)

        # 1. Create temporary accounts.
        admin_id = create_user(
            "Temporary MFA Administrator",
            ADMIN_USERNAME,
            ADMIN_PASSWORD,
            "Admin",
            "Test Branch",
        )
        created_accounts.append(admin_id)

        target_id = create_user(
            "Temporary MFA Doctor",
            TARGET_USERNAME,
            TARGET_PASSWORD,
            "Doctor",
            "Test Branch",
        )
        created_accounts.append(target_id)

        admin_user = {
            "user_id": admin_id,
            "username": ADMIN_USERNAME,
            "role": "Admin",
            "full_name": "Temporary MFA Administrator",
            "branch": "Test Branch",
        }

        doctor_user = {
            "user_id": target_id,
            "username": TARGET_USERNAME,
            "role": "Doctor",
            "full_name": "Temporary MFA Doctor",
            "branch": "Test Branch",
        }

        check(True, "Temporary test accounts created")

        # 2. Enroll the doctor in MFA.
        enroll_test_user(doctor_user)

        check(True, "Doctor MFA enrollment created")

        # 3. Create three fictional failed MFA attempts.
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO mfa_login_attempts (
                    user_id,
                    failed_attempts,
                    locked_until,
                    updated_at
                )
                VALUES (?, 3, NULL, datetime('now'))
                """,
                (target_id,),
            )

            # Create ordinary password-login attempts.
            connection.execute(
                """
                INSERT INTO login_attempts (
                    username,
                    failed_attempts,
                    locked_until,
                    updated_at
                )
                VALUES (?, 2, NULL, datetime('now'))
                """,
                (TARGET_USERNAME,),
            )

        # 4. Save the original doctor password hash.
        with get_connection() as connection:
            original_password_hash = connection.execute(
                """
                SELECT password_hash
                FROM users
                WHERE user_id = ?
                """,
                (target_id,),
            ).fetchone()["password_hash"]

        # 5. Perform the administrator MFA reset.
        result = admin_reset_mfa(
            admin_user,
            TARGET_USERNAME,
            "Temporary security recovery test",
            ADMIN_PASSWORD,
        )

        check(result is True, "Administrator MFA reset")

        # 6. Confirm MFA enrollment and failed MFA attempts were removed.
        with get_connection() as connection:

            settings = connection.execute(
                """
                SELECT COUNT(*)
                FROM mfa_settings
                WHERE user_id = ?
                """,
                (target_id,),
            ).fetchone()[0]

            attempts = connection.execute(
                """
                SELECT COUNT(*)
                FROM mfa_login_attempts
                WHERE user_id = ?
                """,
                (target_id,),
            ).fetchone()[0]

        check(settings == 0, "Target MFA enrollment removed")
        check(attempts == 0, "Target MFA failed attempts removed")

        # 7. Confirm ordinary password attempts remain unchanged.
        with get_connection() as connection:
            login_record = connection.execute(
                """
                SELECT failed_attempts
                FROM login_attempts
                WHERE username = ?
                """,
                (TARGET_USERNAME,),
            ).fetchone()

        check(
            login_record is not None
            and login_record["failed_attempts"] == 2,
            "Ordinary password login attempts preserved",
        )

        # 8. Confirm the doctor's password remains unchanged.
        with get_connection() as connection:
            current_hash = connection.execute(
                """
                SELECT password_hash
                FROM users
                WHERE user_id = ?
                """,
                (target_id,),
            ).fetchone()["password_hash"]

        check(
            current_hash == original_password_hash
            and verify_password(TARGET_PASSWORD, current_hash),
            "Doctor password preserved",
        )

        # 9. Confirm the administrator reset was audited.
        with get_connection() as connection:
            audit = connection.execute(
                """
                SELECT user_id, action, record_id, details
                FROM audit_logs
                WHERE user_id = ?
                  AND action = 'MFA reset by administrator'
                  AND record_id = ?
                ORDER BY log_id DESC
                LIMIT 1
                """,
                (admin_id, target_id),
            ).fetchone()

        check(
            audit is not None
            and audit["user_id"] == admin_id
            and audit["record_id"] == target_id
            and TARGET_USERNAME in audit["details"]
            and "Temporary security recovery test" in audit["details"],
            "Administrator reset audit recorded",
        )

        # 10. Confirm a non-administrator cannot reset MFA.
        non_admin_blocked = False

        try:
            admin_reset_mfa(
                doctor_user,
                TARGET_USERNAME,
                "Unauthorized reset test",
                TARGET_PASSWORD,
            )
        except PermissionError:
            non_admin_blocked = True

        check(
            non_admin_blocked,
            "Non-administrator reset rejected",
        )

        # 11. Confirm an incorrect administrator password is rejected.
        wrong_password_blocked = False

        try:
            admin_reset_mfa(
                admin_user,
                TARGET_USERNAME,
                "Incorrect password test",
                "Wrong-Temporary-Password",
            )
        except PermissionError:
            wrong_password_blocked = True

        check(
            wrong_password_blocked,
            "Incorrect administrator password rejected",
        )

        # 12. Confirm administrator self-reset is blocked.
        self_reset_blocked = False

        try:
            admin_reset_mfa(
                admin_user,
                ADMIN_USERNAME,
                "Self-reset test",
                ADMIN_PASSWORD,
            )
        except PermissionError:
            self_reset_blocked = True

        check(
            self_reset_blocked,
            "Administrator self-reset rejected",
        )

    except Exception as error:
        failures.append(type(error).__name__)
        print("\nTEST ERROR:", type(error).__name__)

    finally:
        try:
            cleanup_test_accounts()
        except Exception as error:
            failures.append(f"Cleanup error: {type(error).__name__}")
            print("CLEANUP ERROR:", type(error).__name__)

    print("\nTEST SUMMARY")
    print("=" * 45)

    if failures:
        for failure in failures:
            print("FAIL:", failure)

        raise SystemExit(1)

    print("All administrator MFA reset tests passed.")


if __name__ == "__main__":
    run_admin_mfa_reset_test()
