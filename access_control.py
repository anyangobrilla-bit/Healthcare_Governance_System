
# Healthcare Role-Based Access Control (RBAC)

from database import record_audit


# 1. DEFINE PERMISSIONS FOR EACH STAFF ROLE

ROLE_PERMISSIONS = {
    "Admin": {
        "user.create",
        "user.view",
        "user.deactivate",
        "patient.view",
        "patient.view_basic",
        "patient.create",
        "patient.update_clinical",
        "patient.update_care",
        "audit.view",
        "incident.manage",
        "risk.manage",
        "backup.manage",
        "system.manage",
        "compliance.manage"
    },

    "Doctor": {
        "patient.view",
        "patient.create",
        "patient.update_clinical"
    },

    "Nurse": {
        "patient.view",
        "patient.update_care"
    },

    "Receptionist": {
        "patient.view_basic",
        "patient.create"
    },

    "IT Officer": {
        "audit.view",
        "backup.manage",
        "system.manage"
    }
}


# 2. GET PERMISSIONS ASSIGNED TO A ROLE

def get_permissions(role):
    """Return permissions assigned to a staff role."""

    return ROLE_PERMISSIONS.get(role, set())


# 3. CHECK WHETHER A USER HAS A PERMISSION

def has_permission(user, permission):
    """Check whether a logged-in user has permission."""

    if not user:
        return False

    role = user.get("role")

    if role not in ROLE_PERMISSIONS:
        return False

    return permission in get_permissions(role)


# 4. ENFORCE PERMISSIONS AND RECORD DENIED ATTEMPTS

def require_permission(user, permission):
    """Deny unauthorized actions and record them in audit logs."""

    if not has_permission(user, permission):

        user_id = user.get("user_id") if user else None
        role = user.get("role", "Unknown") if user else "Unknown"

        record_audit(
            user_id,
            "ACCESS_DENIED",
            "Permission",
            None,
            f"Role: {role}; Attempted permission: {permission}"
        )

        raise PermissionError(
            f"ACCESS DENIED: You do not have permission "
            f"to perform '{permission}'."
        )

    return True


# 5. DISPLAY PERMISSIONS FOR A STAFF ROLE

def display_permissions(role):
    """Display permissions assigned to a role."""

    permissions = get_permissions(role)

    print(f"\nROLE: {role}")
    print("-" * 40)

    if not permissions:
        print("No permissions assigned.")
        return

    for permission in sorted(permissions):
        print(f"PASS: {permission}")


# 6. TEST ROLE-BASED ACCESS CONTROL

if __name__ == "__main__":

    print("HEALTHCARE ACCESS CONTROL TEST")
    print("=" * 45)

    doctor = {
        "user_id": 2,
        "username": "doctor1",
        "role": "Doctor"
    }

    nurse = {
        "user_id": 3,
        "username": "nurse1",
        "role": "Nurse"
    }

    receptionist = {
        "user_id": 4,
        "username": "reception1",
        "role": "Receptionist"
    }

    it_officer = {
        "user_id": 5,
        "username": "it1",
        "role": "IT Officer"
    }

    admin = {
        "user_id": 1,
        "username": "healthadmin",
        "role": "Admin"
    }

    # DOCTOR TESTS
    print("\n1. DOCTOR ACCESS")

    print(
        "View patient records:",
        has_permission(doctor, "patient.view")
    )

    print(
        "View audit logs:",
        has_permission(doctor, "audit.view")
    )

    # NURSE TESTS
    print("\n2. NURSE ACCESS")

    print(
        "View patient records:",
        has_permission(nurse, "patient.view")
    )

    print(
        "Update clinical diagnosis:",
        has_permission(nurse, "patient.update_clinical")
    )

    # RECEPTIONIST TESTS
    print("\n3. RECEPTIONIST ACCESS")

    print(
        "View basic patient details:",
        has_permission(receptionist, "patient.view_basic")
    )

    print(
        "View medical records:",
        has_permission(receptionist, "patient.view")
    )

    # IT OFFICER TESTS
    print("\n4. IT OFFICER ACCESS")

    print(
        "Manage backups:",
        has_permission(it_officer, "backup.manage")
    )

    print(
        "View patient records:",
        has_permission(it_officer, "patient.view")
    )

    # ADMINISTRATOR TESTS
    print("\n5. ADMINISTRATOR ACCESS")

    print(
        "Manage incidents:",
        has_permission(admin, "incident.manage")
    )

    print(
        "Manage compliance:",
        has_permission(admin, "compliance.manage")
    )

    print("\nACCESS CONTROL TEST COMPLETED.")
