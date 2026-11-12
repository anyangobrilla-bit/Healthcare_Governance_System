
from datetime import datetime, timezone

from database import get_connection, record_audit
from access_control import require_permission


ALLOWED_SEVERITIES = ["Low", "Medium", "High", "Critical"]
ALLOWED_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]


def report_incident(user, title, description, severity):
    """Record a new security incident."""

    require_permission(user, "incident.manage")

    if not title.strip():
        raise ValueError("Incident title cannot be empty.")

    if not description.strip():
        raise ValueError("Incident description cannot be empty.")

    if severity not in ALLOWED_SEVERITIES:
        raise ValueError(
            "Severity must be Low, Medium, High, or Critical."
        )

    reported_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO incidents
            (title, description, severity, status, reported_by, reported_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title.strip(),
                description.strip(),
                severity,
                "Open",
                user["user_id"],
                reported_at
            )
        )

        incident_id = cursor.lastrowid

    record_audit(
        user["user_id"],
        "INCIDENT_REPORTED",
        "incident",
        incident_id,
        f"Severity: {severity}; Title: {title.strip()}"
    )

    print("\nSecurity incident reported successfully.")
    print(f"Incident ID: {incident_id}")


def list_incidents(user):
    """Display all recorded security incidents."""

    require_permission(user, "incident.manage")

    with get_connection() as connection:
        incidents = connection.execute(
            """
            SELECT incident_id, title, description, severity,
                   status, reported_by, reported_at
            FROM incidents
            ORDER BY reported_at DESC
            """
        ).fetchall()

    if not incidents:
        print("\nNo security incidents have been recorded.")
        return

    print("\nSECURITY INCIDENT REGISTER")
    print("=" * 60)

    for incident in incidents:
        print(f"\nIncident ID: {incident['incident_id']}")
        print(f"Title: {incident['title']}")
        print(f"Description: {incident['description']}")
        print(f"Severity: {incident['severity']}")
        print(f"Status: {incident['status']}")
        print(f"Reported by user ID: {incident['reported_by']}")
        print(f"Reported at: {incident['reported_at']}")
        print("-" * 60)

    record_audit(
        user["user_id"],
        "INCIDENTS_VIEWED",
        "incident",
        None,
        f"Viewed {len(incidents)} incident record(s)."
    )


def update_incident_status(user, incident_id, new_status):
    """Update the status of an existing security incident."""

    require_permission(user, "incident.manage")

    if new_status not in ALLOWED_STATUSES:
        raise ValueError(
            "Status must be Open, In Progress, Resolved, or Closed."
        )

    with get_connection() as connection:
        incident = connection.execute(
            "SELECT incident_id FROM incidents WHERE incident_id = ?",
            (incident_id,)
        ).fetchone()

        if incident is None:
            raise ValueError("The specified incident does not exist.")

        connection.execute(
            """
            UPDATE incidents
            SET status = ?
            WHERE incident_id = ?
            """,
            (new_status, incident_id)
        )

    record_audit(
        user["user_id"],
        "INCIDENT_STATUS_UPDATED",
        "incident",
        incident_id,
        f"New status: {new_status}"
    )

    print(f"\nIncident {incident_id} status updated to {new_status}.")
