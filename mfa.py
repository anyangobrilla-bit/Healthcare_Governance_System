
import pyotp
from datetime import datetime, timezone, timedelta

from database import get_connection, record_audit
from encryption import encrypt_value, decrypt_value
from security import verify_password


ISSUER_NAME = "Healthcare Governance System"

MFA_MAX_FAILED_ATTEMPTS = 5
MFA_LOCKOUT_MINUTES = 15


def prepare_mfa_table():
    """Create MFA settings and persistent failed-attempt tables."""

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS mfa_settings (
                mfa_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                secret_encrypted TEXT NOT NULL,
                is_enabled INTEGER NOT NULL DEFAULT 0,
                last_verified_counter INTEGER NOT NULL DEFAULT -1,
                created_at TEXT NOT NULL,
                enabled_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS mfa_login_attempts (
                user_id INTEGER PRIMARY KEY,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)


def generate_mfa_secret():
    """Generate a unique authenticator secret."""

    return pyotp.random_base32()


def check_mfa_lockout(user):
    """Check whether an account is temporarily locked."""

    prepare_mfa_table()

    user_id = user["user_id"]
    now = datetime.now(timezone.utc)

    with get_connection() as connection:

        row = connection.execute("""
            SELECT failed_attempts, locked_until
            FROM mfa_login_attempts
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        if row is None or not row["locked_until"]:
            return False

        locked_until = datetime.fromisoformat(
            row["locked_until"]
        )

        if now < locked_until:

            connection.execute("""
                INSERT INTO audit_logs (
                    user_id,
                    action,
                    record_type,
                    record_id,
                    details,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                "MFA login blocked - temporary lockout",
                "User",
                user_id,
                f"MFA account locked until {locked_until.isoformat()}.",
                now.isoformat()
            ))

            return True

        connection.execute("""
            DELETE FROM mfa_login_attempts
            WHERE user_id = ?
        """, (user_id,))

    return False


def record_failed_mfa_attempt(user):
    """Record an MFA failure and apply temporary lockout."""

    prepare_mfa_table()

    user_id = user["user_id"]
    now = datetime.now(timezone.utc)

    with get_connection() as connection:

        row = connection.execute("""
            SELECT failed_attempts
            FROM mfa_login_attempts
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        attempts = (
            row["failed_attempts"] if row else 0
        ) + 1

        locked_until = None

        if attempts >= MFA_MAX_FAILED_ATTEMPTS:

            locked_until = (
                now + timedelta(minutes=MFA_LOCKOUT_MINUTES)
            ).isoformat()

        connection.execute("""
            INSERT INTO mfa_login_attempts (
                user_id,
                failed_attempts,
                locked_until,
                updated_at
            )
            VALUES (?, ?, ?, ?)

            ON CONFLICT(user_id) DO UPDATE SET
                failed_attempts = excluded.failed_attempts,
                locked_until = excluded.locked_until,
                updated_at = excluded.updated_at
        """, (
            user_id,
            attempts,
            locked_until,
            now.isoformat()
        ))

        connection.execute("""
            INSERT INTO audit_logs (
                user_id,
                action,
                record_type,
                record_id,
                details,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            (
                "MFA account temporarily locked"
                if locked_until
                else "MFA verification failed"
            ),
            "User",
            user_id,
            (
                f"Failed MFA attempts: {attempts}. "
                f"Locked until {locked_until}."
                if locked_until
                else f"Failed MFA attempts: {attempts}."
            ),
            now.isoformat()
        ))

    return attempts, locked_until


def reset_mfa_failed_attempts(user_id):
    """Clear failed MFA attempts after successful verification."""

    with get_connection() as connection:

        connection.execute("""
            DELETE FROM mfa_login_attempts
            WHERE user_id = ?
        """, (user_id,))


def begin_mfa_enrollment(user):
    """Create a new pending authenticator enrollment."""

    prepare_mfa_table()

    user_id = user["user_id"]
    username = user["username"]

    with get_connection() as connection:

        existing = connection.execute("""
            SELECT is_enabled
            FROM mfa_settings
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        if existing and existing["is_enabled"] == 1:

            raise ValueError(
                "MFA is already enabled. Contact an administrator "
                "for an authorized reset."
            )

        secret = generate_mfa_secret()
        encrypted_secret = encrypt_value(secret)

        connection.execute("""
            INSERT INTO mfa_settings (
                user_id,
                secret_encrypted,
                is_enabled,
                last_verified_counter,
                created_at,
                enabled_at
            )
            VALUES (?, ?, 0, -1, ?, NULL)

            ON CONFLICT(user_id) DO UPDATE SET
                secret_encrypted = excluded.secret_encrypted,
                is_enabled = 0,
                last_verified_counter = -1,
                created_at = excluded.created_at,
                enabled_at = NULL
        """, (
            user_id,
            encrypted_secret,
            datetime.now(timezone.utc).isoformat()
        ))

    record_audit(
        user_id,
        "MFA enrollment started",
        "User",
        user_id,
        "A pending authenticator enrollment was created."
    )

    totp = pyotp.TOTP(secret)

    provisioning_uri = totp.provisioning_uri(
        name=username,
        issuer_name=ISSUER_NAME
    )

    return secret, provisioning_uri


def confirm_mfa_enrollment(user, code):
    """Verify the first authenticator code and enable MFA."""

    prepare_mfa_table()

    user_id = user["user_id"]

    with get_connection() as connection:

        settings = connection.execute("""
            SELECT secret_encrypted, is_enabled
            FROM mfa_settings
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        if settings is None or settings["is_enabled"] == 1:
            return False

        secret = decrypt_value(settings["secret_encrypted"])
        totp = pyotp.TOTP(secret)

        now = datetime.now(timezone.utc)
        current_counter = totp.timecode(now)

        matched_counter = None

        for counter in (
            current_counter - 1,
            current_counter,
            current_counter + 1
        ):

            if counter < 0:
                continue

            if totp.verify(
                code,
                for_time=counter * totp.interval
            ):
                matched_counter = counter
                break

        if matched_counter is None:

            connection.execute("""
                INSERT INTO audit_logs (
                    user_id,
                    action,
                    record_type,
                    record_id,
                    details,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                "MFA enrollment verification failed",
                "User",
                user_id,
                "Invalid authenticator code.",
                now.isoformat()
            ))

            return False

        connection.execute("""
            UPDATE mfa_settings
            SET is_enabled = 1,
                last_verified_counter = ?,
                enabled_at = ?
            WHERE user_id = ?
        """, (
            matched_counter,
            now.isoformat(),
            user_id
        ))

    record_audit(
        user_id,
        "MFA enabled",
        "User",
        user_id,
        "Authenticator enrollment completed successfully."
    )

    return True


def verify_mfa_code(user, code):
    """Verify MFA and reject previously used authenticator codes."""

    prepare_mfa_table()

    user_id = user["user_id"]

    if check_mfa_lockout(user):
        return False

    with get_connection() as connection:

        settings = connection.execute("""
            SELECT secret_encrypted,
                   is_enabled,
                   last_verified_counter
            FROM mfa_settings
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        if settings is None or settings["is_enabled"] != 1:
            return False

        secret = decrypt_value(settings["secret_encrypted"])
        totp = pyotp.TOTP(secret)

        now = datetime.now(timezone.utc)
        current_counter = totp.timecode(now)

        matched_counter = None

        for counter in (
            current_counter - 1,
            current_counter,
            current_counter + 1
        ):

            if counter < 0:
                continue

            if counter <= settings["last_verified_counter"]:
                continue

            if totp.verify(
                code,
                for_time=counter * totp.interval
            ):
                matched_counter = counter
                break

        if matched_counter is None:
            record_failed_mfa_attempt(user)
            return False

        connection.execute("""
            UPDATE mfa_settings
            SET last_verified_counter = ?
            WHERE user_id = ?
        """, (matched_counter, user_id))

    reset_mfa_failed_attempts(user_id)

    record_audit(
        user_id,
        "MFA verification successful",
        "User",
        user_id,
        "Authenticator code verified."
    )

    return True


def is_mfa_enabled(user_id):
    """Check whether a staff member has enabled MFA."""

    prepare_mfa_table()

    with get_connection() as connection:

        settings = connection.execute("""
            SELECT is_enabled
            FROM mfa_settings
            WHERE user_id = ?
        """, (user_id,)).fetchone()

    return bool(settings and settings["is_enabled"] == 1)


def admin_reset_mfa(
    admin_user,
    target_username,
    reason,
    admin_password
):
    """Reset another user's MFA with atomic audit logging."""

    prepare_mfa_table()

    if admin_user.get("role") != "Admin":
        raise PermissionError(
            "Only an administrator can reset MFA."
        )

    if not target_username or not target_username.strip():
        raise ValueError(
            "A target username is required."
        )

    if not reason or not reason.strip():
        raise ValueError(
            "A reason for the reset is required."
        )

    with get_connection() as connection:

        administrator = connection.execute("""
            SELECT password_hash
            FROM users
            WHERE user_id = ?
              AND role = 'Admin'
              AND is_active = 1
        """, (admin_user["user_id"],)).fetchone()

        if administrator is None:
            raise PermissionError(
                "Administrator account is invalid or inactive."
            )

        if not verify_password(
            admin_password,
            administrator["password_hash"]
        ):
            raise PermissionError(
                "Administrator password verification failed."
            )

        target = connection.execute("""
            SELECT user_id, username
            FROM users
            WHERE username = ?
              AND is_active = 1
        """, (target_username.strip().lower(),)).fetchone()

        if target is None:
            raise ValueError(
                "Target account was not found or is inactive."
            )

        target_user_id = target["user_id"]

        if target_user_id == admin_user["user_id"]:
            raise PermissionError(
                "Administrators cannot reset their own MFA."
            )

        connection.execute("""
            DELETE FROM mfa_settings
            WHERE user_id = ?
        """, (target_user_id,))

        connection.execute("""
            DELETE FROM mfa_login_attempts
            WHERE user_id = ?
        """, (target_user_id,))

        # Record the audit event in the same transaction.
        timestamp = datetime.now(timezone.utc).isoformat()

        connection.execute("""
            INSERT INTO audit_logs (
                user_id,
                action,
                record_type,
                record_id,
                details,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            admin_user["user_id"],
            "MFA reset by administrator",
            "User",
            target_user_id,
            (
                f"Target username: {target['username']}; "
                f"Reason: {reason.strip()}"
            ),
            timestamp
        ))

    return True
