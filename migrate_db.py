import sqlite3
import json
import datetime

def migrate():
    conn = sqlite3.connect('portal.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF")

    # 1. Create project_versions table
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
        submitted_at TEXT NOT NULL
    )
    """)

    # 2. Create institution_settings table
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

    # Seed institution settings if not exists
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

    # 3. Deduplicate 'Autonomous Micro-Robot Navigation System'
    # Check if duplicates exist
    cursor.execute("SELECT id, status, submission_version, created_at FROM projects WHERE title LIKE '%Autonomous Micro-Robot%' ORDER BY created_at ASC")
    robot_projects = cursor.fetchall()
    if len(robot_projects) > 1:
        print(f"Found {len(robot_projects)} duplicate robot projects to consolidate into PRJ-2026-125.")
        canonical_id = "PRJ-2026-125"
        
        # Populate versions for canonical project
        v_num = 1
        for p_id, p_status, p_ver, p_date in robot_projects:
            cursor.execute("SELECT * FROM projects WHERE id = ?", (p_id,))
            p_data = cursor.fetchone()
            # Insert into project_versions
            cursor.execute("""
            INSERT INTO project_versions (
                project_id, version_number, title, category, abstract,
                problem_statement, objectives, technologies, team_members,
                repo_url, live_url, doc_file, presentation_file, additional_files,
                changelog, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                canonical_id, v_num, p_data[2], p_data[3], p_data[4],
                p_data[5], p_data[6], p_data[7], p_data[8],
                p_data[9], p_data[10], p_data[11], p_data[12], p_data[13],
                f"Version {v_num} - Status: {p_status}", p_date
            ))
            # Move status history to canonical_id
            cursor.execute("UPDATE project_status_history SET project_id = ? WHERE project_id = ?", (canonical_id, p_id))
            v_num += 1

        # Delete redundant duplicate projects other than canonical_id
        for p_id, _, _, _ in robot_projects:
            if p_id != canonical_id:
                cursor.execute("DELETE FROM evaluations WHERE project_id = ?", (p_id,))
                cursor.execute("DELETE FROM projects WHERE id = ?", (p_id,))

        # Update canonical project to version count
        cursor.execute("UPDATE projects SET submission_version = ? WHERE id = ?", (len(robot_projects), canonical_id))
        print("Duplicates successfully consolidated into PRJ-2026-125.")

    # 4. Also ensure each remaining project has at least v1 in project_versions
    cursor.execute("SELECT id, title, category, abstract, problem_statement, objectives, technologies, team_members, repo_url, live_url, doc_file, presentation_file, additional_files, created_at, submission_version FROM projects")
    all_prjs = cursor.fetchall()
    for prj in all_prjs:
        p_id = prj[0]
        cursor.execute("SELECT COUNT(*) FROM project_versions WHERE project_id = ?", (p_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO project_versions (
                project_id, version_number, title, category, abstract,
                problem_statement, objectives, technologies, team_members,
                repo_url, live_url, doc_file, presentation_file, additional_files,
                changelog, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p_id, 1, prj[1], prj[2], prj[3], prj[4], prj[5], prj[6],
                prj[7], prj[8], prj[9], prj[10], prj[11], prj[12],
                "Initial project submission (v1)", prj[13]
            ))

    cursor.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()
    print("Database migration completed successfully.")

if __name__ == '__main__':
    migrate()

