from database import get_connection
from access_control import require_permission


def view_audit_logs(user):
    """Allow authorized staff to review system activity."""

    require_permission(user, "audit.view")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                log_id,
                user_id,
                action,
                record_type,
                record_id,
                details,
                timestamp
            FROM audit_logs
            ORDER BY timestamp DESC
            LIMIT 50
        """)

        logs = cursor.fetchall()

    finally:
        connection.close()

    print("\nSYSTEM AUDIT LOGS")
    print("=" * 70)

    if not logs:
        print("No audit activities have been recorded.")
        return

    for log in logs:
        print(f"Log ID: {log['log_id']}")
        print(f"User ID: {log['user_id']}")
        print(f"Action: {log['action']}")
        print(f"Record Type: {log['record_type']}")
        print(f"Record ID: {log['record_id']}")
        print(f"Details: {log['details']}")
        print(f"Timestamp: {log['timestamp']}")
        print("-" * 70)