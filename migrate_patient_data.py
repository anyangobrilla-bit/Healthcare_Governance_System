
import sqlite3
from datetime import datetime, timezone

from database import DATABASE_PATH
from encryption import (
    KEY_FILE,
    encrypt_value,
    decrypt_value,
    ENCRYPTION_PREFIX
)

BACKUP_PATH = (
    DATABASE_PATH.parent
    / "backups"
    / "healthcare_backup_20261110_104358.db"
)

FIELDS = [
    "full_name",
    "date_of_birth",
    "gender",
    "phone_number",
    "medical_history",
    "care_notes"
]


def verify_backup():
    if not BACKUP_PATH.exists():
        raise FileNotFoundError(
            "Verified backup was not found."
        )

    connection = sqlite3.connect(BACKUP_PATH)

    try:
        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integrity != "ok":
            raise RuntimeError(
                "Backup integrity check failed."
            )

        count = connection.execute(
            "SELECT COUNT(*) FROM patients"
        ).fetchone()[0]

        print("Backup integrity:", integrity)
        print("Backup patient records:", count)

        return count

    finally:
        connection.close()


def migrate():
    if not KEY_FILE.exists():
        raise FileNotFoundError(
            "Encryption key was not found."
        )

    backup_count = verify_backup()

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        live_count = connection.execute(
            "SELECT COUNT(*) FROM patients"
        ).fetchone()[0]

        if live_count != backup_count:
            raise RuntimeError(
                "Live database and backup patient counts differ."
            )

        connection.execute("BEGIN IMMEDIATE")

        patients = connection.execute(
            "SELECT patient_id, " + ", ".join(FIELDS)
            + " FROM patients"
        ).fetchall()

        migrated_fields = 0

        for patient in patients:
            updates = {}
            original_values = {}

            for field in FIELDS:
                value = patient[field]

                if value is None or value == "":
                    continue

                encrypted = encrypt_value(value)

                if encrypted != value:
                    migrated_fields += 1

                updates[field] = encrypted
                original_values[field] = value

            if updates:
                assignments = ", ".join(
                    field + " = ?" for field in updates
                )

                values = list(updates.values())
                values.append(patient["patient_id"])

                connection.execute(
                    "UPDATE patients SET "
                    + assignments
                    + " WHERE patient_id = ?",
                    values
                )

            for field, original in original_values.items():
                recovered = decrypt_value(updates[field])

                if recovered != original:
                    raise RuntimeError(
                        "Decryption verification failed for "
                        + field
                    )

        # Verify every non-empty field.
        for patient in connection.execute(
            "SELECT " + ", ".join(FIELDS)
            + " FROM patients"
        ).fetchall():

            for field in FIELDS:
                value = patient[field]

                if value is None or value == "":
                    continue

                if not value.startswith(ENCRYPTION_PREFIX):
                    raise RuntimeError(
                        "Plaintext value remains in " + field
                    )

                decrypt_value(value)

        admin = connection.execute(
            """
            SELECT user_id
            FROM users
            WHERE role = 'Admin' AND is_active = 1
            ORDER BY user_id
            LIMIT 1
            """
        ).fetchone()

        if admin is None:
            raise RuntimeError(
                "No active Admin account was found."
            )

        connection.execute(
            """
            INSERT INTO audit_logs (
                user_id, action, record_type, record_id,
                details, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                admin["user_id"],
                "Patient data encryption migration",
                "Patient",
                None,
                "Encrypted "
                + str(migrated_fields)
                + " existing patient fields.",
                datetime.now(timezone.utc).isoformat()
            )
        )

        connection.commit()

        print("\nMIGRATION SUCCESSFUL")
        print("-------------------------")
        print("Patient records processed:", len(patients))
        print("Fields encrypted:", migrated_fields)
        print("Decryption verification: Passed")
        print("Audit log: Recorded")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    print("HEALTHCARE PATIENT DATA ENCRYPTION MIGRATION")
    print("--------------------------------------------")

    migrate()
