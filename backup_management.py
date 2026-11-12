
import sqlite3
from pathlib import Path
from datetime import datetime

from access_control import require_permission
from database import record_audit
from encryption import get_fernet


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "healthcare.db"
BACKUP_DIR = BASE_DIR / "backups"
RESTORE_DIR = BACKUP_DIR / "restored_copies"

REQUIRED_TABLES = {
    "users",
    "patients",
    "audit_logs",
    "incidents",
    "risks"
}


def verify_database_file(database_path):
    """Verify SQLite integrity and required healthcare tables."""

    database_uri = database_path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)

    try:
        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()

        if not integrity or integrity[0] != "ok":
            raise sqlite3.DatabaseError(
                "Database integrity check failed."
            )

        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = ?",
                ("table",)
            ).fetchall()
        }

        if not REQUIRED_TABLES.issubset(tables):
            raise sqlite3.DatabaseError(
                "Database is missing required healthcare tables."
            )

    finally:
        connection.close()


def create_database_backup(user):
    """Create and verify an encrypted SQLite database backup."""

    require_permission(user, "backup.manage")

    if not DATABASE_PATH.is_file():
        print("\nERROR: Healthcare database was not found.")
        return

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_filename = f"healthcare_backup_{timestamp}.db.enc"
    backup_path = BACKUP_DIR / backup_filename

    plaintext_temp_path = BACKUP_DIR / (
        f".healthcare_backup_{timestamp}.plaintext.tmp.db"
    )

    encrypted_temp_path = BACKUP_DIR / (
        f".healthcare_backup_{timestamp}.encrypted.tmp"
    )

    if any(
        path.exists()
        for path in (
            backup_path,
            plaintext_temp_path,
            encrypted_temp_path
        )
    ):
        print("\nBACKUP FAILED: A file with this timestamp already exists.")
        return

    source_connection = None
    backup_connection = None
    backup_published = False

    try:
        # Create a consistent SQLite backup.
        source_connection = sqlite3.connect(DATABASE_PATH)
        backup_connection = sqlite3.connect(plaintext_temp_path)

        source_connection.backup(backup_connection)

        backup_connection.close()
        backup_connection = None

        source_connection.close()
        source_connection = None

        # Verify the temporary SQLite database.
        verify_database_file(plaintext_temp_path)

        # Read and encrypt the complete database.
        plaintext_bytes = plaintext_temp_path.read_bytes()
        fernet = get_fernet()

        encrypted_bytes = fernet.encrypt(plaintext_bytes)

        # Verify that encryption and decryption work correctly.
        if fernet.decrypt(encrypted_bytes) != plaintext_bytes:
            raise ValueError("Encryption verification failed.")

        # Save the encrypted backup without overwriting files.
        with encrypted_temp_path.open("xb") as encrypted_file:
            encrypted_file.write(encrypted_bytes)
            encrypted_file.flush()

        # Verify the actual saved encrypted file.
        saved_encrypted_bytes = encrypted_temp_path.read_bytes()

        if fernet.decrypt(saved_encrypted_bytes) != plaintext_bytes:
            raise ValueError("Saved backup verification failed.")

        # Publish the completed encrypted backup.
        encrypted_temp_path.rename(backup_path)
        backup_published = True

        print("\nENCRYPTED DATABASE BACKUP CREATED")
        print("-" * 45)
        print("Backup file:", backup_filename)
        print("SQLite integrity: Passed")
        print("Encryption verification: Passed")
        print("Saved backup verification: Passed")

        # Remove plaintext only after successful encryption.
        try:
            plaintext_temp_path.unlink()
            print("Temporary plaintext database: Removed")

        except OSError as cleanup_error:
            print(
                "WARNING: Encrypted backup succeeded, but "
                "temporary plaintext cleanup failed:",
                cleanup_error
            )
            print(
                "Protect the remaining temporary file and investigate "
                "the file lock."
            )

        # Record the successful backup.
        try:
            record_audit(
                user["user_id"],
                "DATABASE_BACKUP_CREATED_ENCRYPTED",
                "DATABASE_BACKUP",
                None,
                (
                    f"Backup file: {backup_filename}; "
                    "integrity, encryption and saved-file verification passed"
                )
            )
            print("Audit log: Backup activity recorded.")

        except sqlite3.Error as audit_error:
            print(
                "WARNING: Backup succeeded, but audit logging failed:",
                audit_error
            )

    except Exception as error:

        print("\nBACKUP FAILED:", error)

        # Close any remaining SQLite connections.
        if backup_connection is not None:
            backup_connection.close()

        if source_connection is not None:
            source_connection.close()

        # Remove incomplete encrypted temporary files.
        if encrypted_temp_path.exists():
            try:
                encrypted_temp_path.unlink()
            except OSError as cleanup_error:
                print("Encrypted temporary-file cleanup warning:", cleanup_error)

        # Never delete a plaintext file if a completed encrypted
        # backup was not safely published.
        if not backup_published and plaintext_temp_path.exists():
            print(
                "WARNING: A temporary plaintext database remains at:",
                plaintext_temp_path
            )
            print(
                "Protect it. Do not delete it until the backup "
                "has been recovered or verified."
            )


