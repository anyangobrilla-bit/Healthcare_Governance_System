
import sqlite3
import time
import msvcrt
from getpass import getpass

from database import (
    initialize_database,
    get_connection,
    record_audit
)

from auth import first_time_setup, authenticate_user

from mfa import (
    prepare_mfa_table,
    begin_mfa_enrollment,
    confirm_mfa_enrollment,
    verify_mfa_code,
    is_mfa_enabled,
    check_mfa_lockout,
    admin_reset_mfa
)

from patient_records import (
    prepare_patient_table,
    create_patient,
    list_patients,
    update_clinical_record,
    update_care_notes
)

from it_management import view_audit_logs

from backup_management import (
    create_database_backup,
    restore_database_backup,
    BACKUP_DIR
)

from backup_retention import (
    preview_backup_cleanup,
    cleanup_expired_backups
)

from incident_management import (
    report_incident,
    list_incidents,
    update_incident_status
)

from risk_management import (
    add_risk,
    list_risks,
    update_risk_status
)


# ==========================================
# SESSION INACTIVITY SETTINGS
# ==========================================

INACTIVITY_TIMEOUT_SECONDS = 15 * 60


# ==========================================
# MFA SETTINGS
# ==========================================

MFA_MAX_ATTEMPTS = 5
MFA_ENROLLMENT_MAX_ATTEMPTS = 3


# ==========================================
# SESSION INPUT WITH TIMEOUT
# ==========================================

def get_input_with_timeout(prompt, timeout_seconds):
    """Collect keyboard input and return None after inactivity."""

    print(prompt, end="", flush=True)

    characters = []
    last_activity = time.monotonic()

    while True:

        if msvcrt.kbhit():

            character = msvcrt.getwch()
            last_activity = time.monotonic()

            if character in ("\r", "\n"):
                print()
                return "".join(characters)

            elif character == "\003":
                raise KeyboardInterrupt

            elif character == "\b":

                if characters:
                    characters.pop()
                    print("\b \b", end="", flush=True)

            elif character in ("\x00", "\xe0"):

                if msvcrt.kbhit():
                    msvcrt.getwch()

            elif character.isprintable():

                characters.append(character)
                print(character, end="", flush=True)

        else:

            inactive_time = time.monotonic() - last_activity

            if inactive_time >= timeout_seconds:

                print("\n\nSESSION EXPIRED")
                print("You have been automatically logged out")
                print("because of inactivity.")

                return None

            time.sleep(0.1)


# ==========================================
# APPLICATION PREPARATION
# ==========================================

def prepare_application():
    """Initialize the database and prepare application tables."""

    initialize_database()
    prepare_patient_table()
    prepare_mfa_table()

    with get_connection() as connection:

        result = connection.execute(
            "SELECT COUNT(*) AS total FROM users"
        ).fetchone()

        user_count = result["total"]

    if user_count == 0:
        first_time_setup()


# ==========================================
# MULTI-FACTOR AUTHENTICATION
# ==========================================

def complete_mfa_enrollment(user):
    """Enroll a staff member in authenticator-based MFA."""

    print("\nMULTI-FACTOR AUTHENTICATION ENROLLMENT")
    print("=" * 50)

    print("Your account has not yet been enrolled in MFA.")
    print("You must configure an authenticator app before")
    print("you can access the healthcare system.")

    print("\nSUPPORTED AUTHENTICATOR APPS")
    print("1. Google Authenticator")
    print("2. Microsoft Authenticator")
    print("3. Another compatible TOTP authenticator")

    print("\nENROLLMENT INSTRUCTIONS")
    print("1. Open your authenticator app.")
    print("2. Select the option to add an account.")
    print("3. Choose manual entry or enter a setup key.")
    print("4. Enter the secret key displayed below.")
    print("5. Use the account name shown below.")

    try:

        secret, provisioning_uri = begin_mfa_enrollment(user)

        print("\nYOUR MFA ACCOUNT")
        print("-" * 50)
        print("Account:", user["username"])
        print("Issuer: Healthcare Governance System")

        print("\nYOUR SECRET KEY:")
        print(secret)

        print("\nIMPORTANT:")
        print("Keep this secret key private.")
        print("Do not send it to anyone.")
        print("Do not paste it into messages or emails.")
        print("Store it securely in your authenticator app.")

        for attempt in range(
            1,
            MFA_ENROLLMENT_MAX_ATTEMPTS + 1
        ):

            print(
                f"\nEnrollment verification "
                f"({attempt}/{MFA_ENROLLMENT_MAX_ATTEMPTS})"
            )

            code = getpass(
                "Enter the six-digit code from your authenticator: "
            ).strip()

            if not code.isdigit() or len(code) != 6:
                print("Invalid format. Enter exactly six digits.")
                continue

            if confirm_mfa_enrollment(user, code):

                print("\nMFA ENROLLMENT SUCCESSFUL.")
                print("Your authenticator has been linked to your account.")

                return True

            print("Verification failed. Check your authenticator code.")

        print("\nMFA enrollment was not completed.")
        print("Please restart the login process to try again.")

        return False

    except Exception as error:

        print("\nMFA enrollment could not be completed.")
        print("Error:", error)

        return False


