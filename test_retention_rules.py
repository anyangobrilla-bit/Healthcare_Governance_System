
from datetime import datetime, timedelta
from pathlib import Path

from backup_retention import (
    get_cleanup_candidates,
    PROTECTED_BACKUPS,
)


print("BACKUP RETENTION RULES TEST")
print("=" * 45)

now = datetime.now()

# Create fictional backup entries.
# No actual backup files are created or deleted.
test_backups = [
    (
        now - timedelta(days=1),
        Path("healthcare_backup_20261111_100000.db.enc")
    ),
    (
        now - timedelta(days=2),
        Path("healthcare_backup_20261110_100000.db.enc")
    ),
    (
        now - timedelta(days=60),
        Path("healthcare_backup_20261110_104358.db")
    ),
    (
        now - timedelta(days=10),
        Path("healthcare_backup_recent.db")
    ),
    (
        now - timedelta(days=45),
        Path("healthcare_backup_20260928_100000.db.enc")
    ),
]

candidates = get_cleanup_candidates(test_backups)

candidate_names = {
    file.name for timestamp, file in candidates
}

expected_candidate = "healthcare_backup_20260928_100000.db.enc"

# Test 1: Two newest backups are retained.
assert all(
    file.name not in candidate_names
    for timestamp, file in test_backups[:2]
)

print("PASS: Two newest backups are retained.")

# Test 2: Protected recovery backup is retained.
protected_name = next(iter(PROTECTED_BACKUPS))

assert protected_name not in candidate_names

print("PASS: Protected recovery backup is retained.")

# Test 3: Backup within 30 days is retained.
assert (
    "healthcare_backup_recent.db"
    not in candidate_names
)

print("PASS: Backups within the retention period are retained.")

# Test 4: Expired backup beyond the safeguards is identified.
assert expected_candidate in candidate_names

print("PASS: Expired backup is identified for cleanup.")

print("\nTEST SUMMARY")
print("=" * 45)
print("All backup retention rule tests passed.")
print("No real backup files were changed.")
