# FINAL PROJECT REPORT

# HEALTHCARE GOVERNANCE SYSTEM

## 1. Introduction

Healthcare facilities collect and process sensitive information, including patient identities, contact details, medical histories and clinical records. Protecting this information is important for maintaining patient privacy, preventing unauthorized access and ensuring accountability.

The Healthcare Governance System is a Python-based academic prototype developed to demonstrate how data governance and cybersecurity controls can be applied within a small healthcare facility.

The project combines data protection policies, access control, authentication, encryption, audit logging, risk management and backup procedures to provide a practical approach to managing healthcare information securely.

The prototype uses Python and SQLite and is intended to demonstrate the implementation of selected security and governance controls rather than serve as a production healthcare management system.

## 2. Project Objectives

The main objective was to develop a practical healthcare information governance prototype that demonstrates the protection of sensitive patient information.

The specific objectives were to:

1. Establish appropriate access permissions for different healthcare staff roles.
2. Protect user accounts through secure password authentication and multi-factor authentication.
3. Encrypt sensitive patient information stored in the database.
4. Maintain audit records of important system activities and unauthorized access attempts.
5. Implement backup, restoration and retention controls.
6. Demonstrate privacy protection through role-based access to patient information.
7. Incorporate risk management and incident management functions.
8. Relate the system's governance approach to applicable data protection and information security standards.

## 3. System Design and Architecture

The system was designed around the principle that healthcare information should only be accessed and managed by authorized personnel.

The architecture incorporates the following components:

- **User management:** Supports staff accounts and account administration.
- **Authentication:** Verifies user credentials before granting access.
- **Multi-factor authentication:** Adds an additional verification requirement during login.
- **Access control:** Determines which functions each staff role may use.
- **Patient records:** Manages patient information according to assigned permissions.
- **Encryption:** Protects selected sensitive patient fields in database storage.
- **Audit logging:** Records important activities and denied access attempts.
- **Backup management:** Supports database backup, restoration and retention controls.
- **Risk management:** Provides functionality for managing identified security risks.
- **Incident management:** Supports the recording and management of security incidents.

### 3.1 Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development |
| SQLite | Local database storage |
| Cryptography | Protection of sensitive information |
| PyOTP | Time-based multi-factor authentication |
| Visual Studio Code | Development environment |
| PowerShell | Application execution and testing |

## 4. Data Governance and Privacy

Data governance was incorporated to support the responsible collection, access, use, storage and protection of healthcare information.

The system applies role-based access so that staff members receive access according to their responsibilities.

### 4.1 Staff Roles

The prototype includes five main staff roles:

- **Administrator:** Manages user accounts, permissions, system administration, compliance functions and authorized backup operations.
- **Doctor:** Accesses relevant patient medical history and care information.
- **Nurse:** Accesses permitted patient information and care notes but is restricted from medical history.
- **Receptionist:** Accesses permitted basic patient details needed for administrative activities.
- **IT Officer:** Performs authorized technical and backup management functions without general access to patient clinical information.

### 4.2 Patient Information Privacy

Patient privacy was implemented through restrictions on the information visible to different staff members.

Testing demonstrated that:

- Nurses could access permitted patient details and care notes but not medical history.
- Doctors could access medical history and care notes.
- Receptionists could access permitted basic patient details.
- Nurses were denied unauthorized clinical-record modification.
- Unauthorized actions were rejected through permission checks.

Fictional patient information was used during testing.

### 4.3 Data Encryption

The system uses encryption to protect five sensitive patient information fields stored in SQLite.

The encryption test confirmed that the five fields were encrypted in database storage and that an authorized Doctor could retrieve the decrypted information through the application.

Encryption keys must be stored and managed separately from the database in a properly secured deployment.

## 5. Cybersecurity Implementation

Several security controls were incorporated into the application.

### 5.1 Password Security

Passwords are protected using PBKDF2-HMAC-SHA256 with 600,000 iterations and randomly generated salts.