def authenticate_with_mfa(user):
    """Require MFA verification before granting application access."""

    if not is_mfa_enabled(user["user_id"]):

        enrollment_successful = complete_mfa_enrollment(user)

        if not enrollment_successful:
            return False

        return True

    print("\nMULTI-FACTOR AUTHENTICATION")
    print("=" * 40)

    if check_mfa_lockout(user):

        print("\nACCESS DENIED: MFA account temporarily locked.")
        print("Please wait for the 15-minute lockout period to expire.")

        return False

    print("Enter the six-digit code from your authenticator app.")

    for attempt in range(1, MFA_MAX_ATTEMPTS + 1):

        code = getpass(
            f"Authenticator code ({attempt}/{MFA_MAX_ATTEMPTS}): "
        ).strip()

        if not code.isdigit() or len(code) != 6:
            print("Invalid code format. Enter six digits.")
            continue

        try:

            if verify_mfa_code(user, code):

                print("\nMFA verification successful.")
                return True

            print("MFA verification failed.")

            if check_mfa_lockout(user):

                print("\nACCESS DENIED: MFA account temporarily locked.")
                print("Please wait 15 minutes before trying again.")

                return False

        except Exception as error:

            print("MFA verification error:", error)
            return False

    print("\nMaximum MFA attempts reached.")
    print("Access denied. Please restart the login process.")

    return False


# ==========================================
# ADMINISTRATOR MFA RECOVERY
# ==========================================

def admin_mfa_recovery(admin_user):
    """Allow an administrator to reset another staff member's MFA."""

    if admin_user.get("role") != "Admin":

        raise PermissionError(
            "Only an administrator can reset staff MFA."
        )

    print("\nADMINISTRATOR MFA RECOVERY")
    print("=" * 45)

    print("This operation removes the selected staff member's")
    print("existing authenticator enrollment.")
    print("The staff member must enroll a new authenticator")
    print("during their next successful login.")

    print("\nEnter the target staff account details.")

    target_username = input(
        "\nTarget staff username: "
    ).strip()

    if not target_username:
        print("\nA target username is required.")
        return

    reason = input(
        "Reason for MFA reset: "
    ).strip()

    if not reason:
        print("\nA reason for the reset is required.")
        return

    print("\nRESET CONFIRMATION")
    print("-" * 45)
    print(f"Target username: {target_username}")
    print(f"Reason: {reason}")
    print("Your own administrator account will not be reset.")

    confirmation = input(
        "\nType YES to authorize this MFA reset: "
    ).strip()

    if confirmation != "YES":
        print("\nMFA reset cancelled.")
        return

    print("\nAdministrator identity verification")

    admin_password = getpass(
        "Re-enter your administrator password: "
    )

    try:

        reset_successful = admin_reset_mfa(
            admin_user,
            target_username,
            reason,
            admin_password
        )

        if reset_successful:

            print("\nMFA RESET SUCCESSFUL.")
            print("The target staff member's previous MFA enrollment")
            print("has been removed.")
            print("Their next login will require a new MFA enrollment.")
            print("The administrator action has been recorded")
            print("in the system audit log.")

    except PermissionError as error:

        print(f"\nACCESS DENIED: {error}")

    except ValueError as error:

        print(f"\nRESET NOT COMPLETED: {error}")

    except Exception as error:

        print("\nMFA reset could not be completed.")
        print("Error:", error)


# ==========================================
# PATIENT MANAGEMENT
# ==========================================

def display_patients(user):
    """Display patient information according to permissions."""

    patients = list_patients(user)

    if not patients:
        print("\nNo patient records found.")
        return

    print("\nPATIENT RECORDS")
    print("=" * 50)

    for patient in patients:

        patient_data = dict(patient)

        if user["role"] == "Receptionist":

            allowed_fields = [
                "patient_id",
                "patient_number",
                "full_name",
                "phone_number",
                "branch"
            ]

            patient_data = {
                field: patient_data[field]
                for field in allowed_fields
                if field in patient_data
            }

        for field, value in patient_data.items():
            print(f"{field.replace('_', ' ').title()}: {value}")

        print("-" * 50)


