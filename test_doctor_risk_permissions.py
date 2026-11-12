from database import get_connection
from risk_management import (
    list_risks,
    add_risk,
    update_risk_status
)

print("DOCTOR RISK MANAGEMENT PERMISSION TEST")
print("---------------------------------------")

# Retrieve the existing Doctor account
with get_connection() as connection:
    row = connection.execute(
        """
        SELECT user_id, full_name, username, role, branch
        FROM users
        WHERE username = ?
        """,
        ("doctor_test",)
    ).fetchone()

if row is None:
    print("FAIL: Doctor account not found.")
    raise SystemExit

user = dict(row)

if user["role"] != "Doctor":
    print("FAIL: Account is not a Doctor.")
    raise SystemExit

print("Doctor account loaded successfully.")

# Test viewing risks
try:
    list_risks(user)
    print("FAIL: Doctor was allowed to view risks.")
except PermissionError:
    print("PASS: Doctor cannot view the risk register.")

# Test registering a risk
try:
    add_risk(
        user,
        "Unauthorized test risk",
        "Fictional permission test.",
        2,
        2,
        "Test mitigation."
    )
    print("FAIL: Doctor was allowed to register risks.")
except PermissionError:
    print("PASS: Doctor cannot register risks.")

# Test updating a risk
try:
    update_risk_status(user, 2, "Closed")
    print("FAIL: Doctor was allowed to update risk status.")
except PermissionError:
    print("PASS: Doctor cannot update risk status.")

print("---------------------------------------")
print("DOCTOR RISK PERMISSION TEST COMPLETED")