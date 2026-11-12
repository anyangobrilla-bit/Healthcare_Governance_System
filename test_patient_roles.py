
from patient_records import list_patients

nurse = {
    "user_id": 3,
    "role": "Nurse",
    "branch": "Nairobi Main Branch"
}

doctor = {
    "user_id": 2,
    "role": "Doctor",
    "branch": "Nairobi Main Branch"
}


# TEST 1: Nurse access
print("=" * 55)
print("TEST 1: NURSE PATIENT ACCESS")
print("=" * 55)

nurse_records = list_patients(nurse)

for patient in nurse_records:
    data = dict(patient)

    print("\nNurse-visible information:")
    print(data)

    assert "care_notes" in data
    assert "medical_history" not in data

print("\nPASS: Nurse can access care notes but not medical history.")


# TEST 2: Doctor access
print("\n" + "=" * 55)
print("TEST 2: DOCTOR PATIENT ACCESS")
print("=" * 55)

doctor_records = list_patients(doctor)

for patient in doctor_records:
    data = dict(patient)

    print("\nDoctor-visible information:")
    print(data)

    assert "medical_history" in data
    assert "care_notes" in data

print("\nPASS: Doctor can access medical history and care notes.")

print("\n" + "=" * 55)
print("NURSE AND DOCTOR ACCESS TESTING COMPLETED")
print("=" * 55)
