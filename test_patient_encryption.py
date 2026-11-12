
from uuid import uuid4

from database import get_connection
from patient_records import create_patient, list_patients


doctor = {
    "user_id": 2,
    "role": "Doctor",
    "branch": "Nairobi Main Branch"
}

patient_number = "ENC-TEST-" + uuid4().hex[:10]

try:
    # Register fictional patient information.
    patient_id = create_patient(
        doctor,
        patient_number,
        "Fictional Encryption Patient",
        "1995-05-15",
        "Test",
        "0700000000",
        "Fictional medical history for encryption testing"
    )

    # Inspect what is actually stored in SQLite.
    with get_connection() as connection:
        stored = connection.execute("""
            SELECT full_name, date_of_birth, gender,
                   phone_number, medical_history
            FROM patients
            WHERE patient_id = ?
        """, (patient_id,)).fetchone()

    fields = [
        "full_name",
        "date_of_birth",
        "gender",
        "phone_number",
        "medical_history"
    ]

    for field in fields:
        assert stored[field].startswith("fernet:v1:"), (
            f"FAIL: {field} was not encrypted."
        )

    print("PASS: All five sensitive fields are encrypted in SQLite.")

    # Confirm the authorized Doctor can retrieve readable information.
    patients = list_patients(doctor)

    patient = next(
        item for item in patients
        if item["patient_id"] == patient_id
    )

    assert patient["full_name"] == "Fictional Encryption Patient"
    assert patient["medical_history"] == (
        "Fictional medical history for encryption testing"
    )

    print("PASS: Authorized Doctor retrieved decrypted information.")

finally:
    # Remove the fictional test patient, not existing records.
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM patients WHERE patient_number = ?",
            (patient_number,)
        )

    print("Test patient cleanup completed.")
