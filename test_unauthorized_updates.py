
from patient_records import (
    update_clinical_record,
    update_care_notes
)


# Simulated staff accounts
doctor = {
    "user_id": 2,
    "role": "Doctor",
    "branch": "Nairobi Main Branch"
}

receptionist = {
    "user_id": 4,
    "role": "Receptionist",
    "branch": "Nairobi Main Branch"
}


def test_unauthorized_update(description, function, user):
    print(f"\nTesting: {description}")

    try:
        function(
            user,
            1,
            "UNAUTHORIZED UPDATE TEST"
        )

        print("FAIL: Unauthorized update was allowed.")

    except PermissionError as error:
        print("PASS: Unauthorized update was denied.")
        print("Reason:", error)


print("=" * 60)
print("UNAUTHORIZED PATIENT RECORD UPDATE TESTS")
print("=" * 60)


# TEST 1: Doctor must not update nursing care notes.
test_unauthorized_update(
    "Doctor attempting to update care notes",
    update_care_notes,
    doctor
)


# TEST 2: Receptionist must not update clinical records.
test_unauthorized_update(
    "Receptionist attempting to update clinical records",
    update_clinical_record,
    receptionist
)


# TEST 3: Receptionist must not update care notes.
test_unauthorized_update(
    "Receptionist attempting to update care notes",
    update_care_notes,
    receptionist
)


print("\n" + "=" * 60)
print("UNAUTHORIZED UPDATE TESTING COMPLETED")
print("=" * 60)
