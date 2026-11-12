
from database import get_connection
from access_control import has_permission, require_permission

print("IT OFFICER PERMISSION TEST")
print("=" * 45)

# Retrieve the existing IT Officer account
with get_connection() as connection:
    row = connection.execute(
        """
        SELECT user_id, full_name, username, role, branch
        FROM users
        WHERE username = ?
        """,
        ("ittest",)
    ).fetchone()

if row is None:
    print("FAIL: IT Officer account not found.")
    raise SystemExit

user = dict(row)

print(f"Account: {user['username']}")
print(f"Role: {user['role']}")

# Test permissions that should be allowed
print("\n1. AUTHORIZED PERMISSIONS")

for permission in ["backup.manage", "audit.view", "system.manage"]:
    if has_permission(user, permission):
        print(f"PASS: {permission} is allowed.")
    else:
        print(f"FAIL: {permission} was denied.")

# Test permissions that should be denied
print("\n2. RESTRICTED PERMISSIONS")

for permission in ["risk.manage", "patient.view"]:
    try:
        require_permission(user, permission)
        print(f"FAIL: {permission} was allowed.")
    except PermissionError:
        print(f"PASS: {permission} was denied.")

print("\nIT OFFICER PERMISSION TEST COMPLETED.")