Testing confirmed that:

- Passwords were not stored as readable text.
- Correct passwords matched their stored hashes.
- Incorrect passwords were rejected.
- Separate password hashes used different salts.

### 5.2 Multi-Factor Authentication

The application implements time-based one-time password (TOTP) verification using PyOTP.

The implemented controls include:

- MFA enrollment.
- MFA enrollment confirmation.
- Verification of valid authentication codes.
- Rejection of previously used authentication codes.
- Tracking of failed MFA attempts.
- Account lockout after five failed MFA attempts.
- A fifteen-minute MFA lockout period.
- Administrator-controlled MFA reset.

Testing confirmed successful MFA verification, replay protection, lockout persistence and audit logging.

### 5.3 Login Protection

The authentication process includes controls against repeated unsuccessful password attempts.

Testing demonstrated that:

- Unknown usernames were rejected.
- Inactive accounts were prevented from logging in.
- Five consecutive incorrect password attempts triggered account lockout.
- Correct passwords were rejected during an active lockout.
- Successful password verification cleared the applicable failed-attempt count.
- Lockout and blocked-login events were recorded.

The prototype uses username-based lockout. Additional controls against distributed and IP-based attacks would be needed in a production environment.

### 5.4 Audit Logging

The system maintains audit records for important security and administrative activities.

Examples include:

- Successful authentication stages.
- Failed authentication attempts.
- Account lockout events.
- Unauthorized access attempts.
- Administrator MFA resets.
- Backup-related security activities.

Testing confirmed that unauthorized permission requests generated `ACCESS_DENIED` audit records.

The authentication audit sequence was also tested to confirm that a successful login event was not recorded when MFA verification failed.

## 6. Backup and Disaster Recovery

Backup management was included to support the protection and recovery of healthcare database information.

The system includes functions for creating database backups, restricting restoration operations and managing backup retention.

### 6.1 Backup Access Restrictions

Backup operations are restricted according to staff roles.

Testing confirmed that:

- Doctors were denied backup management permission.
- IT Officers were denied database restoration permission.
- Backup cleanup was restricted to Administrators.
- Unauthorized backup operations generated audit records where tested.

### 6.2 Backup Retention

The implemented retention rules include:

- A thirty-day retention period.
- Retention of the two newest backups.
- Protection of a designated recovery backup.
- Identification of expired backups for possible cleanup.
- Administrator authorization for backup cleanup.

Testing confirmed that the two newest backups, protected recovery backup and backups within the retention period were retained. Expired backups were correctly identified.

No real backup files were deleted during the retention rules test.

### 6.3 Disaster Recovery Considerations

The project includes database restoration functionality and restrictions on who may perform restoration.

However, a complete operational disaster recovery arrangement would require additional work, including approved recovery time objectives (RTO), recovery point objectives (RPO), secure off-site backup storage and documented recovery procedures.

The designated pre-encryption recovery backup also requires an approved secure disposal procedure because it contains unencrypted sensitive information.

## 7. Risk and Incident Management

Risk management and incident management functionality were included as part of the wider governance framework.

Risk management supports the identification and management of information security risks, while incident management provides functionality for recording and managing security incidents.

The project recognizes risks such as:

- Unauthorized access to patient information.
- Exposure of sensitive records.
- Compromised staff accounts.
- Loss or corruption of database records.
- Improper backup handling.
- Inadequate access permissions.
- Failure to recover information following a system disruption.

These risks inform the need for access restrictions, encryption, authentication, audit monitoring and backup procedures.

## 8. Legal and Standards Considerations

The governance approach was informed by the following legal and information security references:

### 8.1 Kenya Data Protection Act, 2019

The Kenya Data Protection Act, 2019 provides an important legal framework for the processing and protection of personal data in Kenya.

The prototype demonstrates selected principles relevant to protecting personal information, including controlled access, confidentiality, security safeguards and accountability.

### 8.2 General Data Protection Regulation (GDPR)

