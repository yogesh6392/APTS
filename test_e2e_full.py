import json
import urllib.request
import urllib.error
import urllib.parse
import sys
import time

BASE_URL = "http://localhost:3000"

def request(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {}
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    else:
        body = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()
            if "application/json" in content_type:
                return resp.status, json.loads(raw.decode("utf-8")), resp.headers
            else:
                return resp.status, raw.decode("utf-8", errors="ignore"), resp.headers
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw.decode("utf-8")), e.headers
        except Exception:
            return e.code, raw.decode("utf-8", errors="ignore"), e.headers

def run_tests():
    print("=" * 70)
    print("RUNNING COMPREHENSIVE E2E VERIFICATION SUITE")
    print(f"Target Server: {BASE_URL}")
    print("=" * 70)

    passed = 0
    total = 0

    def check(test_name, condition, extra_info=""):
        nonlocal passed, total
        total += 1
        if condition:
            print(f"[PASS] #{total:02d}: {test_name}")
            passed += 1
        else:
            print(f"[FAIL] #{total:02d}: {test_name} - {extra_info}")

    # -------------------------------------------------------------------------
    # TEST 1: Public Landing Page & Pure CSS Background Grid
    # -------------------------------------------------------------------------
    status, html_content, _ = request("GET", "/")
    check("Landing Page accessible with HTTP 200", status == 200)
    check("Hero title matches exact specification", 
          "Student Project Management" in html_content and "Evaluation Platform" in html_content)
    check("No DotGrid physics controller script in index.html", 
          "dotgrid.js" not in html_content and "PhysicsController" not in html_content)
    check("Pure CSS Grid class present in HTML", "bg-grid-tech" in html_content)
    check("Unverified accreditation claims removed", 
          "ABET & IEEE Accredited" not in html_content)

    # -------------------------------------------------------------------------
    # TEST 2: Zero Native Browser alert() or prompt() in app.js
    # -------------------------------------------------------------------------
    with open("app.js", "r", encoding="utf-8") as f:
        app_js = f.read()
    check("Zero alert() calls in app.js", "alert(" not in app_js)
    check("Zero prompt() calls in app.js", "prompt(" not in app_js)

    # -------------------------------------------------------------------------
    # TEST 3: Student Registration & Authentication
    # -------------------------------------------------------------------------
    test_enrollment = f"ENR-E2E-{int(time.time())}"
    student_email = f"student_{int(time.time())}@univ.edu"
    student_pw = "Student@2026!"

    reg_payload = {
        "full_name": "Aarav Sharma",
        "enrollment_no": test_enrollment,
        "email": student_email,
        "password": student_pw,
        "confirm_password": student_pw,
        "department": "Computer Science & Engineering",
        "branch": "CSE (AI & Data Science)",
        "semester": 6
    }
    status, reg_res, _ = request("POST", "/api/auth/register", reg_payload)
    check("Student registration returns HTTP 200 and token", 
          status == 200 and reg_res.get("success") and "token" in reg_res)
    student_token = reg_res.get("token")

    # -------------------------------------------------------------------------
    # TEST 4: Student RBAC Verification (Must Reject Admin Endpoints)
    # -------------------------------------------------------------------------
    status, rbac_res, _ = request("GET", "/api/admin/dashboard", token=student_token)
    check("Student token strictly rejected from /api/admin/dashboard (HTTP 403)", 
          status == 403, f"Received status {status}")

    # -------------------------------------------------------------------------
    # TEST 5: Student Project Submission (v1)
    # -------------------------------------------------------------------------
    sub_payload = {
        "title": "Autonomous Drone Fleet Coordination using Decentralized Consensus",
        "category": "Distributed Systems & Robotics",
        "abstract": "This capstone implements peer-to-peer Byzantine fault-tolerant trajectory negotiation for aerial drones in GPS-denied environments.",
        "problem_statement": "Coordinating unmanned aerial vehicles in indoor and contested zones without a central base station suffers from collision vulnerabilities.",
        "objectives": "1. Formulate distributed consensus protocol.\n2. Verify latency under 15ms in Gazebo simulation.\n3. Validate deadlock prevention.",
        "technologies": "ROS 2, Python, C++, Gazebo Simulator, Docker",
        "team_members": "Aarav Sharma (ENR-E2E-999), Priya Patel",
        "repo_url": "https://github.com/aarav-sharma/drone-consensus-fleet",
        "live_url": "https://drone-simulation.demo.internal",
        "doc_file": "/uploads/drone_fleet_srs_v1.pdf",
        "presentation_file": "/uploads/drone_fleet_slides_v1.pptx",
        "is_draft": False
    }
    status, sub_res, _ = request("POST", "/api/student/projects", sub_payload, token=student_token)
    check("Project submission returns HTTP 201 with project ID", 
          status in (200, 201) and sub_res.get("success") and "project_id" in sub_res)
    project_id = sub_res.get("project_id")

    # -------------------------------------------------------------------------
    # TEST 6: Student Dashboard & 7 KPI Cards
    # -------------------------------------------------------------------------
    status, dash_res, _ = request("GET", "/api/student/dashboard", token=student_token)
    check("Student dashboard returns HTTP 200", status == 200 and dash_res.get("success"))
    metrics = dash_res.get("metrics", {})
    check("Student KPI: total_projects >= 1", metrics.get("total_projects", 0) >= 1)
    check("Student KPI: submitted_projects >= 1", metrics.get("submitted_projects", 0) >= 1)
    check("Student KPI: approved == 0", metrics.get("approved_projects", 0) == 0)

    # -------------------------------------------------------------------------
    # TEST 7: Student Tracking & Initial Stepper / Version Provenance (v1)
    # -------------------------------------------------------------------------
    status, track_res, _ = request("GET", f"/api/student/projects/{project_id}/tracking", token=student_token)
    check("Project tracking returns project, history, and versions", 
          status == 200 and track_res.get("success"))
    p_data = track_res.get("project", {})
    check("Initial project status is 'Submitted'", p_data.get("status") == "Submitted")
    versions = track_res.get("versions", [])
    check("Project versions list contains exactly 1 initial version", len(versions) == 1 and versions[0].get("version_number") == 1)

    # -------------------------------------------------------------------------
    # TEST 8: Faculty / Admin Authentication & Dashboard
    # -------------------------------------------------------------------------
    admin_login = {
        "email": "admin@univ.edu",
        "password": "Admin@2026!",
        "portal_type": "admin"
    }
    status, a_res, _ = request("POST", "/api/auth/login", admin_login)
    check("Faculty admin login successful", status == 200 and a_res.get("success") and "token" in a_res)
    admin_token = a_res.get("token")

    status, a_dash, _ = request("GET", "/api/admin/dashboard", token=admin_token)
    check("Admin dashboard returns 6 KPI metrics", 
          status == 200 and "metrics" in a_dash and "pending_reviews" in a_dash["metrics"])
    recent_in_queue = [p["id"] for p in a_dash.get("recent_projects", [])]
    check("Submitted project is present in admin pending review queue", project_id in recent_in_queue)

    # -------------------------------------------------------------------------
    # TEST 9: Faculty Governance - Start Review ('Under Review')
    # -------------------------------------------------------------------------
    status_payload = {
        "status": "Under Review",
        "notes": "Faculty technical inspection initiated."
    }
    status, rev_res, _ = request("POST", f"/api/admin/projects/{project_id}/status", status_payload, token=admin_token)
    check("Status updated to 'Under Review'", status == 200 and rev_res.get("success"))

    # -------------------------------------------------------------------------
    # TEST 10: Faculty Governance - Request Changes with Written Directive
    # -------------------------------------------------------------------------
    changes_directive = "Simulation testbench must prove Byzantine resilience under 30% node dropouts. Add timing analysis charts to PDF."
    status_payload = {
        "status": "Changes Requested",
        "notes": changes_directive
    }
    status, chg_res, _ = request("POST", f"/api/admin/projects/{project_id}/status", status_payload, token=admin_token)
    check("Status updated to 'Changes Requested'", status == 200 and chg_res.get("success"))

    # Verify student sees this directive banner
    status, track_res2, _ = request("GET", f"/api/student/projects/{project_id}/tracking", token=student_token)
    p2 = track_res2.get("project", {})
    history = track_res2.get("history", [])
    check("Student tracking reflects status 'Changes Requested'", p2.get("status") == "Changes Requested")
    check("Student tracking history contains faculty directive notes", 
          any(changes_directive in h.get("notes", "") for h in history))

    # -------------------------------------------------------------------------
    # TEST 11: Student Resubmission (v2) - Version Provenance & Deduplication
    # -------------------------------------------------------------------------
    resub_payload = {
        "title": "Autonomous Drone Fleet Coordination using Decentralized Consensus (v2)",
        "category": "Distributed Systems & Robotics",
        "abstract": "Updated v2: Incorporates Byzantine fault tolerance proofs under 30% node dropout with full Gazebo testbench waveforms.",
        "repo_url": "https://github.com/aarav-sharma/drone-consensus-fleet",
        "live_url": "https://drone-simulation.demo.internal",
        "doc_file": "/uploads/drone_fleet_srs_v2_with_waveforms.pdf",
        "changelog": "Added Byzantine node dropout testbench and timing analysis graphs in Section 4."
    }
    status, resub_res, _ = request("POST", f"/api/student/projects/{project_id}/resubmit", resub_payload, token=student_token)
    check("Project resubmission returns HTTP 200", status == 200 and resub_res.get("success"))

    # Verify provenance and absence of duplicates
    status, track_res3, _ = request("GET", f"/api/student/projects/{project_id}/tracking", token=student_token)
    p3 = track_res3.get("project", {})
    versions3 = track_res3.get("versions", [])
    check("Project status is now 'Resubmitted'", p3.get("status") == "Resubmitted")
    check("Project submission_version is incremented to 2", p3.get("submission_version") == 2)
    check("Project versions ledger contains exactly 2 versions for the same ID", 
          len(versions3) == 2 and versions3[1].get("version_number") == 2)
    check("Version 2 record contains student changelog", 
          "Byzantine node dropout" in versions3[1].get("changelog", ""))

    # Verify student projects list has not duplicated
    status, stu_projs, _ = request("GET", "/api/student/projects", token=student_token)
    matching_projects = [p for p in stu_projs.get("projects", []) if p["id"] == project_id]
    check("Student has exactly 1 project entity with this ID (No duplicate row)", len(matching_projects) == 1)

    # -------------------------------------------------------------------------
    # TEST 12: Faculty Approval for Viva Voce
    # -------------------------------------------------------------------------
    status_payload = {
        "status": "Approved",
        "notes": "Revision satisfies Byzantine resilience requirements. Approved for Viva Voce."
    }
    status, app_res, _ = request("POST", f"/api/admin/projects/{project_id}/status", status_payload, token=admin_token)
    check("Status updated to 'Approved'", status == 200 and app_res.get("success"))

    # -------------------------------------------------------------------------
    # TEST 13: 100-Mark Rubric Evaluation & Publishing
    # -------------------------------------------------------------------------
    eval_payload = {
        "problem_statement_score": 14.5,
        "implementation_score": 24.0,
        "innovation_score": 14.0,
        "documentation_score": 14.5,
        "ui_ux_score": 9.0,
        "presentation_score": 9.5,
        "completeness_score": 9.5,
        "overall_feedback": "Exemplary implementation of decentralized consensus for aerial robotics with solid mathematical proofs.",
        "strengths": "Outstanding Gazebo simulation fidelity and thorough Byzantine dropout testbench.",
        "weaknesses": "Hardware synthesis on real micro-controller boards remains as future work.",
        "missing_features": "None for undergraduate scope.",
        "technical_issues": "Minor packet serialization latency over high-jitter simulated RF links.",
        "documentation_issues": "None; IEEE format strictly adhered to.",
        "recommended_improvements": "Extend protocol to heterogeneous ground-air drone meshes.",
        "is_published": True
    }
    status, eval_res, _ = request("POST", f"/api/admin/projects/{project_id}/evaluate", eval_payload, token=admin_token)
    expected_total = 14.5 + 24.0 + 14.0 + 14.5 + 9.0 + 9.5 + 9.5 # 95.0
    check("Rubric evaluation returns HTTP 200 and total score 95.0 (Grade A+)", 
          status == 200 and eval_res.get("success") and eval_res.get("total_score") == 95.0 and eval_res.get("grade") == "A+")

    # -------------------------------------------------------------------------
    # TEST 14: Review Queue Isolation (Graded Project MUST NOT Be In Pending Queue)
    # -------------------------------------------------------------------------
    status, a_dash2, _ = request("GET", "/api/admin/dashboard", token=admin_token)
    recent_after_grade = [p["id"] for p in a_dash2.get("recent_projects", [])]
    check("Graded project is strictly excluded from pending review queue", project_id not in recent_after_grade)

    # -------------------------------------------------------------------------
    # TEST 15: Student Sees Published Grade & All Evaluation Details
    # -------------------------------------------------------------------------
    status, track_res4, _ = request("GET", f"/api/student/projects/{project_id}/tracking", token=student_token)
    ev4 = track_res4.get("evaluation", {})
    check("Student tracking reflects published evaluation", ev4.get("is_published") == 1)
    check("Student sees correct total score 95.0 and Grade A+", ev4.get("total_score") == 95.0 and ev4.get("grade") == "A+")
    check("Student sees strengths and weaknesses feedback", 
          "Outstanding Gazebo" in ev4.get("strengths", "") and "Hardware synthesis" in ev4.get("weaknesses", ""))

    # -------------------------------------------------------------------------
    # TEST 16: Institution Configuration Settings API
    # -------------------------------------------------------------------------
    status, set_res, _ = request("GET", "/api/institution/settings")
    check("Institution settings GET returns HTTP 200", status == 200 and set_res.get("success"))

    updated_settings = {
        "college_name": "Faculty of Engineering & Technology (Autonomous)",
        "department": "Department of Computer Science & Engineering",
        "degree_program": "B.Tech Computer Science & Engineering",
        "academic_year": "2025-2026",
        "semester": 6,
        "project_session": "Spring 2026 Capstone Evaluation",
        "capstone_title": "Undergraduate Senior Capstone Projects",
        "faculty_supervisor": "Dr. Rajesh K. Sharma, Professor & Head",
        "faculty_evaluator": "Dr. Anjali Gupta, Senior Evaluator",
        "submission_deadline": "2026-05-30",
        "rubric_weights": {
            "problem_statement": 15,
            "implementation": 25,
            "innovation": 15,
            "documentation": 15,
            "ui_ux": 10,
            "presentation": 10,
            "completeness": 10
        }
    }
    status, set_save, _ = request("POST", "/api/admin/institution/settings", updated_settings, token=admin_token)
    check("Institution settings POST saves successfully", status == 200 and set_save.get("success"))

    status, set_res2, _ = request("GET", "/api/institution/settings")
    check("Institution settings reflect updated college name", 
          set_res2.get("settings", {}).get("college_name") == "Faculty of Engineering & Technology (Autonomous)")

    # -------------------------------------------------------------------------
    # TEST 17: Accredited CSV Report Export
    # -------------------------------------------------------------------------
    status, csv_data, headers = request("GET", "/api/admin/export", token=admin_token)
    check("Admin CSV export returns HTTP 200 with text/csv header", 
          status == 200 and "text/csv" in headers.get("Content-Type", ""))
    check("CSV dataset contains project ID and student name", 
          project_id in csv_data and "Aarav Sharma" in csv_data)

    print("=" * 70)
    print(f"TEST SUITE COMPLETE: {passed}/{total} TESTS PASSED ({(passed/total)*100:.1f}%)")
    print("=" * 70)

    if passed == total:
        print("ALL VERIFICATION CHECKS PASSED PERFECTLY!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED - REVIEW OUTPUT ABOVE.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
