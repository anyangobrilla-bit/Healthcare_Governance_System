from database import get_connection
from risk_management import list_risks

print("NURSE AND RECEPTIONIST RISK PERMISSION TEST")
print("--------------------------------------------")

test_accounts = ["nursetest", "receptiontest"]

for username in test_accounts:

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT user_id, full_name, username, role, branch
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

    if row is None:
        print(f"FAIL: {username} account not found.")
        continue

    user = dict(row)

    print(f"\nTesting role: {user['role']}")

    try:
        list_risks(user)
        print("FAIL: Access to the risk register was allowed.")

    except PermissionError:
        print("PASS: Access to the risk register was denied.")

print("\nSTAFF RISK PERMISSION TEST COMPLETED.")