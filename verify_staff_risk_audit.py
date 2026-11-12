
from database import get_connection


def verify_staff_risk_audit():
    print("STAFF RISK ACCESS DENIAL AUDIT CHECK")
    print("=" * 45)

    with get_connection() as connection:
        logs = connection.execute(
            """
            SELECT log_id, user_id, action, details, timestamp
            FROM audit_logs
            WHERE action = 'ACCESS_DENIED'
              AND details LIKE '%risk.manage%'
            ORDER BY log_id DESC
            LIMIT 10
            """
        ).fetchall()

    if not logs:
        print("\nNo risk access denial records found.")
        return

    for log in logs:
        print(f"\nLog ID: {log['log_id']}")
        print(f"User ID: {log['user_id']}")
        print(f"Action: {log['action']}")
        print(f"Details: {log['details']}")
        print(f"Timestamp: {log['timestamp']}")
        print("-" * 45)

    print("\nPASS: Risk access denial records retrieved.")


if __name__ == "__main__":
    verify_staff_risk_audit()