GDPR was considered as an additional reference where its requirements may apply to the processing of personal data.

### 8.3 ISO/IEC 27001:2022

ISO/IEC 27001:2022 was considered as an information security management reference for organizing security controls, managing risks and supporting continuous improvement.

The project demonstrates selected controls informed by these frameworks. It does not constitute legal compliance certification or ISO certification.

## 9. Security Testing and Results

The application was evaluated using standalone Python test scripts.

The following table summarizes the principal tests and their results.

| Test area | Verification result |
|---|---|
| Password hashing | PASS |
| Successful password authentication | PASS |
| Inactive account protection | PASS |
| Unknown username rejection | PASS |
| Password lockout | PASS |
| MFA enrollment and verification | PASS |
| MFA replay protection | PASS |
| MFA lockout | PASS |
| Authentication audit sequence | PASS |
| Administrator MFA reset | PASS |
| Administrator permissions | PASS |
| Nurse and Doctor patient access | PASS |
| Patient data encryption | PASS |
| Patient privacy restrictions | PASS |
| Unauthorized patient updates | PASS |
| Doctor audit access restriction | PASS |
| Doctor backup access restriction | PASS |
| IT Officer restoration restriction | PASS |
| Backup retention rules | PASS |
| Backup cleanup permissions | PASS |

### 9.1 Testing Observations

The tests demonstrated that the implemented controls behaved as expected in the tested scenarios.

In particular:

- Authentication controls rejected invalid login attempts.
- MFA controls enforced additional verification.
- Role-based access restrictions prevented selected unauthorized activities.
- Sensitive patient fields were encrypted in database storage.
- Audit records captured tested unauthorized access attempts.
- Backup retention rules identified eligible expired backups without changing real backup files.

The tests were conducted using the local prototype and test accounts. They do not represent exhaustive security testing or independent penetration testing.

## 10. Limitations

Although the prototype demonstrates several important healthcare data governance and cybersecurity controls, some limitations remain.

1. **Local database:** The system uses SQLite and is not designed for a large multi-user clinical environment.
2. **Session management:** Session inactivity protection has been tested in the main application menu, but does not cover every possible submenu and interaction.
3. **Lockout protection:** Current lockout controls are primarily username-based and do not provide comprehensive distributed attack protection.
4. **Backup storage:** Off-site backup arrangements have not been fully implemented.
5. **Backup automation:** Backup cleanup is manually authorized rather than automatically scheduled.
6. **Recovery planning:** RTO and RPO values require formal approval.
7. **Key management:** Production deployment would require stronger operational controls for encryption key storage, access and recovery.
8. **Security assessment:** The application has not undergone an independent security assessment or formal penetration test.
9. **Compliance assurance:** Implementing selected controls does not establish full compliance with applicable laws or standards.

## 11. Recommendations and Future Improvements

The following improvements are recommended before any real-world deployment:

- Conduct independent security testing and vulnerability assessment.
- Establish secure off-site backup storage.
- Approve and document recovery time and recovery point objectives.
- Establish formal encryption key management and recovery procedures.
- Improve session management across all application functions.
- Introduce stronger monitoring and protection against distributed login attacks.
- Approve formal data retention and secure disposal procedures.
- Review staff permissions regularly.
- Establish incident response and breach notification procedures.
- Conduct periodic security reviews and staff awareness training.

## 12. Conclusion

The Healthcare Governance System demonstrates how data governance and cybersecurity controls can be incorporated into a small healthcare information management prototype.

The project implemented and tested several important controls, including secure password hashing, multi-factor authentication, role-based access control, patient data encryption, audit logging and backup retention restrictions.

The test results provide evidence that the selected controls functioned as expected in the tested scenarios.

Although additional improvements are required before operational deployment, the project provides a practical foundation for understanding how healthcare information can be protected through appropriate governance, technical safeguards and accountability measures.

The overall project demonstrates the importance of balancing the confidentiality, accessibility and availability of healthcare information while ensuring that access is limited to authorized personnel.