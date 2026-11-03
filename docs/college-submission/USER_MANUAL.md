# USER MANUAL & OPERATIONAL GUIDE

## EduProject: Student Project Management & Evaluation Platform

---

## SECTION 1: STUDENT PORTAL GUIDE

### 1.1 First-Time Registration
1. Open your web browser and go to `http://localhost:3000/`.
2. Click **"Enter Student Portal"** on the landing page or navbar.
3. If you do not have an account, click **"Create an Account"**.
4. Fill in:
   - **Full Name:** (e.g. John Doe)
   - **Enrollment Number:** (e.g. `ENR-2026-042`)
   - **College Email:** (e.g. `john@university.edu`)
   - **Department:** (Select e.g. Computer Science & Engineering)
   - **Branch:** (e.g. CSE)
   - **Semester:** (Select e.g. 6 or 8)
   - **Password:** (Minimum 6 characters)
5. Click **"Register & Access Portal"**.

### 1.2 Accessing the Student Dashboard
- **7 KPI Cards:** Displays Total Projects, Submitted Projects, Pending Reviews, Under Review, Changes Requested, Approved Projects, and Latest Published Grade.
- **Top Bar Actions:** View live deadline indicators, toggle theme, or log out.

### 1.3 Submitting a Capstone Project
1. In the student sidebar, click **"Submit Project"**.
2. Complete the form:
   - Project Title & Category
   - Abstract & Problem Statement
   - Project Objectives & Technologies Used
   - GitHub Repository URL & Live Demonstration URL
   - Upload PDF Documentation file (up to 25 MB)
   - Upload PPT Presentation slide deck
3. Click **"Submit Project Proposal"** (or **"Save as Draft"** if still working).
4. A toast will confirm your unique Project ID (e.g. `PRJ-2026-145`).

### 1.4 Tracking Project Lifecycle
1. In the sidebar, click **"Project Tracking"**.
2. Select your project from the dropdown.
3. Observe the 7-Stage Stepper:
   - Stage 1: Draft
   - Stage 2: Submitted
   - Stage 3: Under Review
   - Stage 4: Changes Requested
   - Stage 5: Resubmitted
   - Stage 6: Approved for Viva
   - Stage 7: Graded
4. If faculty requested changes, a red banner will display their exact instructions.
5. Click **"Submit Improved Version"** to upload revised files and enter your changelog.
6. The system updates your project to Revision 2 without creating a duplicate record!

### 1.5 Viewing Published Evaluation
- Once graded, the **Final Grade Card** unlocks showing your aggregate score out of 100, official letter grade, and multi-field feedback (Strengths, Weaknesses, Recommended Improvements).

---

## SECTION 2: FACULTY & ADMIN COMMAND CENTER GUIDE

### 2.1 Faculty Authentication
1. Go to `http://localhost:3000/`.
2. Click **"Enter Admin Portal"**.
3. Default faculty credentials:
   - **Email:** `admin@university.edu`
   - **Password:** `Admin@2026!`
4. Click **"Authorize & Enter Command Center"**.

### 2.2 Priority Review Queue
- The dashboard displays 6 Key Metrics: Registered Candidates, Total Projects, Pending Reviews, Approved Projects, Rejected Submissions, and Cohort Average Score.
- The **Priority Review Queue** only lists active submissions awaiting review (`Submitted`, `Resubmitted`, `Under Review`). Graded or rejected items are filtered out.
- Each row provides status-aware action buttons:
  - *Submitted* &rarr; "Review & Verify"
  - *Under Review* &rarr; "Continue Review"
  - *Changes Requested* &rarr; "Awaiting Resubmission"
  - *Approved* &rarr; "Schedule Viva"
  - *Graded* &rarr; "View Evaluation"

### 2.3 Inspecting Submissions & Governance Actions
1. Click **"Review & Verify"** on any project.
2. The verification modal displays:
   - Candidate details, title, abstract, problem statement, objectives, and technologies.
   - Revision history (if the project has multiple versions).
   - Direct download links for attached PDF spec and PPT slides.
3. Available actions:
   - **Start Review (Under Review):** Notifies student that technical review has begun.
   - **Accept & Approve for Viva:** Clears candidate for viva voce examination.
   - **Request Changes / Improvements:** Opens directive modal. Enter required changes; moves project to *Changes Requested*.
   - **Reject Project:** Opens rationale modal. Rejects project with formal reason.
   - **Grade 100-Mark Rubric:** Opens standardized evaluation form.

### 2.4 Conducting 100-Mark Rubric Grading
1. Navigate to the **"Rubric Evaluator"** tab.
2. Select the candidate project.
3. Enter marks for each of the 7 criteria:
   - Problem Statement & Objectives (0 - 15)
   - Technical Implementation (0 - 25)
   - Innovation & Creativity (0 - 15)
   - Documentation & Specification (0 - 15)
   - UI/UX & Interaction Design (0 - 10)
   - Presentation & Viva Defense (0 - 10)
   - Completeness & Deployability (0 - 10)
4. Aggregate score and letter grade (A+, A, B+, B, C, Needs Improvement) calculate in real-time.
5. Fill in comprehensive qualitative feedback:
   - Overall Evaluation Remarks
   - Project Strengths
   - Project Weaknesses
   - Missing Features
   - Technical Issues
   - Documentation Issues
   - Suggested Improvements
6. Check **"Publish marks to student dashboard immediately"** and click **"Submit & Publish Grade"**.

### 2.5 Institution Configuration & CSV Export
- **Settings Tab:** Edit Institute Name, Department, Degree Program, Academic Year, Session, Supervisor, External Evaluator, Submission Deadline, and Custom Rubric Weightings.
- **Export CSV Report:** Click the button in the top bar to download the accredited CSV report containing full student, project, and grading records.
