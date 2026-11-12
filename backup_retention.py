
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from access_control import require_permission
from database import record_audit


BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "backups"

RETENTION_DAYS = 30
MINIMUM_BACKUPS_TO_KEEP = 2

# Preserve this pre-encryption recovery backup.
PROTECTED_BACKUPS = {
    "healthcare_backup_20261110_104358.db"
}


def get_backup_files():
    """Return valid timestamped historical and encrypted backups."""

    backups = []
    prefix = "healthcare_backup_"

    if not BACKUP_DIR.is_dir():
        return backups

    for file in BACKUP_DIR.iterdir():

        # Process only regular files directly inside the backup folder.
        if not file.is_file() or file.is_symlink():
            continue

        if not file.name.startswith(prefix):
            continue

        # Identify the supported backup format.
        if file.name.endswith(".db.enc"):
            suffix = ".db.enc"
        elif file.name.endswith(".db"):
            suffix = ".db"
        else:
            continue

        timestamp_text = file.name[
            len(prefix):-len(suffix)
        ]

        try:
            timestamp = datetime.strptime(
                timestamp_text,
                "%Y%m%d_%H%M%S"
            )

            backups.append((timestamp, file))

        except ValueError:
            continue

    return sorted(
        backups,
        key=lambda item: item[0],
        reverse=True
    )


def get_cleanup_candidates(backups=None):
    """Identify expired backups while respecting retention safeguards."""

    if backups is None:
        backups = get_backup_files()

    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)

    candidates = []

    for index, (timestamp, file) in enumerate(backups):

        # Always retain the two newest backups.
        if index < MINIMUM_BACKUPS_TO_KEEP:
            continue

        # Never delete explicitly protected backups.
        if file.name in PROTECTED_BACKUPS:
            continue

        # Retain backups within the 30-day period.
        if timestamp >= cutoff:
            continue

        candidates.append((timestamp, file))

    return candidates


def preview_backup_cleanup():
    """Preview retention decisions without deleting files."""

    print("\nBACKUP RETENTION PREVIEW")
    print("=" * 50)

    print(f"Retention period: {RETENTION_DAYS} days")
    print(
        "Minimum backups to retain: "
        f"{MINIMUM_BACKUPS_TO_KEEP}"
    )

    backups = get_backup_files()

    if not backups:
        print("\nNo timestamped backups were found.")
        return

    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)

    print(f"\nTotal recognised backups: {len(backups)}")

    print("\nBACKUPS TO KEEP")
    print("-" * 50)

    for index, (timestamp, file) in enumerate(backups):

        reasons = []

        if index < MINIMUM_BACKUPS_TO_KEEP:
            reasons.append("Minimum backup requirement")

        if file.name in PROTECTED_BACKUPS:
            reasons.append("Protected recovery backup")

        if timestamp >= cutoff:
            reasons.append("Within retention period")

        if reasons:
            print(f"- {file.name}")
            print("  Reason: " + ", ".join(reasons))

    candidates = get_cleanup_candidates(backups)

    print("\nEXPIRED BACKUPS ELIGIBLE FOR REVIEW")
    print("-" * 50)

    if candidates:
        for timestamp, file in candidates:
            print(f"- {file.name}")
            print(f"  Backup date: {timestamp}")
    else:
        print("No backups are currently eligible for deletion.")

    print("\nPREVIEW ONLY: No files have been deleted.")


def cleanup_expired_backups(user):
    """Delete expired backups after Admin authorisation and confirmation."""

    # Backup cleanup is restricted to Admin accounts.
    if not user or user.get("role") != "Admin":

        user_id = user.get("user_id") if user else None
        role = user.get("role", "Unknown") if user else "Unknown"

        record_audit(
            user_id,
            "ACCESS_DENIED",
            "Permission",
            None,
            (
                f"Role: {role}; "
                "Attempted permission: backup.manage; "
                "Admin role required for backup cleanup."
            )
        )

        raise PermissionError(
            "ACCESS DENIED: Only an Admin can clean up expired backups."
        )

    # Verify the Admin's assigned permission.
    require_permission(user, "backup.manage")

    backups = get_backup_files()
    candidates = get_cleanup_candidates(backups)

    if not candidates:
        print("\nNo expired backups need to be deleted.")
        return

    print("\nEXPIRED BACKUPS SELECTED FOR DELETION")
    print("=" * 50)

    for timestamp, file in candidates:
        print(f"- {file.name}")
        print(f"  Backup date: {timestamp}")

    print(
        "\nThe protected recovery backup and "
        "minimum required backups will be retained."
    )

    confirmation = input(
        "\nType DELETE to confirm backup cleanup: "
    )

    if confirmation != "DELETE":
        print("\nCleanup cancelled. No files were deleted.")
        return

    deleted = []
    failed = []

    backup_root = BACKUP_DIR.resolve()

    for timestamp, file in candidates:

        try:
            # Recheck the file location and type before deletion.
            if file.is_symlink():
                raise OSError("Symbolic links cannot be deleted.")

            if file.resolve().parent != backup_root:
                raise OSError(
                    "File is outside the permitted backup folder."
                )

            if not file.is_file():
                raise OSError("Backup file no longer exists.")

            file.unlink()
            deleted.append(file.name)

        except OSError as error:
            failed.append(f"{file.name}: {error}")

    details = (
        f"Retention period: {RETENTION_DAYS} days; "
        f"minimum retained: {MINIMUM_BACKUPS_TO_KEEP}; "
        f"deleted: {deleted}; "
        f"failed: {failed}"
    )

    try:
        record_audit(
            user["user_id"],
            "EXPIRED_BACKUP_CLEANUP",
            "DATABASE_BACKUP",
            None,
            details
        )

        print("\nCleanup activity recorded in the audit log.")

    except sqlite3.Error as error:
        print(
            "\nWARNING: Cleanup completed, "
            f"but audit logging failed: {error}"
        )

    print("\nBACKUP CLEANUP RESULTS")
    print("-" * 50)
    print("Deleted:", len(deleted))
    print("Failed:", len(failed))

    for error in failed:
        print(error)


if __name__ == "__main__":
    preview_backup_cleanup()
