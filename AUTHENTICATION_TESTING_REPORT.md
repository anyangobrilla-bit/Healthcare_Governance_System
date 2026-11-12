
# AUTHENTICATION AND LOGIN SECURITY TESTING REPORT

## 1. Introduction

This report documents the authentication and login security controls implemented and tested in the Healthcare Governance System. The purpose is to protect staff accounts and prevent unauthorized access to confidential healthcare information.

Testing was conducted using temporary fictional staff accounts to evaluate password security, account lockouts, multi-factor authentication, audit logging, session inactivity timeout, and administrator-controlled MFA recovery.

## 2. Authentication Security Controls

The system implements the following controls:

- Password hashing using PBKDF2-HMAC-SHA256 with 600,000 iterations and a random salt.
- Verification of login credentials against stored password hashes.
- Blocking of inactive staff accounts.
- Rejection and audit logging of unknown usernames.
- Temporary account lockout after five consecutive failed password attempts.
- A 15-minute temporary password lockout period.
- Multi-factor authentication (MFA) using time-based one-time passwords (TOTP).
- MFA enrollment and confirmation using an authenticator application.
- Encryption of stored MFA secrets.
- Rejection of previously used MFA codes to prevent replay.
- Temporary lockout protection following repeated failed MFA attempts.
- Recording of password verification, MFA verification, and successful login events in the audit log.
- Successful login recorded only after both password and MFA verification.
- Administrator-controlled MFA reset for other staff accounts.
- Administrator password verification before an MFA reset.
- Rejection of unauthorized MFA reset attempts and administrator self-reset.
- Audit logging of administrator MFA reset activity.
- Automatic logout after 15 minutes of inactivity at the main role menu.
- Audit logging of automatic session termination.
- Preservation of the existing manual logout option.

## 3. Testing Procedures and Results

| Test | Expected result | Outcome |
|---|---|---|
| Incorrect password | Login rejected | PASS |
| Unknown username | Login rejected and recorded | PASS |
| Inactive staff account | Login blocked | PASS |
| Password hashing | Password not stored as readable text | PASS |
| Correct password | Password verification succeeds | PASS |
| Five consecutive failed password attempts | Account temporarily locked | PASS |
| Correct password during lockout | Login remains blocked | PASS |
| Successful password verification resets counter | Failed-attempt counter cleared | PASS |
| Lockout audit logging | Lockout and blocked login events recorded | PASS |
| MFA enrollment | Enrollment process starts successfully | PASS |
| MFA enrollment confirmation | Valid authenticator code enables MFA | PASS |
| MFA enabled status | Database confirms MFA is enabled | PASS |
| Valid MFA code | Authentication code accepted | PASS |
| MFA replay protection | Previously used code rejected | PASS |
| Five failed MFA attempts | MFA lockout triggered | PASS |
| MFA lockout persistence | Lockout remains recorded in database | PASS |
| Successful MFA audit | MFA verification event recorded | PASS |
| Successful login audit sequence | Login recorded after password and MFA verification | PASS |
| Failed MFA authentication | No successful login event recorded | PASS |
| Inactivity timeout | Session expires after configured inactivity period | PASS |
| Automatic logout audit | Session termination recorded in audit log | PASS |
| Administrator MFA reset | Target user's MFA enrollment removed | PASS |
| MFA reset attempt records | Target's MFA failed-attempt records removed | PASS |
| Password preservation during MFA reset | Existing password remains unchanged | PASS |
| Ordinary login attempts during MFA reset | Password-login attempt records preserved | PASS |
| Administrator reset audit | Reset activity recorded in audit log | PASS |
| Non-administrator reset attempt | Request rejected | PASS |
| Incorrect administrator password | Reset request rejected | PASS |
| Administrator self-reset | Request rejected | PASS |

## 4. Login Lockout Verification

A dedicated test script, `test_login_lockout.py`, was used with temporary fictional staff accounts.

The test confirmed that:

1. Five consecutive incorrect passwords triggered a temporary account lockout.
2. The correct password was rejected while the account remained locked.
3. A separate test account successfully authenticated after two failed attempts, and its failed-attempt counter was cleared.
4. The system recorded the account lockout and subsequent blocked login in the audit log.
5. Temporary test accounts were deactivated after testing, while historical security records were preserved.

The password lockout duration is configured to 15 minutes.

## 5. Multi-Factor Authentication Verification

MFA was implemented using time-based one-time passwords (TOTP).

The system supports authenticator enrollment, verification, replay protection, and failed-attempt lockout.

Testing was performed using temporary fictional staff accounts.

The tests confirmed that:

1. MFA enrollment could be initiated successfully.
2. A valid authenticator code confirmed enrollment and enabled MFA.
3. The system correctly identified an account with MFA enabled.
4. A fresh valid authenticator code was accepted.
5. Reusing an already accepted authenticator code was rejected.
6. Five consecutive failed MFA attempts triggered a temporary lockout.
7. The MFA lockout was stored in the database and remained effective when another verification was attempted.
8. Temporary test accounts were deactivated, while MFA settings and historical security records were preserved where applicable.

### Authentication Audit Sequence

