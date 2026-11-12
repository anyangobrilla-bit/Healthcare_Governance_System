
from auth import authenticate_user

print("AUTHENTICATION SECURITY TEST")
print("=" * 45)

# Test an existing account with an incorrect password.
username = "healthadmin"
incorrect_password = "DefinitelyWrongPassword123!"

user = authenticate_user(username, incorrect_password)

if user is None:
    print("PASS: Incorrect password was rejected.")
else:
    print("FAIL: Incorrect password was accepted.")

print("\nAUTHENTICATION TEST COMPLETED.")
