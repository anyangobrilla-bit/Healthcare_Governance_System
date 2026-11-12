
import secrets

from database import get_connection
from security import hash_password, verify_password


print("PASSWORD HASHING SECURITY TEST")
print("=" * 45)

username = f"password_test_{secrets.token_hex(6)}"
test_password = secrets.token_urlsafe(16)

try:
    # Generate a password hash.
    stored_hash = hash_password(test_password)

    if stored_hash != test_password:
        print("PASS: Password is not stored as readable text.")
    else:
        print("FAIL: Password appears to be stored as plain text.")

    # Confirm that the correct password matches the hash.
    if verify_password(test_password, stored_hash):
        print("PASS: Correct password matches the stored hash.")
    else:
        print("FAIL: Correct password did not match the stored hash.")

    # Confirm that an incorrect password is rejected.
    if not verify_password("WrongPassword123!", stored_hash):
        print("PASS: Incorrect password does not match the stored hash.")
    else:
        print("FAIL: Incorrect password was accepted.")

    # Confirm that separate hashes use different random salts.
    second_hash = hash_password(test_password)

    if stored_hash != second_hash:
        print("PASS: Separate password hashes use different salts.")
    else:
        print("FAIL: Password hashes unexpectedly matched.")

finally:
    print("\nPASSWORD HASHING TEST COMPLETED.")
    print("No real staff accounts or patient records were modified.")