A separate test script, `test_auth_audit_sequence.py`, examined the order of authentication audit events.

The successful authentication scenario confirmed this sequence:

1. Password verification was recorded.
2. Successful MFA verification was recorded.
3. The successful login event was recorded after both authentication factors had succeeded.

The failed authentication scenario confirmed that:

1. Password verification was recorded.
2. An invalid MFA code was rejected.
3. No successful login event was recorded for the failed MFA attempt.

The test passed for both scenarios.

The successful-login audit action was tested using the same audit-recording logic as the main application. The corresponding `main.py` source flow was also inspected to confirm that the successful-login audit follows the MFA success check.

## 6. Administrator-Controlled MFA Reset Verification

The administrator MFA reset functionality was tested using a dedicated test script, `test_admin_mfa_reset.py`.

The test used temporary fictional administrator and doctor accounts.

The test confirmed that:

1. An administrator could reset another staff member's MFA enrollment.
2. The target user's MFA enrollment was removed.
3. The target user's failed MFA attempt records were removed.
4. Ordinary password-login attempt records remained unchanged.
5. The target user's existing password remained unchanged.
6. The administrator's reset action was recorded in the audit log with the target account and reason for the reset.
7. A non-administrator could not perform an MFA reset.
8. An incorrect administrator password resulted in rejection.
9. An administrator could not reset their own MFA enrollment.

All administrator MFA reset tests passed.

Temporary test accounts were deactivated after testing. Audit history and security records were preserved.

## 7. Session Inactivity Timeout Verification

A 15-minute inactivity timeout was implemented in the main role menu.

The timeout was tested using a temporary five-second setting during testing. The saved application configuration remained set to 900 seconds (15 minutes).

The test confirmed that:

1. The Admin session menu displayed successfully.
2. The system detected the absence of keyboard activity.
3. The session automatically expired after the temporary five-second test period.
4. The application displayed a session expiration message and returned to the PowerShell prompt.
5. The automatic logout event was successfully recorded in the audit log.
6. The existing manual logout functionality was preserved.

The automatic logout audit entry was verified as follows:

- Audit Log ID: 131
- Action: `SESSION_AUTO_LOGOUT`
- Record Type: Session
- Details: Automatically logged out after 15 minutes of menu inactivity.
- Timestamp: 2026-11-10T10:04:26.750007+00:00

This confirms that the automatic logout process is connected to the audit logging mechanism.

**Implementation limitation:** The inactivity timeout currently monitors the main role menu. It does not monitor inactivity inside forms, backup-retention submenus, or other operations that use ordinary input functions. The implementation uses Windows console-specific functionality.

## 8. Audit Logging Evidence

The audit log records authentication-related activities, including:

- Staff account creation.
- Password verification.
- Failed login attempts.
- Unknown username attempts.
- Blocked login attempts involving inactive accounts.
- Temporary password lockouts.
- Login attempts blocked during an active lockout.
- MFA verification successes and failures.
- Successful login after password and MFA verification.
- Administrator-controlled MFA reset activity.
- Automatic session termination due to menu inactivity.

The authentication audit-sequence tests confirmed that successful login is not recorded when MFA verification fails.

The administrator MFA reset test confirmed that reset activity is recorded with the administrator's account, the target account, and the stated reason.

The verified automatic logout entry (Log ID 131) also provides evidence that session expiration is recorded.

These records support accountability and help administrators investigate suspicious access attempts.

## 9. Security Limitations

Although the authentication controls have passed the tests described above, some additional protections remain to be implemented or evaluated:

- IP-based rate limiting and protection against distributed login attempts.
- Comprehensive session expiration covering all application operations and input forms.
- Further testing of administrator MFA recovery under different operational scenarios.
- Production-grade monitoring and alerting.
- More comprehensive session management suitable for a production environment.
- Further testing of concurrent authentication attempts and production deployment conditions.

The temporary account lockouts are username-based and should be supplemented with additional controls before production deployment.

The inactivity timeout is limited to the main role menu and is Windows-console-specific. It should not be considered a complete session management solution.

The administrator MFA reset functionality has passed the implemented security tests, but further operational testing and a documented recovery procedure would strengthen its use in a real healthcare environment.

## 10. Conclusion

The authentication testing demonstrated that the Healthcare Governance System can verify staff credentials, protect stored passwords, block inactive accounts, record authentication events, and temporarily lock accounts after repeated failed password attempts.

The MFA testing further demonstrated that the system can enroll staff accounts, verify authenticator codes, reject replayed codes, and apply temporary lockouts following repeated failed MFA attempts.

The authentication audit-sequence tests confirmed that a successful login is recorded only after password and MFA verification have both succeeded.

Administrator MFA reset testing confirmed that authorized administrators can reset another staff member's MFA while preserving the user's password and ordinary password-login attempt records. Unauthorized reset attempts, incorrect administrator passwords, and administrator self-reset attempts were rejected.

The session timeout testing also confirmed that the application can automatically log out an inactive user from the main role menu and record the event in the audit log.

These results provide evidence that the implemented authentication controls contribute to protecting patient information and strengthening accountability within the healthcare environment. However, further improvements, broader testing, and independent security assessment are required before production deployment.
