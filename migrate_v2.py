"""
APTS Migration V2 - Add Teacher Role, Teacher Profiles, Teacher Assignments
Run once to upgrade the database schema.
"""
import sqlite3
import datetime
import hashlib
import uuid

DB_FILE = "c:/Users/ASUS/OneDrive/Documents/OOTS/portal.db"

def hash_password(password, salt=None):
    if not salt:
        salt = uuid.uuid4().hex
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000
    ).hex()
    return pwd_hash, salt

def migrate():
    conn = sqlite3.connect(DB_FILE, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    cursor = conn.cursor()

    print("[MIGRATE] Starting V2 migration...")

    # Step 1: Check current users table
    cursor.execute("SELECT sql FROM sqlite_master WHERE name='users'")
    current_sql = cursor.fetchone()[0]
    print(f"[MIGRATE] Current users schema: {current_sql[:80]}...")

    # Step 2: Recreate users table to add 'teacher' role + is_active column
    if "'teacher'" not in current_sql or 'is_active' not in current_sql:
        print("[MIGRATE] Recreating users table with teacher role and is_active...")
        cursor.execute("ALTER TABLE users RENAME TO users_old")
        cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'admin', 'teacher')),
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """)
        cursor.execute("""
        INSERT INTO users (id, email, password_hash, salt, role, is_active, created_at)
        SELECT id, email, password_hash, salt, role, 1, created_at
        FROM users_old
        """)
        cursor.execute("DROP TABLE users_old")
        print("[MIGRATE] users table recreated successfully.")
    else:
        print("[MIGRATE] users table already has teacher role. Skipping.")

    # Step 3: Add is_active to student_profiles if missing
    cursor.execute("PRAGMA table_info(student_profiles)")
    sp_cols = [r[1] for r in cursor.fetchall()]
    if 'section' not in sp_cols:
        print("[MIGRATE] Adding section, academic_year to student_profiles...")
        cursor.execute("ALTER TABLE student_profiles ADD COLUMN section TEXT DEFAULT ''")
        cursor.execute("ALTER TABLE student_profiles ADD COLUMN academic_year TEXT DEFAULT '2025-2026'")

    # Step 4: Create teacher_profiles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teacher_profiles (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        faculty_id TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        designation TEXT DEFAULT 'Assistant Professor',
        specialization TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        avatar TEXT DEFAULT '👨‍🏫',
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    print("[MIGRATE] teacher_profiles table ready.")

    # Step 5: Create teacher_assignments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teacher_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        project_id TEXT,
        assigned_by INTEGER NOT NULL,
        deadline TEXT,
        status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Completed', 'Revoked')),
        notes TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        FOREIGN KEY(teacher_id) REFERENCES users(id),
        FOREIGN KEY(student_id) REFERENCES users(id),
        FOREIGN KEY(project_id) REFERENCES projects(id),
        FOREIGN KEY(assigned_by) REFERENCES users(id)
    )
    """)
    print("[MIGRATE] teacher_assignments table ready.")

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")

    # Step 6: Seed a demo teacher account
    cursor.execute("SELECT id FROM users WHERE email = 'teacher@univ.edu'")
    if not cursor.fetchone():
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        pwd_hash, salt = hash_password("Teacher@2026!")
        cursor.execute(
            "INSERT INTO users (email, password_hash, salt, role, is_active, created_at) VALUES (?, ?, ?, 'teacher', 1, ?)",
            ("teacher@univ.edu", pwd_hash, salt, now)
        )
        teacher_uid = cursor.lastrowid
        cursor.execute(
            """INSERT INTO teacher_profiles (user_id, full_name, faculty_id, department, designation, specialization)
               VALUES (?, 'Dr. Priya Sharma', 'FAC-2026-001', 'Computer Science & Engineering', 'Associate Professor', 'Machine Learning & Distributed Systems')""",
            (teacher_uid,)
        )
        print(f"[MIGRATE] Demo teacher created: teacher@univ.edu / Teacher@2026! (ID: {teacher_uid})")
        conn.commit()

    # Also seed a second demo teacher
    cursor.execute("SELECT id FROM users WHERE email = 'faculty@univ.edu'")
    if not cursor.fetchone():
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        pwd_hash, salt = hash_password("Teacher@2026!")
        cursor.execute(
            "INSERT INTO users (email, password_hash, salt, role, is_active, created_at) VALUES (?, ?, ?, 'teacher', 1, ?)",
            ("faculty@univ.edu", pwd_hash, salt, now)
        )
        teacher_uid2 = cursor.lastrowid
        cursor.execute(
            """INSERT INTO teacher_profiles (user_id, full_name, faculty_id, department, designation, specialization)
               VALUES (?, 'Prof. Arjun Reddy', 'FAC-2026-002', 'Information Technology', 'Assistant Professor', 'Computer Architecture & VLSI')""",
            (teacher_uid2,)
        )
        print(f"[MIGRATE] Demo teacher 2 created: faculty@univ.edu / Teacher@2026! (ID: {teacher_uid2})")
        conn.commit()

    conn.close()
    print("[MIGRATE] V2 migration complete!")
    print("  Demo teacher accounts:")
    print("    teacher@univ.edu   / Teacher@2026!")
    print("    faculty@univ.edu   / Teacher@2026!")
    print("  Admin accounts:")
    print("    admin@univ.edu     / Admin@2026!")

if __name__ == '__main__':
    migrate()

