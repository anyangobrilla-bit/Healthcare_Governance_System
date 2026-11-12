
from database import get_connection
from access_control import has_permission, require_permission

print("ADMIN PERMISSION TEST")
print("=" * 45)

# Retrieve the existing Admin account
with get_connection() as connection:
    row = connection.execute(
        """
        SELECT user_id, full_name, username, role, branch
        FROM users
        WHERE username = ?
        """,
        ("healthadmin",)
    ).fetchone()

if row is None:
    print("FAIL: Admin account not found.")
    raise SystemExit

user = dict(row)

print(f"Account: {user['username']}")
print(f"Role: {user['role']}")

# Permissions expected to be allowed
permissions = [
    "user.create",
    "user.view",
    "patient.view",
    "patient.create",
    "incident.manage",
    "risk.manage",
    "backup.manage",
    "audit.view",
    "system.manage",
    "compliance.manage"
]

print("\nAUTHORIZED PERMISSION TESTS")

failed = []

for permission in permissions:
    if has_permission(user, permission):
        print(f"PASS: {permission} is allowed.")
    else:
        print(f"FAIL: {permission} was denied.")
        failed.append(permission)

if failed:
    print("\nSome Admin permissions need further investigation.")
else:
    print("\nPASS: All tested Admin permissions are allowed.")

print("\nADMIN PERMISSION TEST COMPLETED.")
