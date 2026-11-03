"""
APTS - Academic Project Tracking & Evaluation System
Production Backend Server & Database Engine
Author: Senior Full-Stack Security & Database Engineer
Built with Python 3, SQLite3, Native HTTP Server, PBKDF2-HMAC-SHA256, and Role-Based Access Control.
"""

import http.server
import socketserver
import os
import sys
import json
import sqlite3
import hashlib
import hmac
import uuid
import datetime
import urllib.parse
import mimetypes
import csv
import io

PORT = 3000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "portal.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==============================================================================
# DATABASE ARCHITECTURE & SCHEMA INITIALIZATION
# ==============================================================================

def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(password: str, salt: str = None) -> tuple:
    if not salt:
        salt = uuid.uuid4().hex
    # PBKDF2 HMAC SHA-256 with 100,000 iterations for secure password storage
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return pwd_hash, salt

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    pwd_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(pwd_hash, expected_hash)

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'admin', 'teacher')),
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    )
    """)

    # 2. Student Profiles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_profiles (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        enrollment_no TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        branch TEXT NOT NULL,
        semester INTEGER NOT NULL,
        phone TEXT,
        avatar TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 3. Projects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        student_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        abstract TEXT NOT NULL,
        problem_statement TEXT NOT NULL,
        objectives TEXT NOT NULL,
        technologies TEXT NOT NULL,
        team_members TEXT,
        repo_url TEXT,
        live_url TEXT,
        doc_file TEXT,
        presentation_file TEXT,
        additional_files TEXT,
        status TEXT NOT NULL DEFAULT 'Submitted' CHECK(status IN ('Draft', 'Submitted', 'Under Review', 'Changes Requested', 'Resubmitted', 'Approved', 'Rejected', 'Graded')),
        is_draft INTEGER NOT NULL DEFAULT 0,
        submission_version INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 4. Project Status History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        from_status TEXT,
        to_status TEXT NOT NULL,
        changed_by_user_id INTEGER NOT NULL,
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY(changed_by_user_id) REFERENCES users(id)
    )
    """)

    # 5. Evaluations & 100-Mark Rubric Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT UNIQUE NOT NULL,
        evaluated_by_user_id INTEGER NOT NULL,
        problem_statement_score REAL DEFAULT 0,
        implementation_score REAL DEFAULT 0,
        innovation_score REAL DEFAULT 0,
        documentation_score REAL DEFAULT 0,
        ui_ux_score REAL DEFAULT 0,
        presentation_score REAL DEFAULT 0,
        completeness_score REAL DEFAULT 0,
        total_score REAL DEFAULT 0,
        grade TEXT,
        overall_feedback TEXT,
        strengths TEXT,
        weaknesses TEXT,
        missing_features TEXT,
        technical_issues TEXT,
        documentation_issues TEXT,
        recommended_improvements TEXT,
        is_published INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY(evaluated_by_user_id) REFERENCES users(id)
    )
    """)

    # 6. Notifications Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT DEFAULT 'info',
        link TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 7. Active Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 8. Project Versions Table (Provenance & Revision History)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        version_number INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT,
        abstract TEXT,
        problem_statement TEXT,
        objectives TEXT,
        technologies TEXT,
        team_members TEXT,
        repo_url TEXT,
        live_url TEXT,
        doc_file TEXT,
        presentation_file TEXT,
        additional_files TEXT,
        changelog TEXT,
        submitted_at TEXT NOT NULL,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    )
    """)

    # 9. Teacher Profiles Table
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

    # 10. Teacher Assignments Table
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

    # 11. Institution Settings Table (College Configuration & Rubrics)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS institution_settings (
        id INTEGER PRIMARY KEY,
        college_name TEXT NOT NULL,
        logo_url TEXT,
        department TEXT NOT NULL,
        program TEXT NOT NULL,
        academic_year TEXT NOT NULL,
        semester INTEGER NOT NULL,
        session TEXT NOT NULL,
        project_title TEXT,
        submission_deadline TEXT NOT NULL,
        supervisor_name TEXT,
        evaluator_name TEXT,
        rubric_json TEXT NOT NULL,
        grade_scale_json TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    conn.commit()

    # Seed Default Institution Settings if not present
    cursor.execute("SELECT COUNT(*) FROM institution_settings WHERE id = 1")
    if cursor.fetchone()[0] == 0:
        default_rubric = json.dumps([
            {"key": "problem_statement", "name": "Problem Statement & Relevance", "max": 15, "weight": "15%"},
            {"key": "implementation", "name": "System Architecture & Implementation", "max": 25, "weight": "25%"},
            {"key": "innovation", "name": "Technical Innovation & Complexity", "max": 15, "weight": "15%"},
            {"key": "documentation", "name": "Project Documentation & Report", "max": 15, "weight": "15%"},
            {"key": "ui_ux", "name": "UI/UX & Engineering Usability", "max": 10, "weight": "10%"},
            {"key": "presentation", "name": "Viva Voce & Technical Defense", "max": 10, "weight": "10%"},
            {"key": "completeness", "name": "Testing & Deliverable Completeness", "max": 10, "weight": "10%"}
        ])
        default_grade_scale = json.dumps([
            {"grade": "A+", "min": 90, "max": 100, "remark": "Outstanding / Honors"},
            {"grade": "A", "min": 80, "max": 89.9, "remark": "Excellent"},
            {"grade": "B+", "min": 70, "max": 79.9, "remark": "Very Good"},
            {"grade": "B", "min": 60, "max": 69.9, "remark": "Good"},
            {"grade": "C", "min": 50, "max": 59.9, "remark": "Pass"},
            {"grade": "F", "min": 0, "max": 49.9, "remark": "Requires Major Re-submission"}
        ])
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
        INSERT INTO institution_settings (
            id, college_name, logo_url, department, program, academic_year,
            semester, session, project_title, submission_deadline,
            supervisor_name, evaluator_name, rubric_json, grade_scale_json, updated_at
        ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Faculty of Engineering & Technology",
            "",
            "Computer Science & Engineering",
            "B.Tech Computer Science & Engineering",
            "2025-2026",
            6,
            "Spring 2026 (Batch 2023-2027)",
            "Undergraduate Major Capstone Evaluation",
            "2026-05-15T23:59:59Z",
            "Dr. Rajesh K. Sharma, Professor",
            "Dr. Anjali Gupta, External Evaluator",
            default_rubric,
            default_grade_scale,
            now
        ))

    # Seed Default Administrator Accounts if not present
    for admin_email in ["admin@univ.edu", "admin@university.edu"]:
        cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
        if not cursor.fetchone():
            admin_pwd = "Admin@2026!"
            pwd_hash, salt = hash_password(admin_pwd)
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cursor.execute(
                "INSERT INTO users (email, password_hash, salt, role, created_at) VALUES (?, ?, ?, 'admin', ?)",
                (admin_email, pwd_hash, salt, now)
            )
            print(f"[AUTH] Admin created: {admin_email} / {admin_pwd}")

    # Seed Demo Student Accounts & Realistic Capstones if empty
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
    student_count = cursor.fetchone()['count']
    if student_count == 0:
        seed_demo_data(cursor)

    conn.commit()
    conn.close()
    print("[DATABASE] Schema verified and database ready.")

