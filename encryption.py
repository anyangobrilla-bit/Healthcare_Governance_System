
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


# Store the encryption key outside the project and database backups.
KEY_DIRECTORY = (
    Path.home()
    / "AppData"
    / "Local"
    / "Healthcare_Governance_System"
)

KEY_FILE = KEY_DIRECTORY / "fernet.key"

ENCRYPTION_PREFIX = "fernet:v1:"


def generate_key():
    """Generate a key once without overwriting an existing key."""

    KEY_DIRECTORY.mkdir(parents=True, exist_ok=True)

    if KEY_FILE.exists():
        raise FileExistsError(
            "An encryption key already exists. "
            "It will not be overwritten."
        )

    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)

    print("Encryption key created successfully.")
    print("Key location:", KEY_FILE)


def load_key():
    """Load the existing encryption key."""

    if not KEY_FILE.exists():
        raise FileNotFoundError(
            "Encryption key not found. "
            "Generate the key before encrypting data."
        )

    return KEY_FILE.read_bytes()


def get_fernet():
    """Create a Fernet encryption object."""

    return Fernet(load_key())


def encrypt_value(value):
    """Encrypt a text value while avoiding double encryption."""

    if value is None or value == "":
        return value

    if not isinstance(value, str):
        raise TypeError("Only text values can be encrypted.")

    if value.startswith(ENCRYPTION_PREFIX):
        return value

    encrypted = get_fernet().encrypt(
        value.encode("utf-8")
    ).decode("utf-8")

    return ENCRYPTION_PREFIX + encrypted


def decrypt_value(value):
    """Decrypt a value previously encrypted by this module."""

    if value is None or value == "":
        return value

    if not isinstance(value, str):
        raise TypeError("Only text values can be decrypted.")

    # Leave existing plaintext values unchanged during migration.
    if not value.startswith(ENCRYPTION_PREFIX):
        return value

    token = value[len(ENCRYPTION_PREFIX):]

    try:
        decrypted = get_fernet().decrypt(
            token.encode("utf-8")
        )

        return decrypted.decode("utf-8")

    except InvalidToken as error:
        raise ValueError(
            "Decryption failed. The key or encrypted data "
            "may be incorrect or damaged."
        ) from error


if __name__ == "__main__":

    print("HEALTHCARE DATA ENCRYPTION TEST")
    print("--------------------------------")

    if not KEY_FILE.exists():
        generate_key()
    else:
        print("Existing encryption key found.")

    test_value = "Fictional patient medical history"

    encrypted_value = encrypt_value(test_value)
    decrypted_value = decrypt_value(encrypted_value)

    print("Original value:", test_value)
    print("Encrypted value is different:",
          encrypted_value != test_value)
    print("Decryption successful:",
          decrypted_value == test_value)
    print("Encryption key remains outside the project.")