def register_patient(user):
    """Register a patient using fictional test information."""

    print("\nREGISTER NEW PATIENT")
    print("-" * 35)
    print("Use fictional test information only.")

    patient_number = input("Patient number: ").strip()
    full_name = input("Patient full name: ").strip()
    date_of_birth = input("Date of birth (YYYY-MM-DD): ").strip()
    gender = input("Gender: ").strip()
    phone_number = input("Phone number: ").strip()

    medical_history = input(
        "Medical history (or leave blank): "
    ).strip()

    create_patient(
        user,
        patient_number,
        full_name,
        date_of_birth,
        gender,
        phone_number,
        medical_history
    )


def update_clinical(user):
    """Update a patient's clinical information."""

    print("\nUPDATE CLINICAL RECORD")
    print("-" * 35)

    patient_id = int(input("Enter patient record ID: "))

    medical_history = input(
        "Enter updated medical history: "
    ).strip()

    update_clinical_record(
        user,
        patient_id,
        medical_history
    )


def update_care(user):
    """Update patient care notes."""

    print("\nUPDATE PATIENT CARE NOTES")
    print("-" * 35)

    patient_id = int(input("Enter patient record ID: "))

    care_notes = input("Enter care notes: ").strip()

    update_care_notes(
        user,
        patient_id,
        care_notes
    )


# ==========================================
# SECURITY INCIDENT MANAGEMENT
# ==========================================

def report_security_incident(user):
    """Collect and report a security incident."""

    print("\nREPORT SECURITY INCIDENT")
    print("-" * 35)

    title = input("Incident title: ").strip()

    description = input(
        "Incident description: "
    ).strip()

    severity = input(
        "Severity (Low, Medium, High, Critical): "
    ).strip().title()

    report_incident(
        user,
        title,
        description,
        severity
    )


def view_security_incidents(user):
    """Display recorded security incidents."""

    list_incidents(user)


def change_incident_status(user):
    """Update the status of a security incident."""

    print("\nUPDATE INCIDENT STATUS")
    print("-" * 35)

    incident_id = int(input("Enter incident ID: "))

    new_status = input(
        "New status (Open, In Progress, Resolved, Closed): "
    ).strip().title()

    update_incident_status(
        user,
        incident_id,
        new_status
    )


# ==========================================
# CYBERSECURITY RISK MANAGEMENT
# ==========================================

def register_risk(user):
    """Register a new cybersecurity risk."""

    print("\nREGISTER CYBERSECURITY RISK")
    print("-" * 40)

    risk_name = input("Risk name: ").strip()

    description = input(
        "Risk description: "
    ).strip()

    likelihood = int(input("Likelihood (1-5): "))

    impact = int(input("Impact (1-5): "))

    mitigation = input(
        "Risk mitigation measures: "
    ).strip()

    add_risk(
        user,
        risk_name,
        description,
        likelihood,
        impact,
        mitigation
    )


def view_risk_register(user):
    """Display all recorded cybersecurity risks."""

    list_risks(user)


def change_risk_status(user):
    """Update the status of a cybersecurity risk."""

    print("\nUPDATE CYBERSECURITY RISK STATUS")
    print("-" * 40)

    risk_id = int(input("Enter risk ID: "))

    new_status = input(
        "New status (Open, Under Review, Mitigated, Closed): "
    ).strip().title()

    update_risk_status(
        user,
        risk_id,
        new_status
    )


# ==========================================
# DATABASE RESTORATION
# ==========================================

