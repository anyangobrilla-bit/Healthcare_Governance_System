
import secrets

from database import get_connection
from security import hash_password
from auth import authenticate_user


print("INACTIVE ACCOUNT SECURITY TEST")
print("=" * 45)

# Generate unique temporary test credentials.
username = f"inactive_test_{secrets.token_hex(6)}"
test_password = secrets.token_urlsafe(16)

try:
    # Create a dedicated inactive test account.
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO users (
                full_name,
                username,
                password_hash,
                role,
                branch,
                is_active,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, 0, datetime('now'))
            """,
            (
                "Inactive Security Test",
                username,
                hash_password(test_password),
                "Doctor",
                "Test Branch"
            )
        )

    print("PASS: Temporary inactive test account created.")

    # Attempt login using the correct test password.
    user = authenticate_user(username, test_password)

    if user is None:
        print("PASS: Inactive account login was rejected.")
    else:
        print("FAIL: Inactive account was allowed to log in.")

finally:
    # Deactivate the temporary account without deleting audit history.
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET is_active = 0
            WHERE username = ?
            """,
            (username,)
        )

    print("\nTemporary test account deactivated.")
    print("Existing audit history preserved.")

print("\nINACTIVE ACCOUNT TEST COMPLETED.")
