
# ROLE-BASED ACCESS CONTROL (RBAC) TESTING REPORT

## 1. Introduction

Role-Based Access Control (RBAC) was incorporated into the Healthcare Governance System to regulate access to information and system functions according to the responsibilities assigned to each staff member. Its main purpose is to protect confidential patient information, prevent unauthorized access and ensure that users only perform activities relevant to their roles.

Testing was conducted to establish whether the permission controls function as intended and whether unauthorized access attempts are properly recorded in the system's audit logs.

## 2. Objectives of the Testing

The RBAC testing was carried out to:

- Confirm that system permissions are assigned according to individual staff roles.
- Ensure that access to confidential patient information is restricted to authorized personnel.
- Verify that staff members cannot perform administrative or technical functions outside their assigned responsibilities.
- Establish whether unauthorized access attempts are blocked by the system.
- Confirm that denied access attempts are captured in the audit trail for accountability and monitoring.

## 3. Roles and Access Permissions

The system defines different access privileges for the following user categories:

| User Role | Main Access Responsibilities |
|---|---|
| Admin | User administration, patient records, incident management, risk management, backup management and other administrative functions. |
| Doctor | Viewing patient records, registering patients and updating clinical information within the assigned branch. |
| Nurse | Viewing patient records and updating patient care notes. |
| Receptionist | Registering patients and accessing limited basic patient information. |
| IT Officer | Managing backups, viewing audit logs and performing authorized technical system functions. |

These permissions are intended to separate clinical, administrative and technical responsibilities while limiting unnecessary access to sensitive information.

## 4. RBAC Testing Procedures and Results

Testing was conducted using existing staff accounts. Each account was assessed against permissions that should either be granted or restricted according to its assigned role.

### 4.1 Doctor Account

The Doctor account was tested to determine whether it could access clinical records while remaining restricted from cybersecurity risk management activities.

The tests established that:

- The Doctor could view patient records belonging to the assigned branch.
- Attempts to access the cybersecurity risk register were rejected.
- Attempts to register new cybersecurity risks were denied.
- Attempts to change the status of existing risks were also denied.

**Test result: PASS.**

The results indicate that the Doctor's access is limited to the clinical responsibilities assigned to the role.

### 4.2 Nurse Account

The Nurse account was assessed to establish whether it could access restricted administrative and cybersecurity functions.

The test confirmed that:

- The Nurse was denied access to the cybersecurity risk register.
- The system generated an access-denied response when the restricted function was attempted.

**Test result: PASS.**

This confirms that the Nurse role does not have permission to manage organizational cybersecurity risks.

### 4.3 Receptionist Account

The Receptionist account was tested against the cybersecurity risk management function.

The test established that:

- The Receptionist could not access the cybersecurity risk register.
- The system blocked the unauthorized request.

**Test result: PASS.**

The results demonstrate that the Receptionist's access is restricted to the basic administrative and patient registration responsibilities assigned to the role.

### 4.4 IT Officer Account

The IT Officer account was assessed to confirm that it could perform technical duties without gaining unrestricted access to clinical or risk management functions.

The following authorized permissions were tested:

- Backup management: Access granted.
- Audit log viewing: Access granted.
- System management: Access granted.

The following restricted permissions were also tested:

- Cybersecurity risk management: Access denied.
- Patient record access: Access denied.

**Test result: PASS.**

The findings demonstrate separation between technical system administration and clinical information management.

### 4.5 Admin Account

The Admin account was tested to verify whether it could access the management functions assigned to its role.

The test examined ten permissions covering user administration, patient records, incident management, cybersecurity risk management, backup management, audit monitoring, system administration and compliance management.

The results confirmed that all ten permissions were granted successfully. No unexpected access restrictions were encountered during the test.

**Test result: PASS.**

The findings confirm that the Admin account has the required management privileges defined in the system's access-control configuration.

## 5. Verification of Unauthorized Access Attempts Through Audit Logs

In addition to testing access restrictions, the system's audit logs were examined to determine whether unauthorized activities were being recorded.

The following records were retrieved during testing:

| Log ID | User ID | User Role | Restricted Permission Attempted |
|---|---:|---|---|
| 106–108 | 2 | Doctor | risk.manage |
| 110 | 3 | Nurse | risk.manage |
| 111 | 4 | Receptionist | risk.manage |
| 112 | 5 | IT Officer | risk.manage |
| 113 | 5 | IT Officer | patient.view |

The audit records show that the system captured the user account involved, the attempted permission, the access-denied action and the corresponding timestamp.

These records provide an accountability mechanism that can help administrators identify and review unauthorized access attempts.

**Audit verification result: PASS.**

## 6. Summary of Findings

The RBAC tests produced the expected results across all five user roles examined: Admin, Doctor, Nurse, Receptionist and IT Officer.

The main findings were:

1. Access permissions are assigned according to the responsibilities of individual staff categories.
2. Clinical, administrative and technical responsibilities are separated through role-specific permissions.
3. Unauthorized attempts to access restricted functions are denied by the system.
4. Access-denied events are recorded in the audit logs to support accountability.
5. The Admin role has the management permissions required by the system's access-control configuration.

Overall, the testing confirmed that the implemented RBAC controls functioned as expected in the scenarios examined.

**Overall RBAC testing result: PASS.**

## 7. Limitations and Recommendations

Although the tested access-control functions performed as expected, further improvements are recommended before production deployment:

- Conduct broader testing of every permission across all user roles.
- Introduce periodic reviews of staff accounts and assigned permissions.
- Review access privileges whenever staff responsibilities change.
- Conduct independent security testing to identify potential authorization weaknesses.
- Ensure that access-control policies remain aligned with applicable healthcare data protection requirements.

The tests described in this report cover selected access permissions and scenarios. They should not be interpreted as proof that every possible authorization weakness has been eliminated.

## 8. Conclusion

The RBAC testing demonstrated that the Healthcare Governance System can restrict access according to assigned staff responsibilities, deny unauthorized operations and record access-denied events.

The results provide evidence that role-based permissions support the protection of confidential patient information and improve accountability within the healthcare environment.

However, broader security testing, periodic access reviews and independent security assessment remain necessary before production deployment.