def restore_database(user):
    """Restore an encrypted or historical backup into a separate recovery copy."""

    if user.get("role") != "Admin":
        raise PermissionError(
            "Only an Admin can restore database backups."
        )

    print("\nDATABASE RESTORATION")
    print("=" * 45)

    print("The live healthcare database will NOT be overwritten.")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backup_files = sorted(
        [
            file
            for file in BACKUP_DIR.iterdir()
            if file.is_file()
            and (
                file.name.endswith(".db")
                or file.name.endswith(".db.enc")
            )
            and not file.name.startswith(".")
        ],
        key=lambda file: file.name
    )

    if not backup_files:
        print("\nNo database backup files were found.")
        return

    print("\nAVAILABLE BACKUPS")
    print("-" * 45)

    for index, backup_file in enumerate(backup_files, start=1):

        backup_type = (
            "Encrypted"
            if backup_file.name.endswith(".db.enc")
            else "Historical"
        )

        print(
            f"{index}. {backup_file.name} "
            f"({backup_type})"
        )

    print("-" * 45)

    selection = input(
        "\nEnter the number of the backup to restore: "
    ).strip()

    if not selection.isdigit():
        print("\nInvalid selection. Please enter a number.")
        return

    backup_index = int(selection)

    if backup_index < 1 or backup_index > len(backup_files):
        print("\nInvalid backup selection.")
        return

    selected_backup = backup_files[backup_index - 1]

    print(f"\nSelected backup: {selected_backup.name}")

    destination_filename = input(
        "Enter a name for the restored copy "
        "(example: recovered_database.db): "
    ).strip()

    if not destination_filename:
        print("\nA destination filename is required.")
        return

    if (
        not destination_filename.lower().endswith(".db")
        or "/" in destination_filename
        or "\\" in destination_filename
        or destination_filename in {".", ".."}
    ):
        print("\nEnter a valid destination filename ending in .db.")
        return

    print("\nRESTORATION CONFIRMATION")
    print("-" * 45)
    print(f"Source backup: {selected_backup.name}")
    print(f"Restored copy: {destination_filename}")
    print("Destination folder: backups/restored_copies/")
    print("Live database: Will NOT be changed")

    confirmation = input(
        "\nProceed with restoration? Type YES to confirm: "
    ).strip()

    if confirmation != "YES":
        print("\nRestoration cancelled.")
        return

    restore_database_backup(
        user,
        selected_backup.name,
        destination_filename
    )


# ==========================================
# BACKUP RETENTION MANAGEMENT
# ==========================================

def manage_backup_retention(user):
    """Allow only an Admin to manage backup retention."""

    if user["role"] != "Admin":
        raise PermissionError(
            "Only an Admin can manage backup retention."
        )

    while True:

        print("\nBACKUP RETENTION MANAGEMENT")
        print("=" * 45)
        print("1. Preview backup retention")
        print("2. Clean up expired backups")
        print("3. Return to Admin menu")

        choice = input("\nSelect an option: ").strip()

        if choice == "1":

            preview_backup_cleanup()

        elif choice == "2":

            print("\nBACKUP CLEANUP")
            print("-" * 45)
            print("Only eligible expired backups will be considered.")
            print("Protected backups and the two most recent backups")
            print("will be retained.")

            cleanup_expired_backups(user)

        elif choice == "3":

            print("\nReturning to Admin menu.")
            break

        else:

            print("\nInvalid option. Please try again.")


# ==========================================
# ROLE-BASED MENUS
# ==========================================

def display_admin_menu():

    print("1. Register patient")
    print("2. View patient records")
    print("3. Update clinical record")
    print("4. Update care notes")
    print("5. Report security incident")
    print("6. View security incidents")
    print("7. Update incident status")
    print("8. Register cybersecurity risk")
    print("9. View cybersecurity risk register")
    print("10. Update risk status")
    print("11. View system audit logs")
    print("12. Restore database backup")
    print("13. Manage backup retention")
    print("14. Reset staff MFA")
    print("15. Log out")


def display_doctor_menu():

    print("1. Register patient")
    print("2. View patient records")
    print("3. Update clinical record")
    print("4. Log out")


def display_nurse_menu():

    print("1. View patient records")
    print("2. Update care notes")
    print("3. Log out")


def display_receptionist_menu():

    print("1. Register patient")
    print("2. View basic patient details")
    print("3. Log out")


def display_it_officer_menu():

    print("1. View system audit logs")
    print("2. Create database backup")
    print("3. Log out")


# ==========================================
# LOGOUT AUDIT RECORDING
# ==========================================

def record_session_logout(user, logout_type):
    """Record manual or automatic session termination."""

    if logout_type == "MANUAL":

        action = "SESSION_MANUAL_LOGOUT"
        details = "User manually logged out successfully."

    elif logout_type == "AUTOMATIC":

        action = "SESSION_AUTO_LOGOUT"
        details = (
            "Automatically logged out after "
            "15 minutes of menu inactivity."
        )

    else:
        raise ValueError("Invalid logout type.")

    try:

        record_audit(
            user["user_id"],
            action,
            "Session",
            user["user_id"],
            details
        )

        print("Logout event recorded in the audit log.")

    except Exception as error:

        print(
            "WARNING: Logout occurred, "
            f"but audit logging failed: {error}"
        )


