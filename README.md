# Healthcare Governance System

## 1. Project Overview

The Healthcare Governance System is a Python-based prototype designed to demonstrate data governance, patient information privacy and cybersecurity controls in a small healthcare facility.

The system uses Python and SQLite to manage healthcare information while applying access restrictions, authentication, encryption, audit logging and backup management.

## 2. Main Features

- **User authentication:** Secure password hashing and account verification.
- **Multi-factor authentication:** Time-based one-time password (TOTP) verification.
- **Role-based access control:** Different access permissions for Administrators, Doctors, Nurses, Receptionists and IT Officers.
- **Patient data protection:** Encryption of sensitive patient information stored in the database.
- **Audit logging:** Recording of important system activities and denied access attempts.
- **Account protection:** Failed-login tracking, account lockout and MFA lockout.
- **Backup management:** Database backup, restoration permissions and backup retention controls.
- **Risk and incident management:** Support for recording and managing healthcare security risks and incidents.

## 3. Technologies Used

- Python
- SQLite
- Cryptography
- PyOTP
- Visual Studio Code
- PowerShell

## 4. Project Requirements

Install Python and ensure that it is available from the Windows command line.

The project dependencies are listed in `requirements.txt`.

Install the dependencies using:

```powershell
python -m pip install -r requirements.txt
```

## 5. Running the Application

Open PowerShell in the project directory:

```powershell
cd "$HOME\Desktop\Healthcare_Governance_System"
```

Start the application using:

```powershell
python .\main.py
```

Follow the instructions displayed by the application.

## 6. Running Security Tests

The project includes standalone Python test scripts for checking authentication, MFA, patient privacy, encryption, role permissions, audit logging and backup controls.

Run individual tests from the project directory. For example:

```powershell
python .\test_password_hashing.py
python .\test_mfa_security.py
python .\test_patient_encryption.py
python .\test_patient_privacy.py
python .\test_admin_permissions.py
python .\test_retention_rules.py
```

A successful test displays a PASS message.

## 7. Project Structure

The project contains the following main application modules:

- `main.py` – Application entry point and main interface.
- `database.py` – Database operations and audit records.
- `auth.py` – User authentication.
- `mfa.py` – Multi-factor authentication.
- `access_control.py` – Role-based permissions.
- `security.py` – Security-related functions.
- `encryption.py` – Data encryption and decryption.
- `patient_records.py` – Patient information management.
- `backup_management.py` – Database backup and restoration.
- `backup_retention.py` – Backup retention and cleanup.
- `risk_management.py` – Risk management.
- `incident_management.py` – Incident management.
- `it_management.py` – IT administration functions.
- `staff_setup.py` – Staff account setup.
- `migrate_patient_data.py` – Patient data migration.

## 8. Security and Privacy Considerations

The prototype demonstrates several security measures, including password hashing, MFA, role-based access, encryption of sensitive patient fields, audit logging and restricted backup operations.

Only fictional patient information should be used during testing.

Database files, encryption keys, credentials, backup files and other sensitive information should not be included in shared source-code submissions.

## 9. Limitations and Future Improvements

The current implementation is an academic prototype and is not approved for live clinical deployment.

Further work would include:

- Independent security assessment and penetration testing.
- Approved backup and disaster recovery arrangements.
- Off-site and securely managed backup storage.
- Formal approval of recovery time and recovery point objectives.
- Improved session management and monitoring.
- Formal operational approval of data retention and disposal procedures.
- Further testing under realistic healthcare operating conditions.

## 10. Conclusion

The project demonstrates how data governance and cybersecurity controls can be incorporated into a small healthcare information system. It provides a practical foundation for protecting patient information, controlling staff access and improving accountability.