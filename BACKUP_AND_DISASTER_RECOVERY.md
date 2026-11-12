# Healthcare Data Backup and Disaster Recovery Policy

## 1. Purpose

This policy establishes procedures for protecting healthcare information through regular database backups, secure storage, controlled restoration and recovery testing.

## 2. Scope

This policy applies to the clinic's administrators, IT personnel and authorized staff who manage or access the healthcare information system.

## 3. Backup Procedures

- The clinic shall create regular backups of its healthcare database.
- Backups shall be stored separately from the live database.
- Each backup shall have a unique filename containing its creation date and time.
- Backup integrity shall be checked after creation.
- Access to backup files shall be restricted to authorized personnel.
- Backup files containing encrypted patient information shall be protected against unauthorized access.

## 4. Encryption and Key Protection

- Sensitive patient fields shall be encrypted before storage.
- Backup copies shall preserve encrypted patient information.
- The encryption key shall be stored separately from the database and backup files.
- Access to the encryption key shall be restricted to authorized personnel.
- The key shall have a secure recovery copy because losing it may make encrypted patient information permanently inaccessible.

## 5. Restoration Authorization

- Only an authorized Administrator may restore a database backup.
- The system shall verify the integrity of a selected backup before restoration.
- Restoration shall initially create a separate recovered database copy.
- The live database shall not be overwritten without an approved recovery decision.
- Restoration activities shall be recorded in the system audit logs.

## 6. Recovery Testing

The clinic shall periodically test its backup and restoration procedures.

Testing shall confirm:
- Database integrity.
- Availability of expected database tables.
- Preservation of patient records.
- Preservation of encrypted patient fields.
- Successful decryption using the authorized encryption key.
- Availability of staff accounts, incidents, risks and audit records.

## 7. Responsibilities

**Administrator**
- Authorizes database restoration.
- Oversees backup and recovery activities.
- Ensures that recovery activities are documented.

**IT Officer**
- Performs authorized database backups.
- Checks backup integrity.
- Protects backup files and encryption-key access.
- Reports backup and recovery failures.

**Authorized Healthcare Staff**
- Follow information security procedures.
- Report suspected data loss or security incidents.

## 8. Recovery Records

The system shall maintain records of backup creation, restoration attempts, successful restorations and denied restoration requests.

## 9. Review

This policy shall be reviewed periodically and whenever significant changes occur to the clinic's information systems or security requirements.

---

**Implementation note:** This policy describes the current project prototype. Backup frequency, retention periods, recovery time objectives and recovery point objectives must be formally approved by clinic management before operational deployment.
##  Backup Retention and Disposal Policy

### 1. Retention Period

The healthcare system implements a 30-day backup retention period. Backups older than 30 days may be considered for deletion, subject to administrative review.

The system also maintains a minimum of two backups to support recovery.

### 2. Backup Protection

The following safeguards are implemented:

- The two most recent backups are protected from automatic cleanup.
- The pre-encryption backup is specifically protected from deletion because it contains sensitive patient information in its earlier, unencrypted form.
- Only an authenticated Admin can perform backup cleanup.
- The cleanup process checks eligibility before deleting any backup.
- A preview function displays backups to retain and those eligible for review without deleting files.

### 3. Administrative Responsibilities

Backup retention is accessed through the Admin menu under **Manage Backup Retention**.

The Admin can:
- Preview backup retention.
- Clean up eligible expired backups.
- Return to the main Admin menu.

Backup cleanup is currently a manual operation and is not automatically scheduled.

### 4. Testing and Verification

The following tests were conducted:

| Test | Result |
|---|---|
| Backup retention preview | Passed |
| 30-day retention period | Passed |
| Minimum two backups safeguard | Passed |
| Protected backup safeguard | Passed |
| IT Officer denied cleanup access | Passed |
| Admin cleanup permission | Passed |
| Cleanup when no expired backups exist | Passed |
| Integration with Admin menu | Passed |
| Return to Admin menu and logout | Passed |

No backup files were deleted during these tests because all existing backups were within the retention period.

### 5. Future Improvements

Before production deployment, the clinic should approve the retention policy, establish an automated cleanup schedule, maintain secure off-site backup copies, and implement appropriate controls for the secure disposal of backups containing sensitive patient information.