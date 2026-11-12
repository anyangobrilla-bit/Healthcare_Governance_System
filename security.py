
import hashlib
import hmac
import secrets


# Password hashing configuration
ITERATIONS = 600_000
SALT_SIZE = 16
MIN_PASSWORD_LENGTH = 10


def hash_password(password):
    """Securely hash a password before database storage."""

    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must contain at least {MIN_PASSWORD_LENGTH} characters."
        )

    salt = secrets.token_bytes(SALT_SIZE)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS
    )

    # Store the algorithm, iterations, salt and hash together.
    return (
        f"pbkdf2_sha256${ITERATIONS}$"
        f"{salt.hex()}${password_hash.hex()}"
    )


def verify_password(password, stored_hash):
    """Verify a password against its stored hash."""

    if not isinstance(password, str):
        return False

    if not isinstance(stored_hash, str):
        return False

    try:
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        iteration_count = int(iterations)

        if iteration_count <= 0:
            return False

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        if len(salt) != SALT_SIZE or len(expected_hash) != 32:
            return False

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iteration_count
        )

        return hmac.compare_digest(
            calculated_hash,
            expected_hash
        )

    except (ValueError, TypeError, AttributeError):
        return False


if __name__ == "__main__":
    # Generate a random temporary password for testing.
    test_password = secrets.token_urlsafe(16)

    saved_hash = hash_password(test_password)

    print("PASSWORD SECURITY TEST")
    print("----------------------")
    print("Password hashed successfully.")

    print(
        "Correct password:",
        verify_password(test_password, saved_hash)
    )

    print(
        "Incorrect password:",
        verify_password("WrongPassword123", saved_hash)
    )
