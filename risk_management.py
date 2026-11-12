from database import get_connection, record_audit
from access_control import require_permission


# Risk status options
ALLOWED_RISK_STATUSES = [
    "Open",
    "Under Review",
    "Mitigated",
    "Closed"
]


def calculate_risk_score(likelihood, impact):
    """Calculate risk score using likelihood multiplied by impact."""

    if not 1 <= likelihood <= 5:
        raise ValueError("Likelihood must be between 1 and 5.")

    if not 1 <= impact <= 5:
        raise ValueError("Impact must be between 1 and 5.")

    return likelihood * impact


def get_risk_level(score):
    """Determine the risk level from its score."""

    if score <= 4:
        return "Low"
    elif score <= 9:
        return "Medium"
    elif score <= 16:
        return "High"
    else:
        return "Critical"


def add_risk(user, risk_name, description,
             likelihood, impact, mitigation):
    """Register a new cybersecurity or data governance risk."""

    require_permission(user, "risk.manage")

    risk_name = risk_name.strip()
    description = description.strip()
    mitigation = mitigation.strip()

    if not risk_name or not description:
        raise ValueError("Risk name and description are required.")

    if not 1 <= likelihood <= 5:
        raise ValueError("Likelihood must be between 1 and 5.")

    if not 1 <= impact <= 5:
        raise ValueError("Impact must be between 1 and 5.")

    risk_score = calculate_risk_score(likelihood, impact)

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO risks (
                risk_name,
                description,
                likelihood,
                impact,
                risk_score,
                mitigation,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                risk_name,
                description,
                likelihood,
                impact,
                risk_score,
                mitigation,
                "Open"
            )
        )

        risk_id = cursor.lastrowid

        connection.commit()

        record_audit(
            user["user_id"],
            "CREATE",
            "Risk",
            risk_id,
            f"Registered risk: {risk_name}; "
            f"Score: {risk_score}"
        )

        print("\nRisk registered successfully.")
        print(f"Risk ID: {risk_id}")
        print(f"Risk score: {risk_score}")
        print(f"Risk level: {get_risk_level(risk_score)}")

    finally:
        connection.close()


def list_risks(user):
    """Display all registered risks."""

    require_permission(user, "risk.manage")

    connection = get_connection()

    try:
        risks = connection.execute(
            """
            SELECT *
            FROM risks
            ORDER BY risk_score DESC, risk_id DESC
            """
        ).fetchall()

        print("\nCYBERSECURITY RISK REGISTER")
        print("=" * 65)

        if not risks:
            print("No risks have been registered yet.")

        for risk in risks:
            print(f"\nRisk ID: {risk['risk_id']}")
            print(f"Risk name: {risk['risk_name']}")
            print(f"Description: {risk['description']}")
            print(f"Likelihood: {risk['likelihood']}/5")
            print(f"Impact: {risk['impact']}/5")
            print(f"Risk score: {risk['risk_score']}")
            print(
                f"Risk level: "
                f"{get_risk_level(risk['risk_score'])}"
            )
            print(f"Mitigation: {risk['mitigation']}")
            print(f"Status: {risk['status']}")
            print("-" * 65)

        record_audit(
            user["user_id"],
            "VIEW",
            "Risk",
            None,
            f"Viewed risk register containing {len(risks)} risks."
        )

    finally:
        connection.close()


def update_risk_status(user, risk_id, new_status):
    """Update the status of an existing risk."""

    require_permission(user, "risk.manage")

    new_status = new_status.strip().title()

    if new_status not in ALLOWED_RISK_STATUSES:
        raise ValueError(
            "Status must be Open, Under Review, "
            "Mitigated or Closed."
        )

    connection = get_connection()

    try:
        existing_risk = connection.execute(
            "SELECT risk_name FROM risks WHERE risk_id = ?",
            (risk_id,)
        ).fetchone()

        if existing_risk is None:
            raise ValueError("Risk ID was not found.")

        connection.execute(
            """
            UPDATE risks
            SET status = ?
            WHERE risk_id = ?
            """,
            (new_status, risk_id)
        )

        connection.commit()

        record_audit(
            user["user_id"],
            "UPDATE",
            "Risk",
            risk_id,
            f"Updated risk status to {new_status}."
        )

        print(
            f"\nRisk {risk_id} status updated to "
            f"{new_status}."
        )

    finally:
        connection.close()