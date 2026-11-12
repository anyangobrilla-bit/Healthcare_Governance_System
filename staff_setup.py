
from getpass import getpass
from auth import create_user

print("\nHEALTHCARE STAFF ACCOUNT SETUP")
print("=" * 40)

roles = ["Doctor", "Nurse", "Receptionist", "IT Officer"]

for role in roles:
    print(f"\nCREATE {role.upper()} ACCOUNT")

    full_name = input("Staff full name: ").strip()
    username = input("Choose username: ").strip()
    branch = input("Branch name: ").strip()

    password = getpass("Create password (minimum 10 characters): ")
    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        print("Passwords do not match. Account not created.")
        continue

    try:
        create_user(
            full_name,
            username,
            password,
            role,
            branch
        )
        print(f"{role} account created successfully.")

    except Exception as error:
        print(f"Could not create account: {error}")

print("\nSTAFF ACCOUNT SETUP COMPLETED.")
