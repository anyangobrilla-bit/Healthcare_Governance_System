
from patient_records import update_clinical_record, list_patients


# Test user accounts
nurse = {
    "user_id": 3,
    "role": "Nurse",
    "branch": "Nairobi Main Branch"
}

receptionist = {
    "user_id": 4,
    "role": "Receptionist",
    "branch": "Nairobi Main Branch"
}


# TEST 1: Nurse must not update clinical records.
print("=" * 55)
print("TEST 1: NURSE CLINICAL RECORD ACCESS")
print("=" * 55)

try:
    update_clinical_record(
        nurse,
        1,
        "UNAUTHORIZED PRIVACY TEST"
    )

    print("FAIL: Nurse was allowed to update clinical records.")

except PermissionError as error:
    print("PASS: Nurse clinical-record access denied.")
    print("Reason:", error)


# TEST 2: Receptionist must only see basic patient information.
print("\n" + "=" * 55)
print("TEST 2: RECEPTIONIST PATIENT ACCESS")
print("=" * 55)

try:
    records = list_patients(receptionist)

    if not records:
        print("No patient records found for this branch.")

    for patient in records:
        patient_data = dict(patient)

        print("\nPatient information:")
        for field, value in patient_data.items():
            print(f"{field}: {value}")

        # Check that confidential fields are excluded.
        assert "medical_history" not in patient_data
        assert "care_notes" not in patient_data

    print("\nPASS: Receptionist can only access permitted basic details.")

except PermissionError as error:
    print("FAIL: Receptionist access was denied.")
    print("Reason:", error)

except AssertionError:
    print("FAIL: Confidential patient information was exposed.")

print("\n" + "=" * 55)
print("PATIENT PRIVACY TESTING COMPLETED")
print("=" * 55)
