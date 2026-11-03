# EduProject • Student Project Management & Faculty Evaluation Platform

**Degree Program:** Bachelor of Technology (B.Tech) Capstone Evaluation System  
**Institution:** Faculty of Engineering & Technology • Department of Computer Science & Engineering  
**Application URL:** [http://localhost:3000/](http://localhost:3000/)  

---

## 🚀 Overview

**EduProject** is a production-grade, full-stack Student Project Submission, Revision Provenance, and Faculty Evaluation Platform designed for engineering colleges and universities.

It eliminates the critical failure modes of conventional academic project tracking:
1. **Multi-Version Revision Provenance Ledger:** Eliminates project duplication when students make revisions (`v1 &rarr; v2 &rarr; vn`), maintaining an immutable revision history under a single canonical project ID.
2. **Phase-Gate Governance Stepper:** Enforces an active 7-stage lifecycle (*Draft &rarr; Submitted &rarr; Under Review &rarr; Changes Requested &rarr; Resubmitted &rarr; Approved for Viva &rarr; Graded*).
3. **Automated 100-Mark Rubric Evaluator:** 7 standardized criteria with automatic aggregate scoring, letter-grade determination (`A+`, `A`, `B+`, `B`, `C`), and mandatory qualitative feedback fields.
4. **Queue Isolation:** Faculty review queue strictly isolates pending reviews and filters out graded or rejected submissions.
5. **Pure CSS Tech Grid Background:** Elegant `#080F1D` dark navy interface with subtle CSS grid lines (`36px × 36px`) and cyan radial glows. Zero unwanted physics controllers.
6. **Zero Browser Native Alerts:** Completely eliminates disruptive browser `alert()` and `prompt()` popups, utilizing sleek inline modal prompts and custom notifications.

---

## 🌐 Live Access & Credentials

- **Local Web Server:** `http://localhost:3000/`

### Portal Routes & Direct Navigation
- **Student Portal:** `#/student/login` | `#/student/register` | `#/student/dashboard`
- **Teacher / Guide Portal:** `#/teacher/login` | `#/teacher/dashboard`
- **Admin / Faculty Command:** `#/admin/login` | `#/admin/dashboard`

### Default User Credentials
| Role | Portal URL | Email Address | Password | Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **Student** | `#/student/login` | `aarav.patel@student.univ.edu` | `Student@2026!` | Submit projects, multi-version resubmissions, milestone tracking, view grades |
| **Teacher / Guide** | `#/teacher/login` | `teacher@univ.edu` | `Teacher@2026!` | Supervise assigned students, review deliverables, request revisions, 100-mark rubric grading |
| **Administrator / HOD** | `#/admin/login` | `admin@univ.edu` | `Admin@2026!` | Manage students & teachers, guide assignments, cohort analytics, accreditation export |

---

## 🛠️ Technology Stack

- **Frontend:** HTML5 Semantic Markup, Modern Responsive CSS3 (Custom Variables, Flexbox, Grid), Vanilla ES6+ Object-Oriented Architecture (`APTSClient`). Zero heavy frontend dependencies.
- **Backend:** Python 3 Standard Library (`http.server`, `urllib.parse`, `hashlib`, `json`, `sqlite3`). Lightweight, highly portable, instant startup.
- **Database:** SQLite3 with WAL (Write-Ahead Logging), Foreign Key enforcement, and ACID transaction safety (`portal.db`).
- **Visualizations:** Pure inline SVG rendering for status distribution, criterion radar breakdown, and timeline velocity.

---

## 📁 Project Structure

```
├── app.js                          # Client SPA controller (ES6 class APTSClient)
├── index.html                      # Semantic UI structure, modals, templates
├── styles.css                      # Design system, CSS grid, dark navy theme (#080F1D)
├── server.py                       # RESTful backend API & HTTP file server
├── portal.db                       # Relational database (SQLite3)
├── portal.db.bak                   # Verified database backup
├── migrate_db.py                   # DB migration & deduplication script
├── test_e2e_full.py                # 41-point comprehensive automated E2E test suite
├── .env.example                    # Environment configuration template
├── uploads/                        # Document & PPT artifact repository
└── docs/
    └── college-submission/
        ├── PROJECT_REPORT.md       # Comprehensive 28-section academic project report
        ├── SYSTEM_ARCHITECTURE.md  # 3-Tier architecture & Mermaid diagrams
        ├── USER_MANUAL.md          # Step-by-step student and faculty user manuals
        └── TEST_CASES_AND_VALIDATION.md # 30+ formal test cases & verification matrix
```

---

## 🧪 Automated Testing

Execute the test suites covering all 3 roles, authentication, RBAC, file uploads, provenance deduplication, 100-mark rubric grading, guide assignment, and CSV export:

```bash
# 1. 3-Role (Student, Teacher, Admin) RBAC & Assignment Lifecycle Suite:
python test_three_roles_full.py
# Result: 32/32 Tests Passed (100.0%)

# 2. Comprehensive E2E System Verification Suite:
python test_e2e_full.py
# Result: 41/41 Tests Passed (100.0%)
```
*Total Verification: 73/73 Tests Passed (100.0%) with Zero Failures.*

---

## 📖 Academic Documentation

Comprehensive submission documentation is pre-compiled under `docs/college-submission/`:
- **Full Capstone Report:** [`docs/college-submission/PROJECT_REPORT.md`](file:///c:/Users/ASUS/OneDrive/Documents/OOTS/docs/college-submission/PROJECT_REPORT.md)
- **System Architecture & Diagrams:** [`docs/college-submission/SYSTEM_ARCHITECTURE.md`](file:///c:/Users/ASUS/OneDrive/Documents/OOTS/docs/college-submission/SYSTEM_ARCHITECTURE.md)
- **Student & Faculty User Manual:** [`docs/college-submission/USER_MANUAL.md`](file:///c:/Users/ASUS/OneDrive/Documents/OOTS/docs/college-submission/USER_MANUAL.md)
- **Test Cases & Traceability Matrix:** [`docs/college-submission/TEST_CASES_AND_VALIDATION.md`](file:///c:/Users/ASUS/OneDrive/Documents/OOTS/docs/college-submission/TEST_CASES_AND_VALIDATION.md)
