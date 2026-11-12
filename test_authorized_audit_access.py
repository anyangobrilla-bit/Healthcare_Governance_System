from it_management import view_audit_logs

it_officer = {
    "user_id": 5,
    "role": "IT Officer",
    "branch": "Nairobi Main Branch"
}

print("=" * 60)
print("AUTHORISED AUDIT LOG ACCESS TEST")
print("=" * 60)

try:
    view_audit_logs(it_officer)

    print("\nPASS: IT Officer successfully accessed audit logs.")

except PermissionError as error:
    print("\nFAIL: IT Officer was denied access.")
    print("Reason:", error)