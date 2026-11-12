
import sqlite3

from encryption import (
    ENCRYPTION_PREFIX,
    decrypt_value
)

connection = sqlite3.connect("healthcare.db")

fields = [
    "full_name",
    "date_of_birth",
    "gender",
    "phone_number",
    "medical_history",
    "care_notes"
]

query = (
    "SELECT "
    + ", ".join(fields)
    + " FROM patients"
)

rows = connection.execute(query).fetchall()

encrypted = 0
plaintext = 0
verified = 0

for row in rows:
    for value in row:

        if value is None or value == "":
            continue

        if value.startswith(ENCRYPTION_PREFIX):
            encrypted += 1

            # Confirm that the encrypted value can be decrypted.
            decrypt_value(value)
            verified += 1

        else:
            plaintext += 1

connection.close()

print("PATIENT ENCRYPTION VERIFICATION")
print("--------------------------------")
print("Patient records:", len(rows))
print("Encrypted fields:", encrypted)
print("Plaintext fields remaining:", plaintext)
print("Successfully decrypted:", verified)

if plaintext == 0 and encrypted == verified:
    print("\nPASS: All populated patient fields are encrypted.")
else:
    print("\nWARNING: Further investigation is required.")