def restore_database_backup(
    user,
    backup_filename,
    destination_filename
):
    """
    Restore a backup into a separate recovery database.

    The live healthcare database is never replaced.
    """

    if user.get("role") != "Admin":
        raise PermissionError(
            "Only an Admin can restore database backups."
        )

    require_permission(user, "backup.manage")

    # Validate filenames.
    if (
        not backup_filename
        or Path(backup_filename).name != backup_filename
    ):
        raise ValueError("Invalid backup filename.")

    if (
        not destination_filename
        or Path(destination_filename).name != destination_filename
    ):
        raise ValueError("Invalid destination filename.")

    if not (
        backup_filename.endswith(".db")
        or backup_filename.endswith(".db.enc")
    ):
        raise ValueError("Unsupported backup format.")

    if not destination_filename.lower().endswith(".db"):
        raise ValueError("Destination must have a .db extension.")

    if destination_filename.lower() in {
        "healthcare.db",
        "healthcare.db-wal",
        "healthcare.db-shm"
    }:
        raise ValueError("The live database cannot be replaced.")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    RESTORE_DIR.mkdir(parents=True, exist_ok=True)

    backup_directory = BACKUP_DIR.resolve()
    restore_directory = RESTORE_DIR.resolve()

    source_path = (backup_directory / backup_filename).resolve()
    destination_path = (
        restore_directory / destination_filename
    ).resolve()

    if source_path.parent != backup_directory:
        raise ValueError("Backup must be in the backups folder.")

    if destination_path.parent != restore_directory:
        raise ValueError("Invalid restoration destination.")

    if not source_path.is_file():
        raise FileNotFoundError("Selected backup does not exist.")

    if destination_path.exists():
        raise FileExistsError(
            "A restored database with that name already exists."
        )

    temporary_path = restore_directory / (
        destination_filename + ".temporary"
    )

    decrypted_temp_path = restore_directory / (
        destination_filename + ".decrypted.temporary"
    )

    if temporary_path.exists() or decrypted_temp_path.exists():
        raise FileExistsError(
            "A temporary restoration file already exists."
        )

    source_connection = None
    restored_connection = None
    restoration_published = False

    try:
        # Decrypt encrypted backups using the existing Fernet key.
        if backup_filename.endswith(".db.enc"):

            encrypted_bytes = source_path.read_bytes()
            decrypted_bytes = get_fernet().decrypt(encrypted_bytes)

            with decrypted_temp_path.open("xb") as decrypted_file:
                decrypted_file.write(decrypted_bytes)

            database_to_restore = decrypted_temp_path

        else:
            # Continue supporting historical plaintext backups.
            database_to_restore = source_path

        # Verify source database.
        verify_database_file(database_to_restore)

        source_uri = (
            database_to_restore.resolve().as_uri()
            + "?mode=ro"
        )

        source_connection = sqlite3.connect(
            source_uri,
            uri=True
        )

        # Create a separate restoration copy.
        restored_connection = sqlite3.connect(temporary_path)

        source_connection.backup(restored_connection)

        # Verify restored database integrity.
        integrity = restored_connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()

        if not integrity or integrity[0] != "ok":
            raise sqlite3.DatabaseError(
                "Restored database integrity check failed."
            )

        tables = {
            row[0]
            for row in restored_connection.execute(
                "SELECT name FROM sqlite_master WHERE type = ?",
                ("table",)
            ).fetchall()
        }

        if not REQUIRED_TABLES.issubset(tables):
            raise sqlite3.DatabaseError(
                "Restored database is missing required tables."
            )

        # Close connections before publishing or deleting files.
        restored_connection.close()
        restored_connection = None

        source_connection.close()
        source_connection = None

        # Publish the verified recovery copy.
        temporary_path.rename(destination_path)
        restoration_published = True

        print("\nDATABASE RESTORATION SUCCESSFUL")
        print("-" * 45)
        print("Source backup:", backup_filename)
        print("Restored copy:", destination_path)
        print("SQLite integrity: Passed")
        print("Required tables: Verified")
        print("Live healthcare database: Not changed")

        # Record restoration activity.
        try:
            record_audit(
                user["user_id"],
                "DATABASE_BACKUP_RESTORED_TO_SEPARATE_COPY",
                "DATABASE_BACKUP",
                None,
                (
                    f"Source: {backup_filename}; "
                    f"destination: {destination_filename}; "
                    "integrity check passed"
                )
            )
            print("Audit log: Restoration activity recorded.")

        except sqlite3.Error as audit_error:
            print(
                "WARNING: Restoration succeeded, but audit logging failed:",
                audit_error
            )

    except Exception:

        if restored_connection is not None:
            restored_connection.close()

        if source_connection is not None:
            source_connection.close()

        # Remove only incomplete restoration files.
        for temporary_file in (
            temporary_path,
            decrypted_temp_path
        ):
            if temporary_file.exists():
                try:
                    temporary_file.unlink()
                except OSError as cleanup_error:
                    print(
                        "Temporary restoration cleanup warning:",
                        cleanup_error
                    )

        raise

    finally:
        # Remove temporary decrypted plaintext only after
        # the restoration copy has been safely published.
        if restoration_published and decrypted_temp_path.exists():
            try:
                decrypted_temp_path.unlink()
            except OSError as cleanup_error:
                print(
                    "WARNING: Temporary decrypted file remains:",
                    cleanup_error
                )


if __name__ == "__main__":
    print("BACKUP MODULE")
    print(
        "Run this module through the authenticated healthcare application."
    )
