
import getpass
from datetime import datetime, timedelta, timezone

from database import get_connection, record_audit
from security import hash_password, verify_password


VALID_ROLES = [
    "Admin",
    "Doctor",
    "Nurse",
    "Receptionist",
    "IT Officer"
]

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def prepare_login_attempts_table():
    """Create the login-attempt tracking table if it does not exist."""

    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                username TEXT PRIMARY KEY,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                updated_at TEXT NOT NULL
            )
        """)


def check_login_lockout(username, user_id=None):
    """Check whether a username is currently temporarily locked."""

    prepare_login_attempts_table()
    now = datetime.now(timezone.utc)

    with get_connection() as connection:
        attempt = connection.execute("""
            SELECT failed_attempts, locked_until
            FROM login_attempts
            WHERE username = ?
        """, (username,)).fetchone()

        if attempt is None or not attempt["locked_until"]:
            return False

        locked_until = datetime.fromisoformat(
            attempt["locked_until"]
        )

        if now < locked_until:
            record_audit(
                user_id,
                "Login blocked - temporary lockout",
                "User",
                user_id,
                f"Account temporarily locked until {attempt['locked_until']}."
            )
            return True

        # Remove the record after the lockout period expires.
        connection.execute(
            "DELETE FROM login_attempts WHERE username = ?",
            (username,)
        )

    return False


def record_failed_login(username, user_id=None):
    """Increase failed attempts and apply a temporary lockout."""

    prepare_login_attempts_table()

    now = datetime.now(timezone.utc)
    now_text = now.isoformat()

    with get_connection() as connection:
        attempt = connection.execute("""
            SELECT failed_attempts
            FROM login_attempts
            WHERE username = ?
        """, (username,)).fetchone()

        failed_attempts = (
            attempt["failed_attempts"] + 1
            if attempt else 1
        )

        locked_until = None

        if failed_attempts >= MAX_FAILED_ATTEMPTS:
            locked_until = (
                now + timedelta(minutes=LOCKOUT_MINUTES)
            ).isoformat()

        connection.execute("""
            INSERT INTO login_attempts (
                username,
                failed_attempts,
                locked_until,
                updated_at
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                failed_attempts = excluded.failed_attempts,
                locked_until = excluded.locked_until,
                updated_at = excluded.updated_at
        """, (
            username,
            failed_attempts,
            locked_until,
            now_text
        ))

    if locked_until:
        record_audit(
            user_id,
            "Account temporarily locked",
            "User",
            user_id,
            f"Failed login attempts: {failed_attempts}. "
            f"Locked until {locked_until}."
        )
    else:
        record_audit(
            user_id,
            "Failed login attempt",
            "User",
            user_id,
            (
                f"Unknown username: {username}"
                if user_id is None
                else "Incorrect password."
            )
        )

    return failed_attempts, locked_until


def create_user(full_name, username, password, role, branch):
    """Register a new staff member."""

    if role not in VALID_ROLES:
        raise ValueError("Invalid staff role.")

    if not full_name.strip() or not username.strip():
        raise ValueError("Name and username are required.")

    if not branch.strip():
        raise ValueError("Branch is required.")

    password_hash = hash_password(password)

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO users (
                full_name,
                username,
                password_hash,
                role,
                branch,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (
            full_name.strip(),
            username.strip().lower(),
            password_hash,
            role,
            branch.strip()
        ))

        user_id = cursor.lastrowid

    record_audit(
        user_id,
        "Staff account created",
        "User",
        user_id,
        f"Role: {role}; Branch: {branch.strip()}"
    )

    return user_id


def authenticate_user(username, password):
    """
    Verify staff credentials with temporary lockout protection.

    This function verifies the password only.
    MFA verification and the final successful-login audit
    are handled by main.py.
    """

    username = username.strip().lower()

    with get_connection() as connection:
        user = connection.execute("""
            SELECT
                user_id,
                full_name,
                username,
                password_hash,
                role,
                branch,
                is_active
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

    user_id = user["user_id"] if user else None

    if user is not None and user["is_active"] != 1:
        record_audit(
            user_id,
            "Blocked login attempt",
            "User",
            user_id,
            "Account is inactive."
        )
        return None

    if check_login_lockout(username, user_id):
        return None

    if user is None:
        record_failed_login(username)
        return None

    if not verify_password(password, user["password_hash"]):
        record_failed_login(username, user_id)
        return None

    # Password is correct: clear previous failed attempts.
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM login_attempts WHERE username = ?",
            (username,)
        )

    # Do not record a successful login until MFA is completed.
    record_audit(
        user_id,
        "Password verified",
        "User",
        user_id,
        f"Password authentication successful. "
        f"Role: {user['role']}. MFA verification pending."
    )

    return {
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "username": user["username"],
        "role": user["role"],
        "branch": user["branch"]
    }


def first_time_setup():
    """Create the first administrator account once."""

    with get_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

    if count > 0:
        print("An administrator or staff account already exists.")
        return

    print("\nFIRST-TIME ADMINISTRATOR SETUP")
    print("--------------------------------")

    full_name = input("Administrator's full name: ").strip()
    username = input("Choose an administrator username: ").strip()
    branch = input("Enter the branch name: ").strip()

    if not full_name or not username or not branch:
        print("All fields are required.")
        return

    while True:
        password = getpass.getpass(
            "Create a password (minimum 10 characters): "
        )

        confirm_password = getpass.getpass(
            "Confirm password: "
        )

        if password != confirm_password:
            print("Passwords do not match. Try again.")
            continue

        try:
            password_hash = hash_password(password)
            break
        except ValueError as error:
            print(error)

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO users (
                full_name,
                username,
                password_hash,
                role,
                branch,
                created_at
            )
            VALUES (?, ?, ?, 'Admin', ?, datetime('now'))
        """, (
            full_name,
            username.lower(),
            password_hash,
            branch
        ))

        user_id = cursor.lastrowid

    record_audit(
        user_id,
        "Initial administrator account created",
        "User",
        user_id,
        f"Branch: {branch}"
    )

    print("\nAdministrator account created successfully.")