# ==========================================
# APPLICATION SESSION
# ==========================================

def run_session(user):
    """Run the application according to the user's role."""

    role = user["role"]

    menu_choices = {
        "Admin": [str(i) for i in range(1, 16)],
        "Doctor": ["1", "2", "3", "4"],
        "Nurse": ["1", "2", "3"],
        "Receptionist": ["1", "2", "3"],
        "IT Officer": ["1", "2", "3"]
    }

    while True:

        print("\n" + "=" * 50)
        print("HEALTHCARE GOVERNANCE SYSTEM")
        print("=" * 50)

        print(f"Logged in as: {user['full_name']}")
        print(f"Role: {role}")
        print(f"Branch: {user['branch']}")

        print("-" * 50)

        if role == "Admin":
            display_admin_menu()

        elif role == "Doctor":
            display_doctor_menu()

        elif role == "Nurse":
            display_nurse_menu()

        elif role == "Receptionist":
            display_receptionist_menu()

        elif role == "IT Officer":
            display_it_officer_menu()

        else:
            print("Unrecognized role. Access is restricted.")
            break

        choice = get_input_with_timeout(
            "\nSelect an option: ",
            INACTIVITY_TIMEOUT_SECONDS
        )

        # AUTOMATIC LOGOUT AFTER INACTIVITY

        if choice is None:

            record_session_logout(user, "AUTOMATIC")
            break

        choice = choice.strip()

        if choice not in menu_choices[role]:
            print("\nInvalid option. Please try again.")
            continue

        # MANUAL LOGOUT

        if choice == menu_choices[role][-1]:

            record_session_logout(user, "MANUAL")

            print("\nLogging out...")
            print("You have exited your session.")
            break

        try:

            if role == "Admin":

                if choice == "1":
                    register_patient(user)

                elif choice == "2":
                    display_patients(user)

                elif choice == "3":
                    update_clinical(user)

                elif choice == "4":
                    update_care(user)

                elif choice == "5":
                    report_security_incident(user)

                elif choice == "6":
                    view_security_incidents(user)

                elif choice == "7":
                    change_incident_status(user)

                elif choice == "8":
                    register_risk(user)

                elif choice == "9":
                    view_risk_register(user)

                elif choice == "10":
                    change_risk_status(user)

                elif choice == "11":
                    view_audit_logs(user)

                elif choice == "12":
                    restore_database(user)

                elif choice == "13":
                    manage_backup_retention(user)

                elif choice == "14":
                    admin_mfa_recovery(user)

            elif role == "Doctor":

                if choice == "1":
                    register_patient(user)

                elif choice == "2":
                    display_patients(user)

                elif choice == "3":
                    update_clinical(user)

            elif role == "Nurse":

                if choice == "1":
                    display_patients(user)

                elif choice == "2":
                    update_care(user)

            elif role == "Receptionist":

                if choice == "1":
                    register_patient(user)

                elif choice == "2":
                    display_patients(user)

            elif role == "IT Officer":

                if choice == "1":
                    view_audit_logs(user)

                elif choice == "2":
                    create_database_backup(user)

        except PermissionError as error:

            print(f"\nACCESS DENIED: {error}")

        except ValueError as error:

            print(f"\nINVALID INPUT: {error}")

        except sqlite3.IntegrityError:

            print(
                "\nDATABASE ERROR: The operation could not be "
                "completed because of a database constraint."
            )

        except Exception as error:

            print(f"\nAn unexpected error occurred: {error}")


# ==========================================
# MAIN APPLICATION
# ==========================================

def main():
    """Start the healthcare governance application."""

    prepare_application()

    print("\nHEALTHCARE SYSTEM STAFF LOGIN")
    print("=" * 40)

    while True:

        username = input("Username: ").strip()
        password = getpass("Password: ")

        user = authenticate_user(
            username,
            password
        )

        if user:

            print(
                f"\nPassword authentication successful for "
                f"{user['full_name']}."
            )

            mfa_successful = authenticate_with_mfa(user)

            if mfa_successful:

                record_audit(
                    user["user_id"],
                    "Successful login",
                    "User",
                    user["user_id"],
                    (
                        f"Role: {user['role']}; "
                        "Authentication: password and MFA."
                    )
                )

                print("\nAccess granted.")
                print("Authentication completed successfully.")

                run_session(user)
                break

            print("\nACCESS DENIED: MFA verification is required.")
            print("Please try logging in again.\n")
            continue

        print("\nLogin failed. Please check your details.")
        print("Please try again.\n")


if __name__ == "__main__":
    main()
