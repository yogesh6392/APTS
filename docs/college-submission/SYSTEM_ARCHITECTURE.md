# SYSTEM ARCHITECTURE & DESIGN SPECIFICATION

## EduProject: Student Project Management & Evaluation Platform

---

### 1. Architectural Overview & Design Patterns
EduProject is designed following a **Three-Tier Architecture** with a decoupled Single Page Application (SPA) frontend, a lightweight stateless REST application tier, and an ACID-compliant relational persistence layer.

```mermaid
flowchart TD
    subgraph Presentation Tier
        SPA["Vanilla ES6 Single Page Application (app.js)"]
        HTML["Semantic Structure (index.html)"]
        CSS["Design System & Theme Engine (styles.css)"]
    end

    subgraph Application Tier
        HTTP["HTTP Request Dispatcher (server.py)"]
        Auth["Authentication & Session Middleware"]
        Upload["File Validation & Storage Handler"]
        GovEngine["Phase-Gate Governance Engine"]
        Rubric["100-Mark Rubric Evaluation Engine"]
        Analytics["Cohort Performance Analytics"]
    end

    subgraph Data Tier
        DB[("SQLite3 Relational Storage (portal.db)")]
        FS[("File System Repository (uploads/)")]
    end

    SPA --> HTTP
    HTTP --> Auth
    Auth --> GovEngine
    Auth --> Rubric
    Auth --> Analytics
    HTTP --> Upload

    GovEngine --> DB
    Rubric --> DB
    Analytics --> DB
    Auth --> DB
    Upload --> FS
```

---

### 2. Detailed Component Decomposition

#### 2.1 Presentation Tier
- **State Store:** Managed within the `APTSClient` class (`app.js`). Stores active user profile, session token, project caches, and selected view state.
- **Theme Engine:** CSS custom properties define colors, spacing, typography, and dark navy glowing background grids.
- **Charts Engine:** Pure inline SVG rendering without external chart libraries (e.g. Chart.js, D3). Ensures zero bundle latency and exact color system alignment.

#### 2.2 Application Tier (REST API)
- Built on Python 3's `http.server.BaseHTTPRequestHandler`.
- Custom JSON serialization and error handling helper methods (`send_json`, `send_error_json`).
- PBKDF2 with SHA-256 password hashing (100,000 iterations + 16-byte cryptographically secure salt).
- Role-Based Access Control (RBAC) enforced on every private route.

#### 2.3 Data Persistence Tier
- **Foreign Key Cascades:** `PRAGMA foreign_keys = ON;`
- **Write-Ahead Logging (WAL Mode):** Ensures high read throughput while maintaining write serialization without locking conflicts.
- **Transactional Consistency:** All multi-table updates (e.g., project resubmission creating a new version and logging status history) execute within explicit SQLite database transactions.

---

### 3. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    users ||--o{ sessions : "maintains"
    users ||--o| student_profiles : "extends"
    users ||--o{ notifications : "receives"
    student_profiles ||--o{ projects : "submits"
    projects ||--o{ project_versions : "tracks"
    projects ||--o{ project_status_history : "records"
    projects ||--o| project_evaluations : "scored_by"

    users {
        int id PK
        string email UK
        string password_hash
        string salt
        string role
        datetime created_at
    }

    student_profiles {
        int id PK
        int user_id FK
        string full_name
        string enrollment_no UK
        string department
        string branch
        int semester
    }

    projects {
        string id PK
        int student_id FK
        string title
        string category
        text abstract
        text problem_statement
        text objectives
        text technologies
        string repo_url
        string live_url
        string doc_file
        string presentation_file
        string status
        int submission_version
        boolean is_draft
        datetime created_at
        datetime updated_at
    }

    project_versions {
        int id PK
        string project_id FK
        int version_number
        string title
        string category
        text abstract
        string repo_url
        string live_url
        string doc_file
        string presentation_file
        text changelog
        datetime submitted_at
    }

    project_status_history {
        int id PK
        string project_id FK
        string from_status
        string to_status
        int changed_by_user_id FK
        text notes
        datetime created_at
    }

    project_evaluations {
        int id PK
        string project_id FK
        int evaluator_id FK
        float problem_statement_score
        float implementation_score
        float innovation_score
        float documentation_score
        float ui_ux_score
        float presentation_score
        float completeness_score
        float total_score
        string grade
        text overall_feedback
        text strengths
        text weaknesses
        text missing_features
        text technical_issues
        text documentation_issues
        text recommended_improvements
        boolean is_published
        datetime updated_at
    }
```

---

### 4. Process Workflow & State Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Draft : Student initiates proposal
    Draft --> Submitted : Student submits proposal & files (v1)
    Submitted --> Under_Review : Faculty begins technical inspection
    Under_Review --> Changes_Requested : Faculty identifies gaps & issues directive
    Changes_Requested --> Resubmitted : Student submits corrected artifacts (v2..vn)
    Resubmitted --> Under_Review : Faculty inspects new revision
    Under_Review --> Approved : Verification successful, cleared for viva
    Approved --> Graded : Faculty completes 100-mark rubric & publishes
    Under_Review --> Rejected : Fatal non-conformance with B.Tech standards
    Graded --> [*] : Evaluation Completed & Archived
    Rejected --> [*] : Process Terminated
```

---

### 5. Multi-Version Revision Provenance Architecture
To solve the industry problem of duplicate project rows, EduProject separates the master entity identity from version artifacts:
- **Canonical Master Record (`projects`):** Holds the project's unique ID (`PRJ-2026-XXX`), current lifecycle status, and active pointer to the latest submission version.
- **Immutable Revision Ledger (`project_versions`):** Appends a new immutable snapshot row every time the student resubmits. Includes uploaded files, updated URLs, and explicit changelog text explaining how faculty comments were resolved.
