"""
Comprehensive 3-Role (Student, Teacher, Admin) Automated Test Suite
Validates:
- RBAC security (Student, Teacher, Admin role segregation)
- Student Portal endpoints & permissions
- Teacher Portal endpoints, dashboard, review queue, and grading
- Admin Portal management: Add Student, Add Teacher, Status Toggles, Password Resets
- Teacher-Student Assignment lifecycle & project supervision
"""
import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:3000"

def make_req(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if "application/json" in resp.headers.get("Content-Type", "") else content
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = {"raw": content}
        return e.code, parsed

def run_tests():
    passed = 0
    failed = 0

    def assert_eq(cond, desc):
        nonlocal passed, failed
        if cond:
            print(f"  [PASS] {desc}")
            passed += 1
        else:
            print(f"  [FAIL] {desc}")
            failed += 1

    print("=================================================================")
    print("RUNNING 3-ROLE UNIVERSITY PORTAL E2E VERIFICATION SUITE")
    print("=================================================================")

    # 1. LOGIN TESTS
    print("\n--- 1. Role-Based Login & Isolation ---")
    
    # Student Login
    code, res = make_req("/api/auth/login", "POST", {
        "email": "aarav.patel@student.univ.edu",
        "password": "Student@2026!",
        "portal_type": "student"
    })
    assert_eq(code == 200 and res.get("success"), "Student can log into Student Portal")
    student_token = res.get("token")
    student_id = res.get("user", {}).get("id")

    # Student cannot log into Teacher Portal
    code, res = make_req("/api/auth/login", "POST", {
        "email": "aarav.patel@student.univ.edu",
        "password": "Student@2026!",
        "portal_type": "teacher"
    })
    assert_eq(code == 403, "Student is denied entry to Teacher Portal (403)")

    # Student cannot log into Admin Portal
    code, res = make_req("/api/auth/login", "POST", {
        "email": "aarav.patel@student.univ.edu",
        "password": "Student@2026!",
        "portal_type": "admin"
    })
    assert_eq(code == 403, "Student is denied entry to Admin Portal (403)")

    # Teacher Login
    code, res = make_req("/api/auth/login", "POST", {
        "email": "teacher@univ.edu",
        "password": "Teacher@2026!",
        "portal_type": "teacher"
    })
    assert_eq(code == 200 and res.get("success"), "Teacher can log into Teacher Portal")
    teacher_token = res.get("token")
    teacher_id = res.get("user", {}).get("id")

    # Teacher cannot log into Admin Portal
    code, res = make_req("/api/auth/login", "POST", {
        "email": "teacher@univ.edu",
        "password": "Teacher@2026!",
        "portal_type": "admin"
    })
    assert_eq(code == 403, "Teacher is denied entry to Admin Portal (403)")

    # Admin Login
    code, res = make_req("/api/auth/login", "POST", {
        "email": "admin@univ.edu",
        "password": "Admin@2026!",
        "portal_type": "admin"
    })
    assert_eq(code == 200 and res.get("success"), "Admin can log into Admin Portal")
    admin_token = res.get("token")

    # 2. RBAC ACCESS CONTROL TESTS
    print("\n--- 2. RBAC Endpoint Access Authorization ---")
    
    # Student token hitting Admin Dashboard -> 403
    code, _ = make_req("/api/admin/dashboard", "GET", token=student_token)
    assert_eq(code == 403, "Student token blocked from GET /api/admin/dashboard (403)")

    # Student token hitting Teacher Dashboard -> 403
    code, _ = make_req("/api/teacher/dashboard", "GET", token=student_token)
    assert_eq(code == 403, "Student token blocked from GET /api/teacher/dashboard (403)")

    # Teacher token hitting Admin Dashboard -> 403
    code, _ = make_req("/api/admin/dashboard", "GET", token=teacher_token)
    assert_eq(code == 403, "Teacher token blocked from GET /api/admin/dashboard (403)")

    # Teacher token hitting Admin Teachers list -> 403
    code, _ = make_req("/api/admin/teachers", "GET", token=teacher_token)
    assert_eq(code == 403, "Teacher token blocked from GET /api/admin/teachers (403)")

    # Teacher token hitting Student Dashboard -> 403
    code, _ = make_req("/api/student/dashboard", "GET", token=teacher_token)
    assert_eq(code == 403, "Teacher token blocked from GET /api/student/dashboard (403)")

    # Teacher token accessing Teacher Dashboard -> 200
    code, res = make_req("/api/teacher/dashboard", "GET", token=teacher_token)
    assert_eq(code == 200 and "metrics" in res, "Teacher token authorized for GET /api/teacher/dashboard (200)")

    # Teacher token accessing Teacher Profile -> 200
    code, res = make_req("/api/teacher/profile", "GET", token=teacher_token)
    assert_eq(code == 200 and res.get("profile", {}).get("faculty_id") == "FAC-2026-001", "Teacher can read own profile")

    # 3. ADMIN STUDENT MANAGEMENT
    print("\n--- 3. Admin Student Account Management ---")

    import time
    unique_suffix = str(int(time.time()))[-4:]
    test_student_email = f"student_{unique_suffix}@univ.edu"
    test_student_enr = f"21CS{unique_suffix}"

    # Admin creates new student
    code, res = make_req("/api/admin/students", "POST", {
        "full_name": f"Test Candidate {unique_suffix}",
        "enrollment_no": test_student_enr,
        "email": test_student_email,
        "department": "Computer Science & Engineering",
        "branch": "Systems Engineering",
        "semester": 6,
        "phone": "9876543210",
        "temp_password": "NewStudent@2026!"
    }, token=admin_token)
    assert_eq(code == 200 and res.get("success"), f"Admin created student account: {test_student_email}")
    created_student_id = res.get("user_id")

    # Verify newly created student can log in
    code, res = make_req("/api/auth/login", "POST", {
        "email": test_student_email,
        "password": "NewStudent@2026!",
        "portal_type": "student"
    })
    assert_eq(code == 200 and res.get("success"), "Newly created student logs in successfully")
    new_student_token = res.get("token")

    # Admin deactivates student
    code, res = make_req(f"/api/admin/students/{created_student_id}/status", "POST", {
        "is_active": 0
    }, token=admin_token)
    assert_eq(code == 200, "Admin deactivates student account")

    # Admin reactivates student
    code, res = make_req(f"/api/admin/students/{created_student_id}/status", "POST", {
        "is_active": 1
    }, token=admin_token)
    assert_eq(code == 200, "Admin reactivates student account")

    # Admin resets student password
    code, res = make_req(f"/api/admin/students/{created_student_id}/reset-password", "POST", {
        "new_password": "ResetPass@2026!"
    }, token=admin_token)
    assert_eq(code == 200, "Admin resets student password")

    # Verify student logs in with new password
    code, res = make_req("/api/auth/login", "POST", {
        "email": test_student_email,
        "password": "ResetPass@2026!",
        "portal_type": "student"
    })
    assert_eq(code == 200 and res.get("success"), "Student logs in with reset password")
    new_student_token = res.get("token")

    # 4. ADMIN TEACHER MANAGEMENT
    print("\n--- 4. Admin Teacher / Faculty Account Management ---")

    test_teacher_email = f"prof_{unique_suffix}@univ.edu"
    test_teacher_fac_id = f"FAC-2026-{unique_suffix}"

    # Admin creates new teacher
    code, res = make_req("/api/admin/teachers", "POST", {
        "full_name": f"Dr. Vikram {unique_suffix}",
        "faculty_id": test_teacher_fac_id,
        "email": test_teacher_email,
        "department": "Computer Science & Engineering",
        "designation": "Associate Professor",
        "specialization": "Quantum Computing & Security",
        "phone": "9811223344",
        "temp_password": "NewTeacher@2026!"
    }, token=admin_token)
    assert_eq(code == 200 and res.get("success"), f"Admin created teacher account: {test_teacher_email}")
    created_teacher_id = res.get("user_id")

    # Verify newly created teacher can log in
    code, res = make_req("/api/auth/login", "POST", {
        "email": test_teacher_email,
        "password": "NewTeacher@2026!",
        "portal_type": "teacher"
    })
    assert_eq(code == 200 and res.get("success"), "Newly created teacher logs in successfully")

    # Admin resets teacher password
    code, res = make_req(f"/api/admin/teachers/{created_teacher_id}/reset-password", "POST", {
        "new_password": "TeacherReset@2026!"
    }, token=admin_token)
    assert_eq(code == 200, "Admin resets teacher password")

    # 5. TEACHER-STUDENT ASSIGNMENT & SUPERVISION WORKFLOW
    print("\n--- 5. Teacher-Student Assignment & Milestone Review Workflow ---")

    # Student submits a new capstone project
    code, res = make_req("/api/student/projects", "POST", {
        "title": f"High-Throughput Cryptographic Coprocessor ({unique_suffix})",
        "category": "Hardware Security",
        "abstract": "Hardware-accelerated AES-GCM engine with pipelined Galois Field multiplier.",
        "problem_statement": "Software crypto bottlenecks PCIe throughput in secure data transfers.",
        "objectives": "1. Synthesize AES pipeline\n2. Verify GCM authentication tags",
        "technologies": "SystemVerilog, UVM, Synopsys Design Compiler",
        "repo_url": "https://github.com/cse-batch2026/crypto-coproc",
        "is_draft": 0
    }, token=new_student_token)
    assert_eq(code == 200 and res.get("success"), "Student submits project for review")
    test_project_id = res.get("project_id")

    # Admin assigns teacher to student and project
    code, res = make_req("/api/admin/assignments", "POST", {
        "teacher_id": teacher_id,
        "student_id": created_student_id,
        "project_id": test_project_id,
        "deadline": "2026-05-30",
        "notes": "Faculty guide for Major Capstone FPGA synthesis."
    }, token=admin_token)
    assert_eq(code == 200 and res.get("success"), "Admin assigns Teacher to Student and Capstone Project")

    # Teacher checks assigned students list
    code, res = make_req("/api/teacher/students", "GET", token=teacher_token)
    has_student = any(s.get("id") == created_student_id for s in res.get("students", []))
    assert_eq(code == 200 and has_student, "Teacher sees assigned student in roster")

    # Teacher checks assigned projects list
    code, res = make_req("/api/teacher/projects", "GET", token=teacher_token)
    has_project = any(p.get("id") == test_project_id for p in res.get("projects", []))
    assert_eq(code == 200 and has_project, "Teacher sees student's submitted project in project queue")

    # Teacher updates project status to 'Under Review'
    code, res = make_req(f"/api/teacher/projects/{test_project_id}/status", "POST", {
        "status": "Under Review",
        "notes": "Commencing review of timing closure constraints."
    }, token=teacher_token)
    assert_eq(code == 200, "Teacher updates project status to 'Under Review'")

    # Teacher requests technical changes with specific guidance
    code, res = make_req(f"/api/teacher/projects/{test_project_id}/status", "POST", {
        "status": "Changes Requested",
        "notes": "Provide synthesis resource utilization report (LUTs and BRAMs)."
    }, token=teacher_token)
    assert_eq(code == 200, "Teacher requests technical changes with feedback notes")

    # Student resubmits project addressing teacher directives
    code, res = make_req(f"/api/student/projects/{test_project_id}/resubmit", "POST", {
        "abstract": "Hardware-accelerated AES-GCM engine. v2 adds synthesis utilization benchmarks.",
        "changelog": "Added LUT and BRAM utilization report as requested by guide."
    }, token=new_student_token)
    assert_eq(code == 200, "Student resubmits project (v2) addressing teacher directives")

    # Teacher approves project
    code, res = make_req(f"/api/teacher/projects/{test_project_id}/status", "POST", {
        "status": "Approved",
        "notes": "Synthesis reports verified. Timing met at 250 MHz."
    }, token=teacher_token)
    assert_eq(code == 200, "Teacher approves project")

    # Teacher evaluates project using 100-mark rubric and publishes grade
    code, res = make_req(f"/api/teacher/projects/{test_project_id}/evaluate", "POST", {
        "problem_statement_score": 14.5,
        "implementation_score": 24.0,
        "innovation_score": 14.0,
        "documentation_score": 14.0,
        "ui_ux_score": 9.5,
        "presentation_score": 9.5,
        "completeness_score": 9.5,
        "overall_feedback": "Exceptional ASIC implementation with verified testbench coverage.",
        "strengths": "Fast Galois Multiplier, minimal clock skew.",
        "recommended_improvements": "Add hardware side-channel DPA mitigation in future work.",
        "is_published": 1
    }, token=teacher_token)
    assert_eq(code == 200 and res.get("grade") == "A+", f"Teacher grades project: {res.get('total_score')}/100 (Grade {res.get('grade')})")

    # Student inspects published grade & feedback
    code, res = make_req(f"/api/student/projects/{test_project_id}/tracking", "GET", token=new_student_token)
    has_eval = res.get("evaluation") is not None and res.get("evaluation", {}).get("grade") == "A+"
    assert_eq(code == 200 and has_eval, "Student receives published Grade A+ and teacher feedback in tracking")

    print("\n=================================================================")
    print(f"TEST SUMMARY: {passed} PASSED, {failed} FAILED (Total: {passed + failed})")
    print("=================================================================")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