def seed_demo_data(cursor):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    students = [
        {
            "email": "aarav.patel@student.univ.edu",
            "name": "Aarav Patel",
            "enr": "21CS042",
            "dept": "Computer Science & Engineering",
            "branch": "Systems & Architecture",
            "sem": 6
        },
        {
            "email": "sneha.nair@student.univ.edu",
            "name": "Sneha Nair",
            "enr": "21CS089",
            "dept": "Computer Science & Engineering",
            "branch": "High Performance Computing",
            "sem": 6
        },
        {
            "email": "vikram.malhotra@student.univ.edu",
            "name": "Vikram Malhotra",
            "enr": "21IT015",
            "dept": "Information Technology",
            "branch": "Computer Systems",
            "sem": 6
        }
    ]

    student_user_ids = []
    for s in students:
        pwd_hash, salt = hash_password("Student@2026!")
        cursor.execute(
            "INSERT INTO users (email, password_hash, salt, role, created_at) VALUES (?, ?, ?, 'student', ?)",
            (s['email'], pwd_hash, salt, now)
        )
        uid = cursor.lastrowid
        student_user_ids.append(uid)
        cursor.execute(
            """INSERT INTO student_profiles 
               (user_id, full_name, enrollment_no, department, branch, semester, phone, avatar)
               VALUES (?, ?, ?, ?, ?, ?, '9876543210', '👨‍🎓')""",
            (uid, s['name'], s['enr'], s['dept'], s['branch'], s['sem'])
        )

    # Seed Initial Capstones
    projects = [
        {
            "id": "PRJ-2026-001",
            "student_id": student_user_ids[0],
            "title": "Multi-Core RISC-V Processor with MESI Cache Coherence Protocol",
            "category": "Computer Architecture & Parallel Systems",
            "abstract": "A synthesizable dual-core RV32I micro-architecture with 5-stage pipeline, hazard forwarding unit, and snoop-based MESI shared bus cache controller.",
            "problem": "Standard simulator-based student micro-architecture projects lack cycle-accurate cache coherence hardware verification on multi-core topologies.",
            "objectives": "1. Design 5-stage RV32I pipeline\n2. Integrate data forwarding\n3. Implement 4-state MESI snooping protocol on shared memory bus.",
            "technologies": "Verilog HDL, GTKWave, C++, RISC-V Toolchain, Python",
            "members": "Aarav Patel (Lead), Pooja Mehta, Karan Singhania",
            "repo": "https://github.com/cse-batch2026/multi-core-risc-mesi",
            "live": "https://riscv-mesi.univ.edu",
            "status": "Under Review"
        },
        {
            "id": "PRJ-2026-002",
            "student_id": student_user_ids[1],
            "title": "Scalable CC-NUMA Shared Memory System with Directory Coherence",
            "category": "High Performance Computing & Networks",
            "abstract": "CC-NUMA directory architecture modeled after SGI Origin, implementing memory-based directory bitmasks, LL-SC barriers, and 2D Torus interconnect routing.",
            "problem": "Snooping bus protocols fail to scale beyond 16 cores due to broadcast bandwidth saturation on single shared buses.",
            "objectives": "1. Implement point-to-point directory bitmask\n2. Enforce sequential consistency\n3. Benchmark 2D Mesh vs Torus wormhole routing latency.",
            "technologies": "SystemC, C++20, MPI, Verilator, Gem5",
            "members": "Sneha Nair (Lead), Rohan Das",
            "repo": "https://github.com/cse-batch2026/numa-origin-directory",
            "live": "https://numa-origin.univ.edu",
            "status": "Graded"
        },
        {
            "id": "PRJ-2026-003",
            "student_id": student_user_ids[2],
            "title": "High-Throughput IEEE 754 Floating-Point ALU with Booth Multiplier",
            "category": "Digital Electronics & VLSI",
            "abstract": "Synthesizable ALU supporting 32-bit single precision IEEE 754 floating point arithmetic, signed Booth's multiplier, and array divider.",
            "problem": "Floating-point division and signed multiplication introduce severe multi-cycle latency bottlenecks in scientific computing processors.",
            "objectives": "1. Design radix-4 Booth recoding array\n2. Support IEEE 754 denormalized numbers\n3. Optimize power with clock gating.",
            "technologies": "VHDL, ModelSim, Xilinx Vivado, Python",
            "members": "Vikram Malhotra (Lead), Ananya Sen",
            "repo": "https://github.com/cse-batch2026/fp-alu-booth",
            "live": "https://alu-booth.univ.edu",
            "status": "Changes Requested"
        }
    ]

    for p in projects:
        cursor.execute("""
            INSERT INTO projects (
                id, student_id, title, category, abstract, problem_statement,
                objectives, technologies, team_members, repo_url, live_url,
                doc_file, presentation_file, additional_files, status, is_draft,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'doc_spec.pdf', 'presentation.pptx', '', ?, 0, ?, ?)
        """, (
            p['id'], p['student_id'], p['title'], p['category'], p['abstract'],
            p['problem'], p['objectives'], p['technologies'], p['members'],
            p['repo'], p['live'], p['status'], now, now
        ))

        # Status History
        cursor.execute("""
            INSERT INTO project_status_history (
                project_id, from_status, to_status, changed_by_user_id, notes, created_at
            ) VALUES (?, 'Draft', 'Submitted', ?, 'Initial capstone submission completed.', ?)
        """, (p['id'], p['student_id'], now))

        if p['status'] in ['Under Review', 'Changes Requested', 'Graded']:
            cursor.execute("""
                INSERT INTO project_status_history (
                    project_id, from_status, to_status, changed_by_user_id, notes, created_at
                ) VALUES (?, 'Submitted', 'Under Review', 1, 'Faculty committee commenced technical evaluation.', ?)
            """, (p['id'], now))

        if p['status'] == 'Changes Requested':
            cursor.execute("""
                INSERT INTO project_status_history (
                    project_id, from_status, to_status, changed_by_user_id, notes, created_at
                ) VALUES (?, 'Under Review', 'Changes Requested', 1, 'Corner cases with -128 overflow in Booth recoding table require resolution.', ?)
            """, (p['id'], now))

        if p['status'] == 'Graded':
            cursor.execute("""
                INSERT INTO project_status_history (
                    project_id, from_status, to_status, changed_by_user_id, notes, created_at
                ) VALUES (?, 'Under Review', 'Approved', 1, 'All verification testbenches verified.', ?)
            """, (p['id'], now))
            cursor.execute("""
                INSERT INTO project_status_history (
                    project_id, from_status, to_status, changed_by_user_id, notes, created_at
                ) VALUES (?, 'Approved', 'Graded', 1, 'Final Viva Voce evaluation complete and published.', ?)
            """, (p['id'], now))

            # Seed Published Evaluation for PRJ-2026-002
            cursor.execute("""
                INSERT INTO evaluations (
                    project_id, evaluated_by_user_id,
                    problem_statement_score, implementation_score, innovation_score,
                    documentation_score, ui_ux_score, presentation_score, completeness_score,
                    total_score, grade, overall_feedback, strengths, weaknesses,
                    missing_features, recommended_improvements, is_published, created_at, updated_at
                ) VALUES (
                    ?, 1,
                    15.0, 24.5, 14.5, 14.0, 9.5, 9.5, 9.5,
                    96.5, 'A+',
                    'Exemplary CC-NUMA implementation. The directory bitmask synchronization matches IEEE industrial standards.',
                    'Rigorous memory consistency verification, robust 2D Torus interconnect simulator.',
                    'Minor simulation runtime overhead on high thread counts.',
                    'None for undergraduate capstone scope.',
                    'Consider exploring relaxed consistency release consistency models.',
                    1, ?, ?
                )
            """, (p['id'], now, now))

    # Seed Notifications
    cursor.execute("""
        INSERT INTO notifications (user_id, title, message, type, link, created_at)
        VALUES (?, 'Welcome to APTS', 'Your student account is active. You can now submit and track capstone projects.', 'info', '#/dashboard', ?)
    """, (student_user_ids[0], now))

    cursor.execute("""
        INSERT INTO notifications (user_id, title, message, type, link, created_at)
        VALUES (?, 'Project Review Commenced', 'Dr. V. K. Sharma has started evaluating your Multi-Core RISC-V capstone (PRJ-2026-001).', 'status', '#/tracking', ?)
    """, (student_user_ids[0], now))

    cursor.execute("""
        INSERT INTO notifications (user_id, title, message, type, link, created_at)
        VALUES (?, 'Final Grade Published', 'Congratulations! Your capstone PRJ-2026-002 has been evaluated with Grade A+ (96.5/100).', 'grade', '#/feedback', ?)
    """, (student_user_ids[1], now))


# ==============================================================================
# HTTP REQUEST HANDLER & REST API ROUTER
# ==============================================================================

class APTSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def send_json(self, data, status_code=200):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status_code=400):
        self.send_json({"success": False, "error": message}, status_code=status_code)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.end_headers()

    def get_auth_user(self):
        auth_header = self.headers.get('Authorization', '')
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
        else:
            cookie_header = self.headers.get('Cookie', '')
            for cookie in cookie_header.split(';'):
                if 'apts_token=' in cookie:
                    token = cookie.split('apts_token=')[1].strip()

        if not token:
            try:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                if 'token' in qs and qs['token']:
                    token = qs['token'][0].strip()
            except Exception:
                pass

        if not token:
            return None

        conn = get_db()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute(
            """SELECT s.token, s.role, u.id, u.email, sp.full_name, sp.enrollment_no, sp.department, sp.branch, sp.semester
               FROM sessions s
               JOIN users u ON s.user_id = u.id
               LEFT JOIN student_profiles sp ON u.id = sp.user_id
               WHERE s.token = ? AND s.expires_at > ?""",
            (token, now)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length <= 0:
            return {}
        raw_body = self.rfile.read(content_length).decode('utf-8')
        try:
            return json.loads(raw_body)
        except Exception:
            return {}

    # ==========================================================================
    # GET ROUTER
    # ==========================================================================
    def do_GET(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path
        query = urllib.parse.parse_qs(url_parsed.query)

        # 1. API Routes
        if path.startswith('/api/'):
            self.handle_api_get(path, query)
            return

        # 2. Static File Serving with Safe Fallback to index.html for SPA routes
        requested_file = os.path.join(BASE_DIR, path.lstrip('/'))
        if os.path.isfile(requested_file):
            return super().do_GET()
        else:
            # SPA Fallback: serve index.html for HTML requests
            self.path = '/index.html'
            return super().do_GET()

    def handle_api_get(self, path, query):
        user = self.get_auth_user()

        # Auth state check
        if path == '/api/auth/me':
            if not user:
                return self.send_error_json("Unauthenticated", 401)
            return self.send_json({"success": True, "user": user})

        # Institution Configuration (Public & Authenticated)
        if path == '/api/institution/settings':
            return self.api_get_institution_settings()

        # --- STUDENT ENDPOINTS ---
        if path == '/api/student/dashboard':
            if not user or user['role'] != 'student':
                return self.send_error_json("Access restricted to authenticated students", 403)
            return self.api_student_dashboard(user['id'])

        if path == '/api/student/projects':
            if not user or user['role'] != 'student':
                return self.send_error_json("Access restricted to authenticated students", 403)
            return self.api_student_list_projects(user['id'])

        if path.startswith('/api/student/projects/') and path.endswith('/tracking'):
            project_id = path.split('/')[4]
            if not user or user['role'] != 'student':
                return self.send_error_json("Unauthorized", 403)
            return self.api_student_project_tracking(project_id, user['id'])

        if path.startswith('/api/student/projects/'):
            project_id = path.split('/')[4]
            if not user or user['role'] != 'student':
                return self.send_error_json("Unauthorized", 403)
            return self.api_student_get_project(project_id, user['id'])

        if path == '/api/student/notifications':
            if not user:
                return self.send_error_json("Unauthorized", 401)
            return self.api_get_notifications(user['id'])

        # --- ADMIN ENDPOINTS ---
        if path == '/api/admin/dashboard':
            if not user or user['role'] != 'admin':
                return self.send_error_json("Access restricted to Faculty Administrators", 403)
            return self.api_admin_dashboard()

        if path == '/api/admin/projects':
            if not user or user['role'] != 'admin':
                return self.send_error_json("Access restricted to Faculty Administrators", 403)
            status_filter = query.get('status', [None])[0]
            search_query = query.get('search', [None])[0]
            return self.api_admin_list_projects(status_filter, search_query)

        if path.startswith('/api/admin/projects/'):
            project_id = path.split('/')[4]
            if not user or user['role'] != 'admin':
                return self.send_error_json("Access restricted to Faculty Administrators", 403)
            return self.api_admin_get_project(project_id)

        if path == '/api/admin/students':
            if not user or user['role'] != 'admin':
                return self.send_error_json("Access restricted to Faculty Administrators", 403)
            return self.api_admin_list_students()

        if path.startswith('/api/admin/students/'):
            if not user or user['role'] != 'admin':
                return self.send_error_json("Access restricted to Faculty Administrators", 403)
            student_id = path.split('/')[4]
            return self.api_admin_get_student(student_id)

        if path == '/api/admin/teachers':
            if not user or user['role'] != 'admin':
                return self.send_error_json("Access restricted to Faculty Administrators", 403)
            return self.api_admin_list_teachers()

        if path.startswith('/api/admin/teachers/'):
            if not user or user['role'] != 'admin':
                return self.send_error_json("Access restricted to Faculty Administrators", 403)
            teacher_id = path.split('/')[4]
            return self.api_admin_get_teacher(teacher_id)

        if path == '/api/admin/assignments':
            if not user or user['role'] != 'admin':
                return self.send_error_json("Access restricted to Faculty Administrators", 403)
            return self.api_admin_list_assignments()

        # --- TEACHER ENDPOINTS ---
        if path == '/api/teacher/dashboard':
            if not user or user['role'] != 'teacher':
                return self.send_error_json("Access restricted to Faculty", 403)
            return self.api_teacher_dashboard(user['id'])

        if path == '/api/teacher/students':
            if not user or user['role'] != 'teacher':
                return self.send_error_json("Access restricted to Faculty", 403)
            return self.api_teacher_list_students(user['id'])

        if path == '/api/teacher/projects':
            if not user or user['role'] != 'teacher':
                return self.send_error_json("Access restricted to Faculty", 403)
            status_filter = query.get('status', [None])[0]
            return self.api_teacher_list_projects(user['id'], status_filter)

        if path.startswith('/api/teacher/projects/') and path.endswith('/tracking'):
            project_id = path.split('/')[4]
            if not user or user['role'] != 'teacher':
                return self.send_error_json("Unauthorized", 403)
            return self.api_admin_get_project(project_id)

        if path.startswith('/api/teacher/projects/'):
            project_id = path.split('/')[4]
            if not user or user['role'] != 'teacher':
                return self.send_error_json("Unauthorized", 403)
            return self.api_teacher_get_project(project_id, user['id'])

        if path == '/api/teacher/notifications':
            if not user or user['role'] != 'teacher':
                return self.send_error_json("Unauthorized", 401)
            return self.api_get_notifications(user['id'])

        if path == '/api/teacher/profile':
            if not user or user['role'] != 'teacher':
                return self.send_error_json("Unauthorized", 401)
            return self.api_teacher_get_profile(user['id'])

        if path == '/api/admin/analytics':
            if not user or user['role'] != 'admin':
                return self.send_error_json("Access restricted to Faculty Administrators", 403)
            return self.api_admin_analytics(query)

        if path in ['/api/admin/export', '/api/admin/export/csv']:
            if not user or user['role'] != 'admin':
                return self.send_error_json("Access restricted to Faculty Administrators", 403)
            return self.api_admin_export_csv()

        return self.send_error_json("Endpoint not found", 404)

    # ==========================================================================
    # POST ROUTER
    # ==========================================================================
    def do_POST(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path

        if not path.startswith('/api/'):
            return self.send_error_json("Not found", 404)

        user = self.get_auth_user()
        body = self.read_json_body()

        # Public Auth Endpoints
        if path == '/api/auth/register':
            return self.api_auth_register(body)

        if path == '/api/auth/login':
            return self.api_auth_login(body)

        if path == '/api/auth/logout':
            return self.api_auth_logout()

        # Student Endpoints
        if path == '/api/student/projects':
            if not user or user['role'] != 'student':
                return self.send_error_json("Access restricted to authenticated students", 403)
            return self.api_student_submit_project(user['id'], body)

        if path.startswith('/api/student/projects/') and path.endswith('/resubmit'):
            project_id = path.split('/')[4]
            if not user or user['role'] != 'student':
                return self.send_error_json("Access restricted to authenticated students", 403)
            return self.api_student_resubmit_project(project_id, user['id'], body)

        if path == '/api/student/notifications/read':
            if not user:
                return self.send_error_json("Unauthorized", 401)
            return self.api_mark_notifications_read(user['id'], body)

        # Admin Endpoints
        if path == '/api/admin/institution/settings':
            if not user or user['role'] != 'admin':
                return self.send_error_json("Access restricted to Faculty Administrators", 403)
            return self.api_admin_update_institution_settings(body)

        if path.startswith('/api/admin/projects/') and path.endswith('/status'):
            project_id = path.split('/')[4]
            if not user or user['role'] != 'admin':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_update_status(project_id, user['id'], body)

        if path.startswith('/api/admin/projects/') and path.endswith('/evaluate'):
            project_id = path.split('/')[4]
            if not user or user['role'] != 'admin':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_evaluate_project(project_id, user['id'], body)

        # Admin student management
        if path == '/api/admin/students':
            if not user or user['role'] != 'admin':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_create_student(body)

        if path.startswith('/api/admin/students/') and path.endswith('/status'):
            student_id = path.split('/')[4]
            if not user or user['role'] != 'admin':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_update_student_status(student_id, body)

        if path.startswith('/api/admin/students/') and path.endswith('/reset-password'):
            student_id = path.split('/')[4]
            if not user or user['role'] != 'admin':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_reset_user_password(student_id, body)

        if path.startswith('/api/admin/students/') and path.endswith('/edit'):
            student_id = path.split('/')[4]
            if not user or user['role'] != 'admin':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_edit_student(student_id, body)

        # Admin teacher management
        if path == '/api/admin/teachers':
            if not user or user['role'] != 'admin':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_create_teacher(body)

        if path.startswith('/api/admin/teachers/') and path.endswith('/status'):
            teacher_id = path.split('/')[4]
            if not user or user['role'] != 'admin':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_update_teacher_status(teacher_id, body)

        if path.startswith('/api/admin/teachers/') and path.endswith('/reset-password'):
            teacher_id = path.split('/')[4]
            if not user or user['role'] != 'admin':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_reset_user_password(teacher_id, body)

        if path.startswith('/api/admin/teachers/') and path.endswith('/edit'):
            teacher_id = path.split('/')[4]
            if not user or user['role'] != 'admin':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_edit_teacher(teacher_id, body)

        # Admin assignments
        if path == '/api/admin/assignments':
            if not user or user['role'] != 'admin':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_create_assignment(user['id'], body)

        if path.startswith('/api/admin/assignments/') and path.endswith('/revoke'):
            assign_id = path.split('/')[4]
            if not user or user['role'] != 'admin':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_revoke_assignment(assign_id)

        # Teacher endpoints
        if path.startswith('/api/teacher/projects/') and path.endswith('/status'):
            project_id = path.split('/')[4]
            if not user or user['role'] != 'teacher':
                return self.send_error_json("Forbidden", 403)
            return self.api_teacher_update_project_status(project_id, user['id'], body)

        if path.startswith('/api/teacher/projects/') and path.endswith('/evaluate'):
            project_id = path.split('/')[4]
            if not user or user['role'] != 'teacher':
                return self.send_error_json("Forbidden", 403)
            return self.api_admin_evaluate_project(project_id, user['id'], body)

        if path == '/api/upload':
            if not user:
                return self.send_error_json("Unauthorized", 401)
            return self.api_handle_file_upload(body)

        return self.send_error_json("POST endpoint not found", 404)

    # ==========================================================================
    # PUT ROUTER
    # ==========================================================================
    def do_PUT(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path
        user = self.get_auth_user()
        body = self.read_json_body()

        if path.startswith('/api/student/projects/'):
            project_id = path.split('/')[4]
            if not user or user['role'] != 'student':
                return self.send_error_json("Unauthorized", 403)
            return self.api_student_update_project(project_id, user['id'], body)

        return self.send_error_json("PUT endpoint not found", 404)

    # ==========================================================================
    # AUTHENTICATION BUSINESS LOGIC
    # ==========================================================================
    def api_auth_register(self, data):
        full_name = data.get('full_name', '').strip()
        enrollment_no = data.get('enrollment_no', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        department = data.get('department', '').strip()
        branch = data.get('branch', '').strip()
        semester = int(data.get('semester', 6))

        # Rigorous input validations
        if not full_name or not enrollment_no or not email or not password:
            return self.send_error_json("All required fields must be provided")

        if '@' not in email or '.' not in email:
            return self.send_error_json("Please provide a valid college email address")

        if len(password) < 6:
            return self.send_error_json("Password must be at least 6 characters long")

        if password != confirm_password:
            return self.send_error_json("Passwords do not match")

        conn = get_db()
        cursor = conn.cursor()

        # Check existing email or enrollment
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return self.send_error_json("An account with this email already exists")

        cursor.execute("SELECT user_id FROM student_profiles WHERE enrollment_no = ?", (enrollment_no,))
        if cursor.fetchone():
            conn.close()
            return self.send_error_json("An account with this enrollment number already exists")

        pwd_hash, salt = hash_password(password)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute(
            "INSERT INTO users (email, password_hash, salt, role, created_at) VALUES (?, ?, ?, 'student', ?)",
            (email, pwd_hash, salt, now)
        )
        user_id = cursor.lastrowid

        cursor.execute(
            """INSERT INTO student_profiles 
               (user_id, full_name, enrollment_no, department, branch, semester, phone, avatar)
               VALUES (?, ?, ?, ?, ?, ?, ?, '👨‍🎓')""",
            (user_id, full_name, enrollment_no, department, branch, semester, data.get('phone', ''))
        )

        # Welcome notification
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, link, created_at)
            VALUES (?, 'Account Registered Successfully', 'Welcome to the Academic Project Tracking System. You can now submit your capstone projects.', 'info', '#/dashboard', ?)
        """, (user_id, now))

        # Generate active session token
        token = uuid.uuid4().hex
        expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat()
        cursor.execute(
            "INSERT INTO sessions (token, user_id, role, created_at, expires_at) VALUES (?, ?, 'student', ?, ?)",
            (token, user_id, now, expires_at)
        )

        conn.commit()
        conn.close()

        user_info = {
            "id": user_id,
            "email": email,
            "role": "student",
            "full_name": full_name,
            "enrollment_no": enrollment_no,
            "department": department,
            "branch": branch,
            "semester": semester
        }

        return self.send_json({
            "success": True,
            "message": "Student registration completed successfully",
            "token": token,
            "user": user_info
        })

    def api_auth_login(self, data):
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        portal_type = data.get('portal_type', 'student') # 'student' or 'admin'

        if not email or not password:
            return self.send_error_json("Please provide both email and password")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT u.id, u.email, u.password_hash, u.salt, u.role,
                      sp.full_name, sp.enrollment_no, sp.department, sp.branch, sp.semester,
                      tp.full_name as teacher_name, tp.faculty_id, tp.department as teacher_dept, tp.designation
               FROM users u
               LEFT JOIN student_profiles sp ON u.id = sp.user_id
               LEFT JOIN teacher_profiles tp ON u.id = tp.user_id
               WHERE u.email = ?""",
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            conn.close()
            return self.send_error_json("Invalid credentials. Account not found.", 401)

        if not verify_password(password, user['salt'], user['password_hash']):
            conn.close()
            return self.send_error_json("Invalid password. Please check your credentials.", 401)

        # Role enforcement: Prevent cross-portal logins
        if portal_type == 'admin' and user['role'] != 'admin':
            conn.close()
            return self.send_error_json("Unauthorized. Admin privileges are required to access this portal.", 403)

        if portal_type == 'teacher' and user['role'] != 'teacher':
            conn.close()
            return self.send_error_json("Faculty accounts only. Use the correct portal.", 403)

        if portal_type == 'student' and user['role'] != 'student':
            conn.close()
            return self.send_error_json("Faculty/Admin accounts must use their respective portals.", 403)

        # Create session
        token = uuid.uuid4().hex
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat()

        cursor.execute(
            "INSERT INTO sessions (token, user_id, role, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
            (token, user['id'], user['role'], now, expires_at)
        )
        conn.commit()
        conn.close()

        user_data = dict(user)
        del user_data['password_hash']
        del user_data['salt']

        return self.send_json({
            "success": True,
            "message": f"Successfully authenticated as {user_data.get('full_name') or user_data['email']}",
            "token": token,
            "user": user_data
        })

    def api_auth_logout(self):
        auth_header = self.headers.get('Authorization', '')
        token = auth_header[7:].strip() if auth_header.startswith('Bearer ') else None
        if token:
            conn = get_db()
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            conn.close()
        return self.send_json({"success": True, "message": "Logged out successfully"})

    # ==========================================================================
    # STUDENT BUSINESS LOGIC
    # ==========================================================================
    def api_student_dashboard(self, student_user_id):
        conn = get_db()
        cursor = conn.cursor()

        # Aggregate counts for this student
        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE student_id = ?", (student_user_id,))
        total_projects = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE student_id = ? AND status = 'Submitted'", (student_user_id,))
        submitted_projects = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE student_id = ? AND status IN ('Submitted', 'Resubmitted', 'Under Review')", (student_user_id,))
        pending_reviews = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE student_id = ? AND status = 'Under Review'", (student_user_id,))
        under_review = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE student_id = ? AND status = 'Changes Requested'", (student_user_id,))
        changes_requested = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE student_id = ? AND status IN ('Approved', 'Approved for Viva', 'Viva Completed', 'Graded')", (student_user_id,))
        approved = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE student_id = ? AND status = 'Graded'", (student_user_id,))
        graded = cursor.fetchone()['count']

        # Average grade / latest published marks
        cursor.execute("""
            SELECT e.total_score, e.grade, p.title as project_title, p.id as project_id
            FROM evaluations e
            JOIN projects p ON e.project_id = p.id
            WHERE p.student_id = ? AND e.is_published = 1
            ORDER BY e.updated_at DESC LIMIT 1
        """, (student_user_id,))
        latest_grade = cursor.fetchone()

        # Recent projects list
        cursor.execute("""
            SELECT p.*, e.total_score, e.grade as eval_grade, e.is_published
            FROM projects p
            LEFT JOIN evaluations e ON p.id = e.project_id
            WHERE p.student_id = ?
            ORDER BY p.updated_at DESC
        """, (student_user_id,))
        projects = [dict(r) for r in cursor.fetchall()]

        # Recent notifications
        cursor.execute("""
            SELECT * FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC LIMIT 5
        """, (student_user_id,))
        notifications = [dict(r) for r in cursor.fetchall()]

        conn.close()

        return self.send_json({
            "success": True,
            "metrics": {
                "total_projects": total_projects,
                "submitted_projects": submitted_projects,
                "pending_reviews": pending_reviews,
                "under_review": under_review,
                "approved": approved,
                "changes_requested": changes_requested,
                "graded": graded,
                "latest_grade": dict(latest_grade) if latest_grade else None
            },
            "projects": projects,
            "notifications": notifications
        })

    def api_student_list_projects(self, student_user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, e.total_score, e.grade, e.is_published
            FROM projects p
            LEFT JOIN evaluations e ON p.id = e.project_id
            WHERE p.student_id = ?
            ORDER BY p.updated_at DESC
        """, (student_user_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return self.send_json({"success": True, "projects": rows})

    def api_student_get_project(self, project_id, student_user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, e.total_score, e.grade, e.overall_feedback, e.strengths,
                   e.weaknesses, e.missing_features, e.recommended_improvements, e.is_published
            FROM projects p
            LEFT JOIN evaluations e ON p.id = e.project_id
            WHERE p.id = ? AND p.student_id = ?
        """, (project_id, student_user_id))
        project = cursor.fetchone()
        conn.close()

        if not project:
            return self.send_error_json("Project not found or unauthorized access", 404)
        return self.send_json({"success": True, "project": dict(project)})

    def api_student_submit_project(self, student_user_id, data):
        title = data.get('title', '').strip()
        category = data.get('category', '').strip()
        abstract = data.get('abstract', '').strip()
        problem_statement = data.get('problem_statement', '').strip()
        objectives = data.get('objectives', '').strip()
        technologies = data.get('technologies', '').strip()
        team_members = data.get('team_members', '').strip()
        repo_url = data.get('repo_url', '').strip()
        live_url = data.get('live_url', '').strip()
        doc_file = data.get('doc_file', '')
        presentation_file = data.get('presentation_file', '')
        additional_files = data.get('additional_files', '')
        is_draft = 1 if data.get('is_draft') else 0

        if not is_draft and (not title or not abstract or not problem_statement or not technologies):
            return self.send_error_json("Please complete all required project specification fields")

        # Generate unique project ID
        year = datetime.datetime.now().year
        rand_num = str(uuid.uuid4().int)[:3].zfill(3)
        project_id = f"PRJ-{year}-{rand_num}"

        status = 'Draft' if is_draft else 'Submitted'
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO projects (
                id, student_id, title, category, abstract, problem_statement,
                objectives, technologies, team_members, repo_url, live_url,
                doc_file, presentation_file, additional_files, status, is_draft,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, student_user_id, title, category, abstract, problem_statement,
            objectives, technologies, team_members, repo_url, live_url,
            doc_file, presentation_file, additional_files, status, is_draft,
            now, now
        ))

        # Record Status History
        cursor.execute("""
            INSERT INTO project_status_history (
                project_id, from_status, to_status, changed_by_user_id, notes, created_at
            ) VALUES (?, NULL, ?, ?, ?, ?)
        """, (project_id, status, student_user_id, "Project submitted by student" if not is_draft else "Project saved as draft", now))

        # Record Initial Version (v1) in Provenance Ledger
        if not is_draft:
            cursor.execute("""
                INSERT INTO project_versions (
                    project_id, version_number, title, category, abstract,
                    problem_statement, objectives, technologies, team_members,
                    repo_url, live_url, doc_file, presentation_file, additional_files,
                    changelog, submitted_at
                ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Initial project submission (v1)', ?)
            """, (
                project_id, title, category, abstract, problem_statement,
                objectives, technologies, team_members, repo_url, live_url,
                doc_file, presentation_file, additional_files, now
            ))

        # Add Notification for student
        msg = f"Project '{title}' has been submitted for faculty review. Reference ID: {project_id}" if not is_draft else f"Draft saved for '{title}'."
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, link, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_user_id, "Submission Received" if not is_draft else "Draft Saved", msg, "success", f"#/projects/{project_id}", now))

        # Notify All Administrators
        if not is_draft:
            cursor.execute("SELECT id FROM users WHERE role = 'admin'")
            admins = cursor.fetchall()
            for a in admins:
                cursor.execute("""
                    INSERT INTO notifications (user_id, title, message, type, link, created_at)
                    VALUES (?, 'New Project Submission', ?, 'review', ?, ?)
                """, (a['id'], f"New capstone '{title}' submitted ({project_id}). Awaiting verification.", f"#/admin/projects/{project_id}", now))

        conn.commit()
        conn.close()

        return self.send_json({
            "success": True,
            "message": f"Project successfully {'submitted' if not is_draft else 'saved as draft'}",
            "project_id": project_id
        })

    def api_student_update_project(self, project_id, student_user_id, data):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM projects WHERE id = ? AND student_id = ?", (project_id, student_user_id))
        project = cursor.fetchone()

        if not project:
            conn.close()
            return self.send_error_json("Project not found or unauthorized", 404)

        current_status = project['status']
        # Resubmission allowed only when 'Changes Requested' or 'Draft'
        if current_status not in ['Changes Requested', 'Draft']:
            conn.close()
            return self.send_error_json(f"Cannot edit project while in status '{current_status}'. Edits are only permitted when changes are requested by faculty.", 400)

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        new_status = 'Resubmitted' if current_status == 'Changes Requested' else 'Submitted'
        version = project['submission_version'] + 1

        cursor.execute("""
            UPDATE projects SET
                title = COALESCE(?, title),
                category = COALESCE(?, category),
                abstract = COALESCE(?, abstract),
                problem_statement = COALESCE(?, problem_statement),
                objectives = COALESCE(?, objectives),
                technologies = COALESCE(?, technologies),
                team_members = COALESCE(?, team_members),
                repo_url = COALESCE(?, repo_url),
                live_url = COALESCE(?, live_url),
                doc_file = COALESCE(?, doc_file),
                presentation_file = COALESCE(?, presentation_file),
                additional_files = COALESCE(?, additional_files),
                status = ?,
                is_draft = 0,
                submission_version = ?,
                updated_at = ?
            WHERE id = ? AND student_id = ?
        """, (
            data.get('title'), data.get('category'), data.get('abstract'),
            data.get('problem_statement'), data.get('objectives'), data.get('technologies'),
            data.get('team_members'), data.get('repo_url'), data.get('live_url'),
            data.get('doc_file'), data.get('presentation_file'), data.get('additional_files'),
            new_status, version, now, project_id, student_user_id
        ))

        # Record Status History
        cursor.execute("""
            INSERT INTO project_status_history (
                project_id, from_status, to_status, changed_by_user_id, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, current_status, new_status, student_user_id, f"Resubmitted by student (v{version}) with requested improvements.", now))

        # Record Version Row in Provenance Ledger
        cursor.execute("""
            INSERT INTO project_versions (
                project_id, version_number, title, category, abstract,
                problem_statement, objectives, technologies, team_members,
                repo_url, live_url, doc_file, presentation_file, additional_files,
                changelog, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, version,
            data.get('title', project['title']),
            data.get('category', project['category']),
            data.get('abstract', project['abstract']),
            data.get('problem_statement', project['problem_statement']),
            data.get('objectives', project['objectives']),
            data.get('technologies', project['technologies']),
            data.get('team_members', project['team_members']),
            data.get('repo_url', project['repo_url']),
            data.get('live_url', project['live_url']),
            data.get('doc_file', project['doc_file']),
            data.get('presentation_file', project['presentation_file']),
            data.get('additional_files', project['additional_files']),
            data.get('changelog', f"Resubmission v{version} addressing faculty feedback."),
            now
        ))

        # Notify Admins of Resubmission
        cursor.execute("SELECT id FROM users WHERE role = 'admin'")
        admins = cursor.fetchall()
        for a in admins:
            cursor.execute("""
                INSERT INTO notifications (user_id, title, message, type, link, created_at)
                VALUES (?, 'Project Resubmitted', ?, 'review', ?, ?)
            """, (a['id'], f"Project {project_id} has been resubmitted with improvements (v{version}).", f"#/admin/projects/{project_id}", now))

        conn.commit()
        conn.close()

        return self.send_json({
            "success": True,
            "message": f"Project {project_id} resubmitted successfully for faculty review."
        })

    def api_student_resubmit_project(self, project_id, student_user_id, data):
        return self.api_student_update_project(project_id, student_user_id, data)

    def api_student_project_tracking(self, project_id, student_user_id):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM projects WHERE id = ? AND student_id = ?", (project_id, student_user_id))
        project = cursor.fetchone()
        if not project:
            conn.close()
            return self.send_error_json("Project not found", 404)

        # Status History
        cursor.execute("""
            SELECT psh.*, u.email as user_email, u.role as user_role, sp.full_name as user_name
            FROM project_status_history psh
            JOIN users u ON psh.changed_by_user_id = u.id
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            WHERE psh.project_id = ?
            ORDER BY psh.created_at ASC
        """, (project_id,))
        history = [dict(r) for r in cursor.fetchall()]

        # All Project Versions
        cursor.execute("""
            SELECT * FROM project_versions
            WHERE project_id = ?
            ORDER BY version_number ASC
        """, (project_id,))
        versions = [dict(r) for r in cursor.fetchall()]

        # Evaluation & Feedback if Published
        cursor.execute("""
            SELECT e.*, u.email as evaluator_email
            FROM evaluations e
            JOIN users u ON e.evaluated_by_user_id = u.id
            WHERE e.project_id = ? AND e.is_published = 1
        """, (project_id,))
        evaluation = cursor.fetchone()

        conn.close()

        return self.send_json({
            "success": True,
            "project": dict(project),
            "history": history,
            "versions": versions,
            "evaluation": dict(evaluation) if evaluation else None
        })

    def api_get_notifications(self, user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC LIMIT 30
        """, (user_id,))
        notifications = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return self.send_json({"success": True, "notifications": notifications})

    def api_mark_notifications_read(self, user_id, data):
        notification_id = data.get('notification_id')
        conn = get_db()
        if notification_id:
            conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notification_id, user_id))
        else:
            conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Notifications marked as read"})

    # ==========================================================================
    # ADMIN BUSINESS LOGIC
    # ==========================================================================
    def api_admin_dashboard(self):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(DISTINCT id) as count FROM users WHERE role = 'student'")
        total_students = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(DISTINCT id) as count FROM projects")
        total_projects = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM project_versions")
        total_submissions = cursor.fetchone()['count']
        if total_submissions == 0:
            cursor.execute("SELECT COUNT(*) as count FROM projects WHERE is_draft = 0")
            total_submissions = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE status IN ('Submitted', 'Resubmitted', 'Under Review')")
        pending_reviews = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE status = 'Under Review'")
        under_review = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE status = 'Changes Requested'")
        changes_requested = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE status IN ('Approved', 'Approved for Viva', 'Viva Completed', 'Graded')")
        approved = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE status = 'Rejected'")
        rejected = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE status = 'Graded'")
        graded = cursor.fetchone()['count']

        # Average evaluation score across published capstones
        cursor.execute("SELECT AVG(total_score) as avg_score FROM evaluations WHERE is_published = 1")
        row = cursor.fetchone()
        avg_score = round(row['avg_score'], 1) if (row and row['avg_score'] is not None) else None

        # Recent Submissions for Review Queue (Strictly pending/in-progress reviews only)
        cursor.execute("""
            SELECT p.*, sp.full_name as student_name, sp.enrollment_no, sp.department, sp.branch,
                   e.total_score, e.grade as eval_grade
            FROM projects p
            JOIN student_profiles sp ON p.student_id = sp.user_id
            LEFT JOIN evaluations e ON p.id = e.project_id
            WHERE p.status IN ('Submitted', 'Resubmitted', 'Under Review')
            ORDER BY p.updated_at DESC LIMIT 15
        """)
        recent_projects = [dict(r) for r in cursor.fetchall()]

        conn.close()

        return self.send_json({
            "success": True,
            "metrics": {
                "total_students": total_students,
                "total_projects": total_projects,
                "total_submissions": total_submissions,
                "pending_reviews": pending_reviews,
                "under_review": under_review,
                "changes_requested": changes_requested,
                "approved": approved,
                "rejected": rejected,
                "graded": graded,
                "average_score": avg_score
            },
            "recent_projects": recent_projects
        })

    def api_admin_list_projects(self, status_filter=None, search_query=None):
        conn = get_db()
        cursor = conn.cursor()

        sql = """
            SELECT p.*, sp.full_name as student_name, sp.enrollment_no, sp.department, sp.branch,
                   e.total_score, e.grade as eval_grade, e.is_published
            FROM projects p
            JOIN student_profiles sp ON p.student_id = sp.user_id
            LEFT JOIN evaluations e ON p.id = e.project_id
            WHERE 1=1
        """
        params = []

        if status_filter and status_filter != 'all':
            if status_filter == 'pending':
                sql += " AND p.status IN ('Submitted', 'Resubmitted', 'Under Review')"
            elif status_filter == 'approved':
                sql += " AND p.status IN ('Approved', 'Approved for Viva', 'Viva Completed')"
            else:
                sql += " AND p.status = ?"
                params.append(status_filter)

        if search_query:
            sql += " AND (p.title LIKE ? OR p.id LIKE ? OR sp.full_name LIKE ? OR sp.enrollment_no LIKE ?)"
            term = f"%{search_query}%"
            params.extend([term, term, term, term])

        sql += " ORDER BY p.updated_at DESC"
        cursor.execute(sql, params)
        projects = [dict(r) for r in cursor.fetchall()]
        conn.close()

        return self.send_json({"success": True, "projects": projects})

    def api_admin_get_project(self, project_id):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*, sp.full_name as student_name, sp.enrollment_no, sp.department,
                   sp.branch, sp.semester, u.email as student_email
            FROM projects p
            JOIN users u ON p.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE p.id = ?
        """, (project_id,))
        project = cursor.fetchone()

        if not project:
            conn.close()
            return self.send_error_json("Project not found", 404)

        # Status History
        cursor.execute("""
            SELECT psh.*, u.email as user_email, u.role as user_role, sp.full_name as user_name
            FROM project_status_history psh
            JOIN users u ON psh.changed_by_user_id = u.id
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            WHERE psh.project_id = ?
            ORDER BY psh.created_at ASC
        """, (project_id,))
        history = [dict(r) for r in cursor.fetchall()]

        # All Project Versions
        cursor.execute("""
            SELECT * FROM project_versions
            WHERE project_id = ?
            ORDER BY version_number ASC
        """, (project_id,))
        versions = [dict(r) for r in cursor.fetchall()]

        # Evaluation Data
        cursor.execute("SELECT * FROM evaluations WHERE project_id = ?", (project_id,))
        evaluation = cursor.fetchone()

        conn.close()

        return self.send_json({
            "success": True,
            "project": dict(project),
            "history": history,
            "versions": versions,
            "evaluation": dict(evaluation) if evaluation else None
        })

    def api_admin_update_status(self, project_id, admin_user_id, data):
        new_status = data.get('status')
        notes = data.get('notes', '').strip()

        valid_statuses = ['Under Review', 'Changes Requested', 'Approved', 'Approved for Viva', 'Rejected', 'Graded']
        if new_status not in valid_statuses:
            return self.send_error_json(f"Invalid status '{new_status}'")

        if new_status in ['Changes Requested', 'Rejected'] and not notes:
            return self.send_error_json(f"Written feedback is strictly required when setting status to '{new_status}'")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            return self.send_error_json("Project not found", 404)

        from_status = project['status']
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute("UPDATE projects SET status = ?, updated_at = ? WHERE id = ?", (new_status, now, project_id))

        cursor.execute("""
            INSERT INTO project_status_history (
                project_id, from_status, to_status, changed_by_user_id, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, from_status, new_status, admin_user_id, notes or f"Status changed to {new_status}", now))

        # Real-time notification for student
        student_id = project['student_id']
        notif_titles = {
            'Under Review': 'Review Commenced',
            'Changes Requested': 'Changes Requested by Faculty',
            'Approved': 'Project Approved!',
            'Rejected': 'Project Rejected',
            'Graded': 'Evaluation & Grade Published'
        }
        notif_title = notif_titles.get(new_status, "Project Status Updated")
        notif_msg = notes or f"Your project {project_id} has been moved to '{new_status}'."

        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, link, created_at)
            VALUES (?, ?, ?, 'status', ?, ?)
        """, (student_id, notif_title, notif_msg, f"#/tracking/{project_id}", now))

        conn.commit()
        conn.close()

        return self.send_json({
            "success": True,
            "message": f"Project status updated to '{new_status}'"
        })

    def api_admin_evaluate_project(self, project_id, admin_user_id, data):
        # 100-Mark Default Rubric Criteria
        problem_score = float(data.get('problem_statement_score', 0))
        impl_score = float(data.get('implementation_score', 0))
        innov_score = float(data.get('innovation_score', 0))
        doc_score = float(data.get('documentation_score', 0))
        ui_score = float(data.get('ui_ux_score', 0))
        pres_score = float(data.get('presentation_score', 0))
        comp_score = float(data.get('completeness_score', 0))

        # Max marks checks
        problem_score = max(0, min(15, problem_score))
        impl_score = max(0, min(25, impl_score))
        innov_score = max(0, min(15, innov_score))
        doc_score = max(0, min(15, doc_score))
        ui_score = max(0, min(10, ui_score))
        pres_score = max(0, min(10, pres_score))
        comp_score = max(0, min(10, comp_score))

        total_score = round(problem_score + impl_score + innov_score + doc_score + ui_score + pres_score + comp_score, 1)

        # Automatic Grade Assignment
        if total_score >= 90:
            grade = "A+"
        elif total_score >= 80:
            grade = "A"
        elif total_score >= 70:
            grade = "B+"
        elif total_score >= 60:
            grade = "B"
        elif total_score >= 50:
            grade = "C"
        else:
            grade = "Needs Improvement"

        overall_feedback = data.get('overall_feedback', '').strip()
        strengths = data.get('strengths', '').strip()
        weaknesses = data.get('weaknesses', '').strip()
        missing_features = data.get('missing_features', '').strip()
        technical_issues = data.get('technical_issues', '').strip()
        documentation_issues = data.get('documentation_issues', '').strip()
        recommended_improvements = data.get('recommended_improvements', '').strip()
        is_published = 1 if data.get('is_published') else 0

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT student_id, title FROM projects WHERE id = ?", (project_id,))
        proj = cursor.fetchone()
        if not proj:
            conn.close()
            return self.send_error_json("Project not found", 404)

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute("""
            INSERT INTO evaluations (
                project_id, evaluated_by_user_id,
                problem_statement_score, implementation_score, innovation_score,
                documentation_score, ui_ux_score, presentation_score, completeness_score,
                total_score, grade, overall_feedback, strengths, weaknesses,
                missing_features, technical_issues, documentation_issues,
                recommended_improvements, is_published, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET
                evaluated_by_user_id = excluded.evaluated_by_user_id,
                problem_statement_score = excluded.problem_statement_score,
                implementation_score = excluded.implementation_score,
                innovation_score = excluded.innovation_score,
                documentation_score = excluded.documentation_score,
                ui_ux_score = excluded.ui_ux_score,
                presentation_score = excluded.presentation_score,
                completeness_score = excluded.completeness_score,
                total_score = excluded.total_score,
                grade = excluded.grade,
                overall_feedback = excluded.overall_feedback,
                strengths = excluded.strengths,
                weaknesses = excluded.weaknesses,
                missing_features = excluded.missing_features,
                technical_issues = excluded.technical_issues,
                documentation_issues = excluded.documentation_issues,
                recommended_improvements = excluded.recommended_improvements,
                is_published = excluded.is_published,
                updated_at = excluded.updated_at
        """, (
            project_id, admin_user_id,
            problem_score, impl_score, innov_score, doc_score, ui_score, pres_score, comp_score,
            total_score, grade, overall_feedback, strengths, weaknesses,
            missing_features, technical_issues, documentation_issues,
            recommended_improvements, is_published, now, now
        ))

        if is_published:
            cursor.execute("UPDATE projects SET status = 'Graded', updated_at = ? WHERE id = ?", (now, project_id))
            cursor.execute("""
                INSERT INTO project_status_history (
                    project_id, from_status, to_status, changed_by_user_id, notes, created_at
                ) VALUES (?, 'Approved', 'Graded', ?, ?, ?)
            """, (project_id, admin_user_id, f"Evaluation published with Grade {grade} ({total_score}/100)", now))

            cursor.execute("""
                INSERT INTO notifications (user_id, title, message, type, link, created_at)
                VALUES (?, 'Official Grade Published', ?, 'grade', ?, ?)
            """, (proj['student_id'], f"Your evaluation for '{proj['title']}' is now available: {total_score}/100 ({grade})", f"#/feedback/{project_id}", now))

        conn.commit()
        conn.close()

        return self.send_json({
            "success": True,
            "message": f"Evaluation {'published' if is_published else 'saved as draft'}",
            "total_score": total_score,
            "grade": grade
        })

    def api_admin_list_students(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.is_active, u.created_at,
                   sp.full_name, sp.enrollment_no, sp.department,
                   sp.branch, sp.semester, sp.phone, sp.section, sp.academic_year,
                   COUNT(p.id) as total_projects,
                   AVG(e.total_score) as avg_score,
                   (SELECT tp.full_name FROM teacher_assignments ta
                    JOIN teacher_profiles tp ON ta.teacher_id = tp.user_id
                    WHERE ta.student_id = u.id AND ta.status = 'Active' LIMIT 1) as assigned_teacher
            FROM users u
            JOIN student_profiles sp ON u.id = sp.user_id
            LEFT JOIN projects p ON u.id = p.student_id
            LEFT JOIN evaluations e ON p.id = e.project_id AND e.is_published = 1
            WHERE u.role = 'student'
            GROUP BY u.id
            ORDER BY sp.full_name ASC
        """)
        students = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return self.send_json({"success": True, "students": students})

    def api_admin_analytics(self, query=None):
        conn = get_db()
        cursor = conn.cursor()

        # Build filter clauses if query parameters provided
        where_clauses = []
        params = []
        if query:
            dept = query.get('department', [None])[0]
            sem = query.get('semester', [None])[0]
            status = query.get('status', [None])[0]
            month = query.get('month', [None])[0]

            if dept and dept != 'all':
                where_clauses.append("sp.department = ?")
                params.append(dept)
            if sem and sem != 'all':
                where_clauses.append("sp.semester = ?")
                params.append(int(sem))
            if status and status != 'all':
                where_clauses.append("p.status = ?")
                params.append(status)
            if month and month != 'all':
                where_clauses.append("strftime('%Y-%m', p.created_at) = ?")
                params.append(month)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # 1. Status Breakdown
        cursor.execute(f"""
            SELECT p.status, COUNT(p.id) as count
            FROM projects p
            JOIN student_profiles sp ON p.student_id = sp.user_id
            {where_sql}
            GROUP BY p.status
        """, params)
        status_dist = {r['status']: r['count'] for r in cursor.fetchall()}

        # 2. Grade Breakdown
        cursor.execute(f"""
            SELECT e.grade, COUNT(e.id) as count
            FROM evaluations e
            JOIN projects p ON e.project_id = p.id
            JOIN student_profiles sp ON p.student_id = sp.user_id
            {where_sql + (' AND ' if where_sql else 'WHERE ') + 'e.is_published = 1'}
            GROUP BY e.grade
        """, params)
        grade_dist = {r['grade']: r['count'] for r in cursor.fetchall()}

        # 3. Department Breakdown
        cursor.execute(f"""
            SELECT sp.department, COUNT(p.id) as count
            FROM projects p
            JOIN student_profiles sp ON p.student_id = sp.user_id
            {where_sql}
            GROUP BY sp.department
        """, params)
        dept_dist = {r['department']: r['count'] for r in cursor.fetchall()}

        # 4. Monthly Submissions Trend
        cursor.execute(f"""
            SELECT strftime('%Y-%m', p.created_at) as month, COUNT(p.id) as count
            FROM projects p
            JOIN student_profiles sp ON p.student_id = sp.user_id
            {where_sql}
            GROUP BY month ORDER BY month ASC
        """, params)
        monthly_sub = [dict(r) for r in cursor.fetchall()]

        # 5. Approved vs Rejected Projects
        cursor.execute(f"""
            SELECT 
                SUM(CASE WHEN p.status IN ('Approved', 'Graded') THEN 1 ELSE 0 END) as approved_count,
                SUM(CASE WHEN p.status = 'Rejected' THEN 1 ELSE 0 END) as rejected_count
            FROM projects p
            JOIN student_profiles sp ON p.student_id = sp.user_id
            {where_sql}
        """, params)
        appr_rej = dict(cursor.fetchone() or {"approved_count": 0, "rejected_count": 0})

        # 6. Average Criterion Scores
        cursor.execute(f"""
            SELECT 
                AVG(e.problem_statement_score) as avg_problem,
                AVG(e.implementation_score) as avg_impl,
                AVG(e.innovation_score) as avg_innov,
                AVG(e.documentation_score) as avg_doc,
                AVG(e.ui_ux_score) as avg_ui,
                AVG(e.presentation_score) as avg_pres,
                AVG(e.completeness_score) as avg_comp,
                AVG(e.total_score) as avg_total
            FROM evaluations e
            JOIN projects p ON e.project_id = p.id
            JOIN student_profiles sp ON p.student_id = sp.user_id
            {where_sql + (' AND ' if where_sql else 'WHERE ') + 'e.is_published = 1'}
        """, params)
        avg_scores = dict(cursor.fetchone() or {})
        for k in avg_scores:
            if avg_scores[k] is not None:
                avg_scores[k] = round(avg_scores[k], 1)

        conn.close()

        return self.send_json({
            "success": True,
            "status_distribution": status_dist,
            "grade_distribution": grade_dist,
            "department_distribution": dept_dist,
            "monthly_submissions": monthly_sub,
            "approved_vs_rejected": appr_rej,
            "average_criteria_scores": avg_scores
        })

    def api_admin_export_csv(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id as project_id, p.title, p.category, p.status,
                   sp.full_name as student_name, sp.enrollment_no, sp.department, sp.branch,
                   e.total_score, e.grade, e.overall_feedback, p.created_at
            FROM projects p
            JOIN student_profiles sp ON p.student_id = sp.user_id
            LEFT JOIN evaluations e ON p.id = e.project_id
            ORDER BY p.id ASC
        """)
        rows = cursor.fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Project ID", "Project Title", "Category", "Status",
            "Student Name", "Enrollment No", "Department", "Branch",
            "Total Score (100)", "Grade", "Evaluation Feedback", "Submitted At"
        ])

        for r in rows:
            writer.writerow([
                r['project_id'], r['title'], r['category'], r['status'],
                r['student_name'], r['enrollment_no'], r['department'], r['branch'],
                r['total_score'] or "N/A", r['grade'] or "N/A", r['overall_feedback'] or "", r['created_at']
            ])

        csv_content = output.getvalue().encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/csv; charset=utf-8')
        self.send_header('Content-Disposition', 'attachment; filename="APTS_Capstone_Evaluations.csv"')
        self.send_header('Content-Length', str(len(csv_content)))
        self.end_headers()
        self.wfile.write(csv_content)

    def api_get_institution_settings(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM institution_settings WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        if not row:
            return self.send_json({"success": True, "settings": {}})
        d = dict(row)
        try:
            d['rubric'] = json.loads(d['rubric_json'])
            d['grade_scale'] = json.loads(d['grade_scale_json'])
        except Exception:
            pass
        return self.send_json({"success": True, "settings": d})

    def api_admin_update_institution_settings(self, data):
        college_name = data.get('college_name', '').strip()
        logo_url = data.get('logo_url', '').strip()
        department = data.get('department', '').strip()
        program = data.get('program', '').strip()
        academic_year = data.get('academic_year', '').strip()
        semester = int(data.get('semester', 6))
        session = data.get('session', '').strip()
        project_title = data.get('project_title', '').strip()
        submission_deadline = data.get('submission_deadline', '').strip()
        supervisor_name = data.get('supervisor_name', '').strip()
        evaluator_name = data.get('evaluator_name', '').strip()

        rubric = data.get('rubric')
        rubric_json = json.dumps(rubric) if rubric else None

        grade_scale = data.get('grade_scale')
        grade_scale_json = json.dumps(grade_scale) if grade_scale else None

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE institution_settings SET
                college_name = COALESCE(?, college_name),
                logo_url = COALESCE(?, logo_url),
                department = COALESCE(?, department),
                program = COALESCE(?, program),
                academic_year = COALESCE(?, academic_year),
                semester = COALESCE(?, semester),
                session = COALESCE(?, session),
                project_title = COALESCE(?, project_title),
                submission_deadline = COALESCE(?, submission_deadline),
                supervisor_name = COALESCE(?, supervisor_name),
                evaluator_name = COALESCE(?, evaluator_name),
                rubric_json = COALESCE(?, rubric_json),
                grade_scale_json = COALESCE(?, grade_scale_json),
                updated_at = ?
            WHERE id = 1
        """, (
            college_name or None, logo_url or None, department or None,
            program or None, academic_year or None, semester,
            session or None, project_title or None, submission_deadline or None,
            supervisor_name or None, evaluator_name or None, rubric_json,
            grade_scale_json, now
        ))
        conn.commit()
        conn.close()

        return self.send_json({"success": True, "message": "Institution configuration and grading criteria saved successfully."})

    def api_handle_file_upload(self, data):
        # File upload handler accepting base64 encoded payload or file mock
        file_name = data.get('file_name', 'document.pdf').strip()
        file_data = data.get('file_data', '')

        # Extension security validation
        ext = os.path.splitext(file_name)[1].lower()
        allowed_exts = ['.pdf', '.ppt', '.pptx', '.doc', '.docx', '.zip', '.tar', '.gz', '.png', '.jpg', '.jpeg']
        if ext not in allowed_exts:
            return self.send_error_json(f"File extension '{ext}' is not permitted. Allowed: {', '.join(allowed_exts)}")

        safe_name = f"{uuid.uuid4().hex[:8]}_{os.path.basename(file_name)}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)

        try:
            import base64
            if ',' in file_data:
                file_data = file_data.split(',')[1]
            content = base64.b64decode(file_data)
            # 25 MB limit check
            if len(content) > 25 * 1024 * 1024:
                return self.send_error_json("File size exceeds 25 MB limit.")
            with open(file_path, 'wb') as f:
                f.write(content)
        except Exception:
            # Fallback for plain text mock
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Sample Project Document: {file_name}\nUploaded successfully to APTS Storage.")

        return self.send_json({
            "success": True,
            "file_url": f"/uploads/{safe_name}",
            "file_name": safe_name
        })


    def api_admin_get_student(self, student_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.is_active, u.created_at,
                   sp.full_name, sp.enrollment_no, sp.department, sp.branch, sp.semester, sp.phone,
                   sp.section, sp.academic_year,
                   COUNT(p.id) as total_projects
            FROM users u
            JOIN student_profiles sp ON u.id = sp.user_id
            LEFT JOIN projects p ON u.id = p.student_id
            WHERE u.id = ? AND u.role = 'student'
            GROUP BY u.id
        """, (student_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return self.send_error_json("Student not found", 404)
        return self.send_json({"success": True, "student": dict(row)})

    def api_admin_create_student(self, data):
        full_name = data.get('full_name', '').strip()
        enrollment_no = data.get('enrollment_no', '').strip()
        email = data.get('email', '').strip().lower()
        department = data.get('department', '').strip()
        branch = data.get('branch', '').strip()
        semester = int(data.get('semester', 6))
        section = data.get('section', '').strip()
        academic_year = data.get('academic_year', '2025-2026').strip()
        phone = data.get('phone', '').strip()
        temp_password = data.get('temp_password', 'Student@2026!')

        if not full_name or not enrollment_no or not email:
            return self.send_error_json("Full name, enrollment number and email are required")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return self.send_error_json("An account with this email already exists")

        cursor.execute("SELECT user_id FROM student_profiles WHERE enrollment_no = ?", (enrollment_no,))
        if cursor.fetchone():
            conn.close()
            return self.send_error_json("An account with this enrollment number already exists")

        pwd_hash, salt = hash_password(temp_password)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute(
            "INSERT INTO users (email, password_hash, salt, role, is_active, created_at) VALUES (?, ?, ?, 'student', 1, ?)",
            (email, pwd_hash, salt, now)
        )
        user_id = cursor.lastrowid

        cursor.execute(
            """INSERT INTO student_profiles
               (user_id, full_name, enrollment_no, department, branch, semester, phone, section, academic_year, avatar)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '👨‍🎓')""",
            (user_id, full_name, enrollment_no, department, branch, semester, phone, section, academic_year)
        )

        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, link, created_at)
            VALUES (?, 'Account Created', 'Your student account has been created by the administrator. Login with your email and provided credentials.', 'info', '#/dashboard', ?)
        """, (user_id, now))

        conn.commit()
        conn.close()

        return self.send_json({
            "success": True,
            "message": f"Student account created for {full_name}",
            "user_id": user_id,
            "temp_password": temp_password
        })

    def api_admin_edit_student(self, student_id, data):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ? AND role = 'student'", (student_id,))
        if not cursor.fetchone():
            conn.close()
            return self.send_error_json("Student not found", 404)

        cursor.execute("""
            UPDATE student_profiles SET
                full_name = COALESCE(?, full_name),
                department = COALESCE(?, department),
                branch = COALESCE(?, branch),
                semester = COALESCE(?, semester),
                phone = COALESCE(?, phone),
                section = COALESCE(?, section),
                academic_year = COALESCE(?, academic_year)
            WHERE user_id = ?
        """, (
            data.get('full_name') or None, data.get('department') or None,
            data.get('branch') or None, data.get('semester') or None,
            data.get('phone') or None, data.get('section') or None,
            data.get('academic_year') or None, student_id
        ))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Student profile updated"})

    def api_admin_update_student_status(self, student_id, data):
        is_active = 1 if data.get('is_active') else 0
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ? AND role = 'student'", (is_active, student_id))
        if cursor.rowcount == 0:
            conn.close()
            return self.send_error_json("Student not found", 404)
        # Invalidate sessions if deactivating
        if not is_active:
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (student_id,))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": f"Student account {'activated' if is_active else 'deactivated'}"})

    def api_admin_reset_user_password(self, user_id, data):
        new_password = data.get('new_password', 'Reset@2026!')
        if len(new_password) < 6:
            return self.send_error_json("Password must be at least 6 characters")
        pwd_hash, salt = hash_password(new_password)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (pwd_hash, salt, user_id))
        if cursor.rowcount == 0:
            conn.close()
            return self.send_error_json("User not found", 404)
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Password reset successfully. All sessions invalidated."})

    # Admin Teacher Management
    def api_admin_list_teachers(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.is_active, u.created_at,
                   tp.full_name, tp.faculty_id, tp.department, tp.designation, tp.specialization, tp.phone,
                   (SELECT COUNT(*) FROM teacher_assignments ta WHERE ta.teacher_id = u.id AND ta.status = 'Active') as assigned_students,
                   (SELECT COUNT(*) FROM teacher_assignments ta2
                    JOIN projects p ON ta2.project_id = p.id
                    WHERE ta2.teacher_id = u.id AND p.status IN ('Submitted', 'Resubmitted', 'Under Review')) as pending_reviews
            FROM users u
            JOIN teacher_profiles tp ON u.id = tp.user_id
            WHERE u.role = 'teacher'
            ORDER BY tp.full_name ASC
        """)
        teachers = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return self.send_json({"success": True, "teachers": teachers})

    def api_admin_get_teacher(self, teacher_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.is_active, u.created_at,
                   tp.full_name, tp.faculty_id, tp.department, tp.designation, tp.specialization, tp.phone
            FROM users u
            JOIN teacher_profiles tp ON u.id = tp.user_id
            WHERE u.id = ? AND u.role = 'teacher'
        """, (teacher_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return self.send_error_json("Teacher not found", 404)
        return self.send_json({"success": True, "teacher": dict(row)})

    def api_admin_create_teacher(self, data):
        full_name = data.get('full_name', '').strip()
        faculty_id = data.get('faculty_id', '').strip()
        email = data.get('email', '').strip().lower()
        department = data.get('department', '').strip()
        designation = data.get('designation', 'Assistant Professor').strip()
        specialization = data.get('specialization', '').strip()
        phone = data.get('phone', '').strip()
        temp_password = data.get('temp_password', 'Teacher@2026!')

        if not full_name or not faculty_id or not email:
            return self.send_error_json("Full name, faculty ID and email are required")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return self.send_error_json("An account with this email already exists")

        cursor.execute("SELECT user_id FROM teacher_profiles WHERE faculty_id = ?", (faculty_id,))
        if cursor.fetchone():
            conn.close()
            return self.send_error_json("A teacher with this faculty ID already exists")

        pwd_hash, salt = hash_password(temp_password)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute(
            "INSERT INTO users (email, password_hash, salt, role, is_active, created_at) VALUES (?, ?, ?, 'teacher', 1, ?)",
            (email, pwd_hash, salt, now)
        )
        user_id = cursor.lastrowid

        cursor.execute(
            """INSERT INTO teacher_profiles
               (user_id, full_name, faculty_id, department, designation, specialization, phone)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, full_name, faculty_id, department, designation, specialization, phone)
        )

        conn.commit()
        conn.close()

        return self.send_json({
            "success": True,
            "message": f"Teacher account created for {full_name}",
            "user_id": user_id,
            "temp_password": temp_password
        })

    def api_admin_edit_teacher(self, teacher_id, data):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ? AND role = 'teacher'", (teacher_id,))
        if not cursor.fetchone():
            conn.close()
            return self.send_error_json("Teacher not found", 404)

        cursor.execute("""
            UPDATE teacher_profiles SET
                full_name = COALESCE(?, full_name),
                department = COALESCE(?, department),
                designation = COALESCE(?, designation),
                specialization = COALESCE(?, specialization),
                phone = COALESCE(?, phone)
            WHERE user_id = ?
        """, (
            data.get('full_name') or None, data.get('department') or None,
            data.get('designation') or None, data.get('specialization') or None,
            data.get('phone') or None, teacher_id
        ))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Teacher profile updated"})

    def api_admin_update_teacher_status(self, teacher_id, data):
        is_active = 1 if data.get('is_active') else 0
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ? AND role = 'teacher'", (is_active, teacher_id))
        if cursor.rowcount == 0:
            conn.close()
            return self.send_error_json("Teacher not found", 404)
        if not is_active:
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (teacher_id,))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": f"Teacher account {'activated' if is_active else 'deactivated'}"})

    # Admin Assignments
    def api_admin_list_assignments(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ta.*, tp.full_name as teacher_name, tp.faculty_id,
                   sp.full_name as student_name, sp.enrollment_no,
                   p.title as project_title, p.status as project_status
            FROM teacher_assignments ta
            JOIN teacher_profiles tp ON ta.teacher_id = tp.user_id
            JOIN student_profiles sp ON ta.student_id = sp.user_id
            LEFT JOIN projects p ON ta.project_id = p.id
            ORDER BY ta.created_at DESC
        """)
        assignments = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return self.send_json({"success": True, "assignments": assignments})

    def api_admin_create_assignment(self, admin_id, data):
        teacher_id = data.get('teacher_id')
        student_id = data.get('student_id')
        project_id = data.get('project_id') or None
        deadline = data.get('deadline') or None
        notes = data.get('notes', '')

        if not teacher_id or not student_id:
            return self.send_error_json("Teacher and student are required")

        conn = get_db()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute("""
            INSERT INTO teacher_assignments
            (teacher_id, student_id, project_id, assigned_by, deadline, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Active', ?)
        """, (teacher_id, student_id, project_id, admin_id, deadline, notes, now))

        # Notify teacher
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, link, created_at)
            VALUES (?, 'New Student Assigned', ?, 'info', '#/teacher/students', ?)
        """, (teacher_id, f"A student has been assigned to you for project supervision.", now))

        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Assignment created successfully"})

    def api_admin_revoke_assignment(self, assign_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE teacher_assignments SET status = 'Revoked' WHERE id = ?", (assign_id,))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Assignment revoked"})

    # Teacher Business Logic
    def api_teacher_dashboard(self, teacher_id):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(DISTINCT student_id) as count FROM teacher_assignments WHERE teacher_id = ? AND status = 'Active'", (teacher_id,))
        assigned_students = cursor.fetchone()['count']

        # Get student IDs assigned to this teacher
        cursor.execute("SELECT DISTINCT student_id FROM teacher_assignments WHERE teacher_id = ? AND status = 'Active'", (teacher_id,))
        student_ids = [r[0] for r in cursor.fetchall()]

        total_projects = 0
        pending_reviews = 0
        under_review = 0
        approved = 0
        graded = 0
        recent_projects = []

        if student_ids:
            placeholders = ','.join('?' * len(student_ids))

            cursor.execute(f"SELECT COUNT(*) as count FROM projects WHERE student_id IN ({placeholders})", student_ids)
            total_projects = cursor.fetchone()['count']

            cursor.execute(f"SELECT COUNT(*) as count FROM projects WHERE student_id IN ({placeholders}) AND status IN ('Submitted', 'Resubmitted')", student_ids)
            pending_reviews = cursor.fetchone()['count']

            cursor.execute(f"SELECT COUNT(*) as count FROM projects WHERE student_id IN ({placeholders}) AND status = 'Under Review'", student_ids)
            under_review = cursor.fetchone()['count']

            cursor.execute(f"SELECT COUNT(*) as count FROM projects WHERE student_id IN ({placeholders}) AND status IN ('Approved', 'Graded')", student_ids)
            approved = cursor.fetchone()['count']

            cursor.execute(f"SELECT COUNT(*) as count FROM projects WHERE student_id IN ({placeholders}) AND status = 'Graded'", student_ids)
            graded = cursor.fetchone()['count']

            cursor.execute(f"""
                SELECT p.*, sp.full_name as student_name, sp.enrollment_no
                FROM projects p
                JOIN student_profiles sp ON p.student_id = sp.user_id
                WHERE p.student_id IN ({placeholders})
                ORDER BY p.updated_at DESC LIMIT 10
            """, student_ids)
            recent_projects = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM teacher_profiles WHERE user_id = ?", (teacher_id,))
        profile = cursor.fetchone()
        conn.close()

        return self.send_json({
            "success": True,
            "metrics": {
                "assigned_students": assigned_students,
                "total_projects": total_projects,
                "pending_reviews": pending_reviews,
                "under_review": under_review,
                "approved": approved,
                "graded": graded
            },
            "recent_projects": recent_projects,
            "profile": dict(profile) if profile else None
        })

    def api_teacher_list_students(self, teacher_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT u.id, u.email, u.is_active,
                   sp.full_name, sp.enrollment_no, sp.department, sp.branch, sp.semester,
                   COUNT(p.id) as total_projects,
                   ta.deadline, ta.notes as assignment_notes, ta.created_at as assigned_at
            FROM teacher_assignments ta
            JOIN users u ON ta.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            LEFT JOIN projects p ON u.id = p.student_id
            WHERE ta.teacher_id = ? AND ta.status = 'Active'
            GROUP BY u.id
            ORDER BY sp.full_name ASC
        """, (teacher_id,))
        students = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return self.send_json({"success": True, "students": students})

    def api_teacher_list_projects(self, teacher_id, status_filter=None):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT student_id FROM teacher_assignments WHERE teacher_id = ? AND status = 'Active'", (teacher_id,))
        student_ids = [r[0] for r in cursor.fetchall()]

        if not student_ids:
            conn.close()
            return self.send_json({"success": True, "projects": []})

        placeholders = ','.join('?' * len(student_ids))
        params = list(student_ids)

        sql = f"""
            SELECT p.*, sp.full_name as student_name, sp.enrollment_no, sp.department,
                   e.total_score, e.grade as eval_grade, e.is_published
            FROM projects p
            JOIN student_profiles sp ON p.student_id = sp.user_id
            LEFT JOIN evaluations e ON p.id = e.project_id
            WHERE p.student_id IN ({placeholders})
        """

        if status_filter and status_filter != 'all':
            if status_filter == 'pending':
                sql += " AND p.status IN ('Submitted', 'Resubmitted', 'Under Review')"
            else:
                sql += " AND p.status = ?"
                params.append(status_filter)

        sql += " ORDER BY p.updated_at DESC"
        cursor.execute(sql, params)
        projects = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return self.send_json({"success": True, "projects": projects})

    def api_teacher_get_project(self, project_id, teacher_id):
        conn = get_db()
        cursor = conn.cursor()

        # Verify this project belongs to one of teacher's assigned students
        cursor.execute("SELECT DISTINCT student_id FROM teacher_assignments WHERE teacher_id = ? AND status = 'Active'", (teacher_id,))
        student_ids = [r[0] for r in cursor.fetchall()]

        cursor.execute("SELECT student_id FROM projects WHERE id = ?", (project_id,))
        proj_row = cursor.fetchone()

        if not proj_row or proj_row[0] not in student_ids:
            conn.close()
            return self.send_error_json("Project not found or unauthorized", 404)

        cursor.execute("""
            SELECT p.*, sp.full_name as student_name, sp.enrollment_no, sp.department,
                   sp.branch, sp.semester, u.email as student_email
            FROM projects p
            JOIN users u ON p.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE p.id = ?
        """, (project_id,))
        project = cursor.fetchone()

        cursor.execute("""
            SELECT psh.*, u.email as user_email, u.role as user_role, sp.full_name as user_name
            FROM project_status_history psh
            JOIN users u ON psh.changed_by_user_id = u.id
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            WHERE psh.project_id = ?
            ORDER BY psh.created_at ASC
        """, (project_id,))
        history = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM evaluations WHERE project_id = ?", (project_id,))
        evaluation = cursor.fetchone()

        conn.close()
        return self.send_json({
            "success": True,
            "project": dict(project),
            "history": history,
            "evaluation": dict(evaluation) if evaluation else None
        })

    def api_teacher_get_profile(self, teacher_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.created_at,
                   tp.full_name, tp.faculty_id, tp.department, tp.designation, tp.specialization, tp.phone
            FROM users u
            JOIN teacher_profiles tp ON u.id = tp.user_id
            WHERE u.id = ?
        """, (teacher_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return self.send_error_json("Profile not found", 404)
        return self.send_json({"success": True, "profile": dict(row)})

    def api_teacher_update_project_status(self, project_id, teacher_id, data):
        new_status = data.get('status')
        notes = data.get('notes', '').strip()

        valid_statuses = ['Under Review', 'Changes Requested', 'Approved', 'Rejected']
        if new_status not in valid_statuses:
            return self.send_error_json(f"Invalid status '{new_status}'")

        if new_status in ['Changes Requested', 'Rejected'] and not notes:
            return self.send_error_json(f"Feedback notes are required when setting status to '{new_status}'")

        # Verify teacher is assigned to this project's student
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT student_id FROM teacher_assignments WHERE teacher_id = ? AND status = 'Active'", (teacher_id,))
        student_ids = [r[0] for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()

        if not project or project['student_id'] not in student_ids:
            conn.close()
            return self.send_error_json("Project not found or unauthorized", 404)

        from_status = project['status']
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute("UPDATE projects SET status = ?, updated_at = ? WHERE id = ?", (new_status, now, project_id))
        cursor.execute("""
            INSERT INTO project_status_history
            (project_id, from_status, to_status, changed_by_user_id, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, from_status, new_status, teacher_id, notes or f"Status updated to {new_status}", now))

        # Notify student
        cursor.execute("SELECT * FROM teacher_profiles WHERE user_id = ?", (teacher_id,))
        tp = cursor.fetchone()
        teacher_name = tp['full_name'] if tp else 'Faculty'

        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, link, created_at)
            VALUES (?, ?, ?, 'status', ?, ?)
        """, (project['student_id'],
              f"Project Status: {new_status}",
              f"Your project {project_id} status changed to '{new_status}' by {teacher_name}. {notes}",
              f"#/tracking/{project_id}", now))

        # Also notify admins
        cursor.execute("SELECT id FROM users WHERE role = 'admin'")
        for a in cursor.fetchall():
            cursor.execute("""
                INSERT INTO notifications (user_id, title, message, type, link, created_at)
                VALUES (?, 'Teacher Updated Project', ?, 'review', ?, ?)
            """, (a['id'], f"{teacher_name} updated project {project_id} to '{new_status}'", f"#/admin/projects/{project_id}", now))

        conn.commit()
        conn.close()

        return self.send_json({"success": True, "message": f"Project status updated to '{new_status}'"})


def run_server():
    init_db()
    server_address = ('', PORT)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(server_address, APTSRequestHandler)
    print(f"=================================================================")
    print(f"APTS Engine active on http://localhost:{PORT}")
    print(f"Admin:   admin@univ.edu     | Pass: Admin@2026!")
    print(f"Teacher: teacher@univ.edu   | Pass: Teacher@2026!")
    print(f"Student: aarav.patel@student.univ.edu | Pass: Student@2026!")
    print(f"=================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()
