
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

# Store the database in the project folder
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "healthcare.db"


def get_connection():
    """Create a connection to the healthcare database."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create the database tables if they do not already exist."""

    with get_connection() as connection:

        # 1. Staff accounts
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN (
                        'Admin',
                        'Doctor',
                        'Nurse',
                        'Receptionist',
                        'IT Officer'
                    )
                ),
                branch TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)

        # 2. Patient records
        connection.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_number TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                date_of_birth TEXT,
                gender TEXT,
                phone_number TEXT,
                medical_history TEXT,
                classification TEXT NOT NULL DEFAULT 'CONFIDENTIAL',
                created_by INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        """)

        # 3. Audit logs
        connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                record_type TEXT,
                record_id INTEGER,
                details TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # 4. Security incidents
        connection.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL CHECK (
                    severity IN ('Low', 'Medium', 'High', 'Critical')
                ),
                status TEXT NOT NULL DEFAULT 'Open',
                reported_by INTEGER,
                reported_at TEXT NOT NULL,
                FOREIGN KEY (reported_by) REFERENCES users(user_id)
            )
        """)

        # 5. Cybersecurity risk register
        connection.execute("""
            CREATE TABLE IF NOT EXISTS risks (
                risk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                risk_name TEXT NOT NULL,
                description TEXT NOT NULL,
                likelihood INTEGER NOT NULL CHECK (
                    likelihood BETWEEN 1 AND 5
                ),
                impact INTEGER NOT NULL CHECK (
                    impact BETWEEN 1 AND 5
                ),
                risk_score INTEGER NOT NULL,
                mitigation TEXT,
                status TEXT NOT NULL DEFAULT 'Open'
            )
        """)

        # Improve audit log searching
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_user
            ON audit_logs(user_id)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp
            ON audit_logs(timestamp)
        """)

    print("Healthcare database initialized successfully.")


def record_audit(user_id, action, record_type=None,
                 record_id=None, details=None):
    """Record an activity in the audit log."""

    timestamp = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute("""
            INSERT INTO audit_logs (
                user_id, action, record_type,
                record_id, details, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id, action, record_type,
            record_id, details, timestamp
        ))


if __name__ == "__main__":
    initialize_database()
