
from database import get_connection, record_audit, initialize_database
from access_control import require_permission
from encryption import encrypt_value, decrypt_value


# Fields encrypted before storage and decrypted after authorization.
ENCRYPTED_FIELDS = [
    "full_name",
    "date_of_birth",
    "gender",
    "phone_number",
    "medical_history",
    "care_notes"
]


def prepare_patient_table():
    """Prepare patient records with branch and care-note fields."""

    with get_connection() as connection:
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(patients)"
            ).fetchall()
        }

        migrations = {
            "branch": """
                ALTER TABLE patients
                ADD COLUMN branch TEXT NOT NULL
                DEFAULT 'Nairobi Main Branch'
            """,
            "care_notes": """
                ALTER TABLE patients
                ADD COLUMN care_notes TEXT
            """
        }

        for column, sql in migrations.items():
            if column not in columns:
                connection.execute(sql)


def decrypt_patient_fields(patient):
    """Decrypt only the fields present in an authorized result."""

    patient_data = dict(patient)

    for field in ENCRYPTED_FIELDS:
        if field in patient_data:
            patient_data[field] = decrypt_value(
                patient_data[field]
            )

    return patient_data


def create_patient(
    user,
    patient_number,
    full_name,
    date_of_birth,
    gender,
    phone_number,
    medical_history
):
    """Register a patient with encrypted sensitive information."""

    require_permission(user, "patient.create")

    if not patient_number or not patient_number.strip():
        raise ValueError("Patient number is required.")

    if not full_name or not full_name.strip():
        raise ValueError("Patient name is required.")

    encrypted_name = encrypt_value(full_name.strip())
    encrypted_dob = encrypt_value(date_of_birth)
    encrypted_gender = encrypt_value(gender)
    encrypted_phone = encrypt_value(phone_number)
    encrypted_history = encrypt_value(medical_history)

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO patients (
                patient_number,
                full_name,
                date_of_birth,
                gender,
                phone_number,
                medical_history,
                classification,
                created_by,
                created_at,
                branch
            )
            VALUES (?, ?, ?, ?, ?, ?, 'CONFIDENTIAL', ?, datetime('now'), ?)
        """, (
            patient_number.strip(),
            encrypted_name,
            encrypted_dob,
            encrypted_gender,
            encrypted_phone,
            encrypted_history,
            user["user_id"],
            user["branch"]
        ))

        patient_id = cursor.lastrowid

    record_audit(
        user["user_id"],
        "Patient registered",
        "Patient",
        patient_id,
        f"Patient registered at {user['branch']}"
    )

    return patient_id


def list_patients(user):
    """Return decrypted patient information permitted for each role."""

    role = user["role"]

    permissions = {
        "Admin": "patient.view",
        "Doctor": "patient.view",
        "Nurse": "patient.view",
        "Receptionist": "patient.view_basic"
    }

    permission = permissions.get(role)

    if permission is None:
        raise PermissionError(
            "Your role is not permitted to view patient records."
        )

    require_permission(user, permission)

    with get_connection() as connection:

        if role == "Admin":
            rows = connection.execute("""
                SELECT patient_id, patient_number, full_name,
                       date_of_birth, gender, phone_number,
                       medical_history, care_notes, branch
                FROM patients
                ORDER BY patient_id DESC
            """).fetchall()

        elif role == "Doctor":
            rows = connection.execute("""
                SELECT patient_id, patient_number, full_name,
                       date_of_birth, gender, phone_number,
                       medical_history, care_notes, branch
                FROM patients
                WHERE branch = ?
                ORDER BY patient_id DESC
            """, (user["branch"],)).fetchall()

        elif role == "Nurse":
            rows = connection.execute("""
                SELECT patient_id, patient_number, full_name,
                       date_of_birth, gender, phone_number,
                       care_notes, branch
                FROM patients
                WHERE branch = ?
                ORDER BY patient_id DESC
            """, (user["branch"],)).fetchall()

        else:
            rows = connection.execute("""
                SELECT patient_id, patient_number,
                       full_name, phone_number, branch
                FROM patients
                WHERE branch = ?
                ORDER BY patient_id DESC
            """, (user["branch"],)).fetchall()

    # Decrypt only after the role-specific query has limited the fields.
    patients = [
        decrypt_patient_fields(row)
        for row in rows
    ]

    record_audit(
        user["user_id"],
        "Viewed patient list",
        "Patient",
        None,
        f"Role: {role}; Records viewed: {len(patients)}"
    )

    return patients


def update_clinical_record(user, patient_id, medical_history):
    """Allow authorized staff to update encrypted clinical information."""

    require_permission(user, "patient.update_clinical")

    encrypted_history = encrypt_value(medical_history)

    with get_connection() as connection:

        patient = connection.execute("""
            SELECT patient_id, branch
            FROM patients
            WHERE patient_id = ?
        """, (patient_id,)).fetchone()

        if patient is None:
            raise ValueError("Patient record not found.")

        if (
            user["role"] != "Admin"
            and patient["branch"] != user["branch"]
        ):
            raise PermissionError(
                "Access denied: Patient belongs to another branch."
            )

        connection.execute("""
            UPDATE patients
            SET medical_history = ?
            WHERE patient_id = ?
        """, (encrypted_history, patient_id))

    record_audit(
        user["user_id"],
        "Updated clinical record",
        "Patient",
        patient_id,
        "Medical history updated."
    )


def update_care_notes(user, patient_id, care_notes):
    """Allow authorized staff to update encrypted patient care notes."""

    require_permission(user, "patient.update_care")

    encrypted_notes = encrypt_value(care_notes)

    with get_connection() as connection:

        patient = connection.execute("""
            SELECT patient_id, branch
            FROM patients
            WHERE patient_id = ?
        """, (patient_id,)).fetchone()

        if patient is None:
            raise ValueError("Patient record not found.")

        if (
            user["role"] != "Admin"
            and patient["branch"] != user["branch"]
        ):
            raise PermissionError(
                "Access denied: Patient belongs to another branch."
            )

        connection.execute("""
            UPDATE patients
            SET care_notes = ?
            WHERE patient_id = ?
        """, (encrypted_notes, patient_id))

    record_audit(
        user["user_id"],
        "Updated patient care notes",
        "Patient",
        patient_id,
        "Care notes updated."
    )


if __name__ == "__main__":

    initialize_database()
    prepare_patient_table()

    print("PATIENT RECORD MANAGEMENT")
    print("-------------------------")
    print("Patient table prepared successfully.")

    with get_connection() as connection:
        columns = connection.execute(
            "PRAGMA table_info(patients)"
        ).fetchall()

    print("\nAvailable patient database fields:")

    for column in columns:
        print("-", column["name"])

    print("\nPatient records module initialized successfully.")
