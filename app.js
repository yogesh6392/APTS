/**
 * Student Project Management & Faculty Evaluation Platform
 * Client Controller & Real REST API Integration
 * Connects directly to SQLite backend at /api/*
 * Handles Student & Admin Portals, Authentication, Submission,
 * Visual Tracking Stepper, 100-Mark Rubric Evaluator, and Institution Governance.
 */

class APTSClient {
  constructor() {
    this.token = localStorage.getItem("apts_token") || null;
    this.currentUser = null;
    this.currentStudentTab = "sTabDashboard";
    this.currentAdminTab = "aTabDashboard";
    this.theme = localStorage.getItem("apts_theme") || "dark";
    this.projectsCache = [];
    this.selectedProjectId = null;
    this.institutionSettings = null;

    this.initTheme();
    window.addEventListener("hashchange", () => this.handleRoute());
    if (window.location.hash) {
      this.handleRoute();
    } else {
      this.checkSessionAndRoute();
    }
    this.loadInstitutionSettings();
  }

  // ==========================================================================
  // THEME INITIALIZATION
  // ==========================================================================
  initTheme() {
    document.documentElement.setAttribute("data-theme", this.theme);
  }

  toggleTheme() {
    this.theme = this.theme === "dark" ? "light" : "dark";
    localStorage.setItem("apts_theme", this.theme);
    this.initTheme();
  }

  toggleSidebar(role) {
    let sidebar, overlay;
    if (role === "admin") {
      sidebar = document.getElementById("adminSidebar");
      overlay = document.getElementById("adminSidebarOverlay");
    } else if (role === "teacher") {
      sidebar = document.getElementById("teacherSidebar");
      overlay = document.getElementById("teacherSidebarOverlay");
    } else {
      sidebar = document.getElementById("studentSidebar");
      overlay = document.getElementById("studentSidebarOverlay");
    }
    if (sidebar) sidebar.classList.toggle("mobile-open");
    if (overlay) overlay.classList.toggle("active");
  }

  closeSidebar(role) {
    let sidebar, overlay;
    if (role === "admin") {
      sidebar = document.getElementById("adminSidebar");
      overlay = document.getElementById("adminSidebarOverlay");
    } else if (role === "teacher") {
      sidebar = document.getElementById("teacherSidebar");
      overlay = document.getElementById("teacherSidebarOverlay");
    } else {
      sidebar = document.getElementById("studentSidebar");
      overlay = document.getElementById("studentSidebarOverlay");
    }
    if (sidebar) sidebar.classList.remove("mobile-open");
    if (overlay) overlay.classList.remove("active");
  }

  closeSidebar(role) {
    const sidebar = role === "admin" ? document.getElementById("adminSidebar") : document.getElementById("studentSidebar");
    const overlay = role === "admin" ? document.getElementById("adminSidebarOverlay") : document.getElementById("studentSidebarOverlay");
    if (sidebar) sidebar.classList.remove("mobile-open");
    if (overlay) overlay.classList.remove("active");
  }

  async loadInstitutionSettings() {
    try {
      const res = await this.apiRequest("/api/institution/settings");
      if (res && res.success && res.settings) {
        this.institutionSettings = res.settings;
        this.applyInstitutionSettings();
      }
    } catch (e) {
      console.warn("Could not load institution settings:", e);
    }
  }

  applyInstitutionSettings() {
    if (!this.institutionSettings) return;
    const s = this.institutionSettings;
    const nameEl = document.getElementById("instCollegeNameDisplay");
    if (nameEl) nameEl.innerText = s.college_name || "Faculty of Engineering & Technology";
    const deptEl = document.getElementById("instDeptDisplay");
    if (deptEl) deptEl.innerText = s.department || "Computer Science & Engineering";
    const sessionEl = document.getElementById("instSessionDisplay");
    if (sessionEl) sessionEl.innerText = s.session || "Spring 2026";
  }

  // ==========================================================================
  // HTTP REQUEST WRAPPER FOR BACKEND REST API
  // ==========================================================================
  async apiRequest(endpoint, method = "GET", body = null) {
    const headers = { "Content-Type": "application/json" };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const options = { method, headers };
    if (body) {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(endpoint, options);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || `Request failed with status ${response.status}`);
      }
      return data;
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  }

  // ==========================================================================
  // SESSION AUTHENTICATION & ROUTING
  // ==========================================================================
  async checkSessionAndRoute() {
    if (!this.token) {
      this.showLanding();
      return;
    }

    try {
      const res = await this.apiRequest("/api/auth/me");
      if (res.success && res.user) {
        this.currentUser = res.user;
        if (res.user.role === "student") {
          this.showStudentPortal();
        } else if (res.user.role === "teacher") {
          this.showTeacherPortal();
        } else if (res.user.role === "admin") {
          this.showAdminPortal();
        } else {
          this.showLanding();
        }
      } else {
        this.logout();
      }
    } catch (e) {
      this.logout();
    }
  }

  showLanding() {
    document.getElementById("viewLanding").style.display = "block";
    document.getElementById("viewStudentPortal").style.display = "none";
    document.getElementById("viewAdminPortal").style.display = "none";
    const tp = document.getElementById("viewTeacherPortal");
    if (tp) tp.style.display = "none";
    this.closeModals();
  }

  handleRoute() {
    const raw = window.location.hash.replace(/^#\/?/, "");
    if (!raw) {
      if (this.currentUser) {
        if (this.currentUser.role === "student") this.showStudentPortal();
        else if (this.currentUser.role === "teacher") this.showTeacherPortal();
        else if (this.currentUser.role === "admin") this.showAdminPortal();
      } else {
        this.showLanding();
      }
      return;
    }
    const parts = raw.split("/");
    const section = parts[0];
    const action = parts[1];

    if (section === "student") {
      if (action === "login") this.openStudentAuthModal("login");
      else if (action === "register") this.openStudentAuthModal("register");
      else if (action === "dashboard") {
        if (this.currentUser && this.currentUser.role === "student") this.showStudentPortal();
        else this.openStudentAuthModal("login");
      }
    } else if (section === "teacher") {
      if (action === "login") this.openTeacherAuthModal();
      else if (action === "dashboard") {
        if (this.currentUser && this.currentUser.role === "teacher") this.showTeacherPortal();
        else this.openTeacherAuthModal();
      }
    } else if (section === "admin") {
      if (action === "login") this.openAdminAuthModal();
      else if (action === "dashboard") {
        if (this.currentUser && this.currentUser.role === "admin") this.showAdminPortal();
        else this.openAdminAuthModal();
      }
    }
  }

  showTeacherPortal() {
    document.getElementById("viewLanding").style.display = "none";
    document.getElementById("viewStudentPortal").style.display = "none";
    document.getElementById("viewAdminPortal").style.display = "none";
    const tp = document.getElementById("viewTeacherPortal");
    if (tp) tp.style.display = "flex";

    const name = this.currentUser.teacher_name || this.currentUser.full_name || "Faculty Guide";
    const dept = this.currentUser.teacher_dept || this.currentUser.department || "Engineering";
    const desig = this.currentUser.designation || "Assistant Professor";

    const nameEl = document.getElementById("teacherNameDisplay");
    const deptEl = document.getElementById("teacherDeptDisplay");
    if (nameEl) nameEl.innerText = name;
    if (deptEl) deptEl.innerText = `${desig} · ${dept}`;

    this.switchTeacherTab("tTabDashboard");
  }

  showStudentPortal() {
    document.getElementById("viewLanding").style.display = "none";
    document.getElementById("viewAdminPortal").style.display = "none";
    document.getElementById("viewStudentPortal").style.display = "flex";

    const name = this.currentUser.full_name || "Student";
    const enr = this.currentUser.enrollment_no || "21CS042";
    const dept = this.currentUser.department || "CSE";
    const sem = this.currentUser.semester || 6;

    const welcomeEl = document.getElementById("studentWelcomeName");
    const sideName = document.getElementById("studentSidebarName");
    const sideEnr = document.getElementById("studentSidebarEnr");

    if (welcomeEl) welcomeEl.innerText = `Welcome, ${name}`;
    if (sideName) sideName.innerText = name;
    if (sideEnr) sideEnr.innerText = `${enr} · ${dept} Sem ${sem}`;

    // Profile page
    const pName = document.getElementById("profName");
    const pEmail = document.getElementById("profEmail");
    const pEnr = document.getElementById("profEnr");
    const pDept = document.getElementById("profDept");
    const pBranch = document.getElementById("profBranch");
    const pSem = document.getElementById("profSem");

    if (pName) pName.innerText = name;
    if (pEmail) pEmail.innerText = this.currentUser.email;
    if (pEnr) pEnr.value = enr;
    if (pDept) pDept.value = dept;
    if (pBranch) pBranch.value = this.currentUser.branch || "Systems & Architecture";
    if (pSem) pSem.value = `Semester ${sem}`;

    this.switchStudentTab("sTabDashboard");
  }

  showAdminPortal() {
    document.getElementById("viewLanding").style.display = "none";
    document.getElementById("viewStudentPortal").style.display = "none";
    document.getElementById("viewAdminPortal").style.display = "flex";

    this.switchAdminTab("aTabDashboard");
  }

  async logout() {
    try {
      await this.apiRequest("/api/auth/logout", "POST");
    } catch (e) {}
    localStorage.removeItem("apts_token");
    this.token = null;
    this.currentUser = null;
    this.showToast("Logged out successfully");
    this.showLanding();
  }

  // ==========================================================================
  // AUTH MODALS & USER CREDENTIALS
  // ==========================================================================
  openStudentAuthModal(tab = "login") {
    this.closeModals();
    this.toggleStudentAuthTab(tab);
    document.getElementById("studentAuthModal").classList.add("open");
  }

  toggleStudentAuthTab(tab) {
    const loginBox = document.getElementById("studentLoginBox");
    const regBox = document.getElementById("studentRegisterBox");
    const title = document.getElementById("studentAuthTitle");

    if (tab === "login") {
      loginBox.style.display = "block";
      regBox.style.display = "none";
      title.innerText = "Student Portal Login";
    } else {
      loginBox.style.display = "none";
      regBox.style.display = "block";
      title.innerText = "Register Student Account";
    }
  }

  openAdminAuthModal() {
    this.closeModals();
    document.getElementById("adminAuthModal").classList.add("open");
  }

  closeModals() {
    document.querySelectorAll(".modal-overlay").forEach(m => m.classList.remove("open"));
  }

  fillDemoStudentCreds() {
    document.getElementById("sLoginEmail").value = "aarav.patel@student.univ.edu";
    document.getElementById("sLoginPassword").value = "Student@2026!";
  }

  fillDemoAdminCreds() {
    document.getElementById("aLoginEmail").value = "admin@univ.edu";
    document.getElementById("aLoginPassword").value = "Admin@2026!";
  }

  async handleStudentLogin() {
    const email = document.getElementById("sLoginEmail").value.trim();
    const password = document.getElementById("sLoginPassword").value;

    try {
      const res = await this.apiRequest("/api/auth/login", "POST", {
        email,
        password,
        portal_type: "student"
      });

      if (res.success && res.token) {
        this.token = res.token;
        localStorage.setItem("apts_token", res.token);
        this.currentUser = res.user;
        this.closeModals();
        this.showToast(`Welcome back, ${res.user.full_name || res.user.email}!`);
        this.showStudentPortal();
      }
    } catch (err) {
      this.showToast(err.message || "Login failed");
    }
  }

  async handleStudentRegister() {
    const full_name = document.getElementById("sRegName").value.trim();
    const enrollment_no = document.getElementById("sRegEnr").value.trim();
    const email = document.getElementById("sRegEmail").value.trim();
    const password = document.getElementById("sRegPassword").value;
    const confirm_password = document.getElementById("sRegConfirmPassword").value;
    const department = document.getElementById("sRegDept").value;
    const branch = document.getElementById("sRegBranch").value.trim();
    const semester = parseInt(document.getElementById("sRegSemester").value);

    try {
      const res = await this.apiRequest("/api/auth/register", "POST", {
        full_name,
        enrollment_no,
        email,
        password,
        confirm_password,
        department,
        branch,
        semester
      });

      if (res.success && res.token) {
        this.token = res.token;
        localStorage.setItem("apts_token", res.token);
        this.currentUser = res.user;
        this.closeModals();
        this.showToast("Registration successful! Welcome to APTS.");
        this.showStudentPortal();
      }
    } catch (err) {
      this.showToast(err.message || "Registration failed");
    }
  }

  async handleAdminLogin() {
    const email = document.getElementById("aLoginEmail").value.trim();
    const password = document.getElementById("aLoginPassword").value;

    try {
      const res = await this.apiRequest("/api/auth/login", "POST", {
        email,
        password,
        portal_type: "admin"
      });

      if (res.success && res.token) {
        this.token = res.token;
        localStorage.setItem("apts_token", res.token);
        this.currentUser = res.user;
        this.closeModals();
        this.showToast("Faculty Command Center unlocked.");
        this.showAdminPortal();
      }
    } catch (err) {
      this.showToast(err.message || "Admin authorization failed");
    }
  }

  // ==========================================================================
  // STUDENT PORTAL NAVIGATION & VIEWS
  // ==========================================================================
  switchStudentTab(tabId) {
    this.currentStudentTab = tabId;
    document.querySelectorAll(".sidebar-nav-item").forEach(item => {
      if (item.dataset.stab === tabId) item.classList.add("active");
      else item.classList.remove("active");
    });

    document.querySelectorAll(".student-page-panel").forEach(p => {
      p.style.display = p.id === tabId ? "block" : "none";
    });

    const titles = {
      sTabDashboard: "Student Dashboard &bull; Capstone Overview",
      sTabSubmit: "Capstone Submission &bull; Code &amp; Testbench",
      sTabProjects: "My Submitted Capstone Projects",
      sTabTracking: "Visual Project Stage Tracking",
      sTabFeedback: "Faculty Feedback &amp; Rubric Evaluation",
      sTabNotifications: "Activity Stream &amp; Notifications",
      sTabProfile: "My Student Academic Profile",
      sTabLab: "Integrated Architecture Lab"
    };
    document.getElementById("studentTopTitle").innerHTML = titles[tabId] || "Student Workspace";

    if (tabId === "sTabDashboard") this.loadStudentDashboard();
    if (tabId === "sTabProjects") this.loadStudentProjects();
    if (tabId === "sTabTracking") this.loadStudentTrackingView();
    if (tabId === "sTabFeedback") this.loadStudentFeedbackView();
    if (tabId === "sTabNotifications") this.loadStudentNotifications();
  }

  async loadStudentDashboard() {
    try {
      const data = await this.apiRequest("/api/student/dashboard");
      if (!data.success) return;

      const m = data.metrics;
      document.getElementById("sKpiTotal").innerText = m.total_projects;
      const subEl = document.getElementById("sKpiSubmitted");
      if (subEl) subEl.innerText = m.total_projects;
      document.getElementById("sKpiReview").innerText = m.under_review;
      document.getElementById("sKpiApproved").innerText = m.approved;

      if (m.latest_grade) {
        document.getElementById("sKpiGrade").innerText = `Grade ${m.latest_grade.grade}`;
        document.getElementById("sKpiScore").innerText = `${m.latest_grade.total_score} / 100 Marks`;
      } else {
        document.getElementById("sKpiGrade").innerText = "Pending";
        document.getElementById("sKpiScore").innerText = "In review process";
      }

      this.projectsCache = data.projects || [];
      const tbody = document.getElementById("studentDashboardProjectsTable");
      if (!tbody) return;

      if (this.projectsCache.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2.5rem; color: var(--text-muted);">
          No projects submitted yet. Click "Submit Project" above to submit your first capstone.
        </td></tr>`;
        return;
      }

      tbody.innerHTML = this.projectsCache.map(p => `
        <tr>
          <td>
            <div style="font-weight: 700; color: var(--text-primary); font-size: 0.9rem;">${p.title}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${p.id}</div>
          </td>
          <td style="font-size: 0.8rem; color: var(--text-secondary);">${p.category}</td>
          <td style="font-size: 0.8rem;">${new Date(p.created_at).toLocaleDateString()}</td>
          <td><span class="status-pill status-${p.status.toLowerCase().replace(/\s+/g, '-')}">${p.status}</span></td>
          <td><strong style="color: var(--brand-blue);">${p.is_published ? `${p.total_score} M (${p.eval_grade})` : 'Under Review'}</strong></td>
          <td>
            <button class="btn btn-quiet" style="font-size: 0.75rem; padding: 3px 8px;" onclick="app.viewProjectTracking('${p.id}')">Track</button>
            <button class="btn btn-primary" style="font-size: 0.75rem; padding: 3px 8px; margin-left: 4px;" onclick="app.viewProjectFeedback('${p.id}')">Feedback</button>
          </td>
        </tr>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  async loadStudentProjects() {
    try {
      const data = await this.apiRequest("/api/student/projects");
      if (!data.success) return;
      this.projectsCache = data.projects || [];
      const tbody = document.getElementById("studentAllProjectsTable");
      if (!tbody) return;

      if (this.projectsCache.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color: var(--text-muted);">No capstones found.</td></tr>`;
        return;
      }

      tbody.innerHTML = this.projectsCache.map(p => `
        <tr>
          <td><strong>${p.id}</strong></td>
          <td>
            <div style="font-weight: 700;">${p.title}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${p.category}</div>
          </td>
          <td>v${p.submission_version || 1}</td>
          <td><span class="status-pill status-${p.status.toLowerCase().replace(/\s+/g, '-')}">${p.status}</span></td>
          <td><strong style="color: var(--brand-blue);">${p.is_published ? `${p.total_score}/100 (${p.grade})` : 'In Progress'}</strong></td>
          <td>
            <button class="btn btn-quiet" style="font-size: 0.75rem; padding: 3px 8px;" onclick="app.viewProjectTracking('${p.id}')">Track</button>
            ${p.status === 'Changes Requested' ? `<button class="btn btn-purple" style="font-size: 0.75rem; padding: 3px 8px; margin-left: 4px;" onclick="app.editProjectForResubmit('${p.id}')">Improve &amp; Resubmit</button>` : ''}
          </td>
        </tr>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  async uploadFile(fileInputId) {
    const input = document.getElementById(fileInputId);
    if (!input || !input.files || input.files.length === 0) return null;
    const file = input.files[0];
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const res = await this.apiRequest("/api/upload", "POST", {
            file_name: file.name,
            file_data: reader.result
          });
          if (res && res.success) {
            resolve(res.file_url);
          } else {
            resolve(null);
          }
        } catch (e) {
          console.warn("Upload fallback:", e);
          resolve(null);
        }
      };
      reader.onerror = () => resolve(null);
      reader.readAsDataURL(file);
    });
  }

  async handleProjectSubmit(isDraft = false) {
    const title = document.getElementById("subTitle").value.trim();
    const category = document.getElementById("subCategory").value;
    const abstract = document.getElementById("subAbstract").value.trim();
    const problem_statement = document.getElementById("subProblem").value.trim();
    const objectives = document.getElementById("subObjectives").value.trim();
    const technologies = document.getElementById("subTechnologies").value.trim();
    const team_members = document.getElementById("subTeam").value.trim();
    const repo_url = document.getElementById("subRepo").value.trim();
    const live_url = document.getElementById("subLive").value.trim();

    try {
      this.showToast("Uploading project documentation & files...", "info");
      const doc_file = (await this.uploadFile("subDocFile")) || "/uploads/sample_spec_doc.pdf";
      const presentation_file = (await this.uploadFile("subPresFile")) || "/uploads/sample_presentation.pptx";

      const payload = {
        title,
        category,
        abstract,
        problem_statement,
        objectives,
        technologies,
        team_members,
        repo_url,
        live_url,
        doc_file,
        presentation_file,
        is_draft: isDraft
      };

      const res = await this.apiRequest("/api/student/projects", "POST", payload);
      if (res.success) {
        this.showToast(`✅ ${res.message} (Reference ID: ${res.project_id})`, "success");
        document.getElementById("projectSubmissionForm").reset();
        await this.loadStudentProjects();
        this.selectedProjectId = res.project_id;
        this.switchStudentTab("sTabTracking");
      }
    } catch (err) {
      this.showToast(err.message || "Submission failed", "error");
    }
  }

  handleProjectDraft() {
    this.handleProjectSubmit(true);
  }

  async loadStudentTrackingView() {
    const sel = document.getElementById("trackProjectSelector");
    if (!sel) return;

    if (this.projectsCache.length === 0) {
      const data = await this.apiRequest("/api/student/projects");
      this.projectsCache = data.projects || [];
    }

    sel.innerHTML = this.projectsCache.map(p => `
      <option value="${p.id}" ${p.id === this.selectedProjectId ? 'selected' : ''}>${p.id} - ${p.title}</option>
    `).join("");

    const targetId = this.selectedProjectId || (this.projectsCache[0] ? this.projectsCache[0].id : null);
    if (targetId) this.loadProjectTracking(targetId);
  }

  viewProjectTracking(id) {
    this.selectedProjectId = id;
    this.switchStudentTab("sTabTracking");
  }

  async loadProjectTracking(projectId) {
    if (!projectId) return;
    try {
      const data = await this.apiRequest(`/api/student/projects/${projectId}/tracking`);
      if (!data.success) return;

      const p = data.project;
      this.currentTrackingProject = p;
      const evalData = data.evaluation;
      const history = data.history || [];
      const versions = data.versions || [];

      // 1. Changes Requested Banner
      const chgBanner = document.getElementById("trackingChangesBanner");
      if (chgBanner) {
        if (p.status === "Changes Requested") {
          chgBanner.style.display = "block";
          const latestHistory = history[history.length - 1];
          const bannerMsg = document.getElementById("trackingChangesBannerMsg");
          if (bannerMsg) {
            bannerMsg.innerText = latestHistory && latestHistory.notes 
              ? `Faculty Directive: "${latestHistory.notes}"`
              : "Faculty reviewed your submission and requested improvements before Viva.";
          }
        } else {
          chgBanner.style.display = "none";
        }
      }

      // 2. Update Stepper (7 Stages)
      const stepIds = [
        "stepNodeDraft", "stepNodeSubmitted", "stepNodeReview",
        "stepNodeChanges", "stepNodeResubmitted", "stepNodeApproved", "stepNodeGraded"
      ];
      stepIds.forEach(sid => {
        const el = document.getElementById(sid);
        if (el) el.className = "step-node";
      });

      const order = ["Draft", "Submitted", "Under Review", "Changes Requested", "Resubmitted", "Approved", "Graded"];
      const currentIdx = order.indexOf(p.status);

      order.forEach((st, idx) => {
        const sid = stepIds[idx];
        const el = document.getElementById(sid);
        if (!el) return;
        if (p.status === "Changes Requested" && st === "Changes Requested") {
          el.className = "step-node active";
        } else if (idx < currentIdx) {
          el.className = "step-node completed";
        } else if (idx === currentIdx) {
          el.className = "step-node active";
        }
      });

      // 3. F. Final Grade Card
      const gradeCard = document.getElementById("trackingFinalGradeCard");
      if (gradeCard) {
        if (evalData && evalData.is_published) {
          gradeCard.style.display = "block";
          gradeCard.innerHTML = `
            <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.12), rgba(100, 124, 255, 0.08)); border: 1px solid var(--brand-blue); border-radius: var(--radius-lg); padding: 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
              <div>
                <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: var(--brand-blue);">Official University Grade Released</div>
                <div style="font-size: 2.25rem; font-weight: 800; color: var(--text-primary); margin: 0.25rem 0;">
                  ${evalData.total_score} <span style="font-size: 1.15rem; color: var(--text-muted);">/ 100 Marks</span>
                </div>
                <div style="font-size: 0.85rem; color: var(--text-secondary);">
                  Evaluation verified and officially accredited for <strong>${p.title}</strong>
                </div>
              </div>
              <div style="text-align: right;">
                <span class="status-pill status-approved" style="font-size: 1.25rem; padding: 0.5rem 1.25rem; font-weight: 800;">
                  Grade ${evalData.grade}
                </span>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">
                  Published on ${new Date(evalData.updated_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          `;
        } else {
          gradeCard.style.display = "block";
          gradeCard.innerHTML = `
            <div style="background: var(--bg-surface); border: 1px solid var(--border-app); border-radius: var(--radius-md); padding: 1rem 1.25rem; display: flex; align-items: center; gap: 1rem;">
              <span style="font-size: 1.5rem;">⏳</span>
              <div>
                <div style="font-weight: 700; font-size: 0.9rem;">Evaluation In Progress</div>
                <div style="font-size: 0.8rem; color: var(--text-secondary);">Faculty evaluation panel has not published final 100-mark scores yet. Status: <strong>${p.status}</strong></div>
              </div>
            </div>
          `;
        }
      }

      // 4. B. Project Status Distribution Chart (Real Data)
      const chartB = document.getElementById("studentStatusChartContainer");
      if (chartB) {
        const counts = { Submitted: 0, "Under Review": 0, "Changes Requested": 0, Approved: 0, Graded: 0, Draft: 0 };
        this.projectsCache.forEach(pr => {
          if (counts[pr.status] !== undefined) counts[pr.status]++;
          else counts[pr.status] = 1;
        });
        const totalP = this.projectsCache.length || 1;

        chartB.innerHTML = `
          <div style="width: 100%; display: flex; flex-direction: column; gap: 0.65rem;">
            ${Object.entries(counts).map(([st, cnt]) => `
              <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 3px;">
                  <span>${st}</span>
                  <strong>${cnt} (${Math.round((cnt / totalP) * 100)}%)</strong>
                </div>
                <div class="progress-bar-bg" style="height: 6px;">
                  <div class="progress-bar-fill" style="width: ${(cnt / totalP) * 100}%; background: ${st === 'Graded' ? 'var(--brand-blue)' : st === 'Approved' ? 'var(--accent-emerald)' : st === 'Changes Requested' ? 'var(--accent-rose)' : 'var(--brand-purple)'};"></div>
                </div>
              </div>
            `).join("")}
          </div>
        `;
      }

      // 5. C. Evaluation Marks Chart (Real Data)
      const chartC = document.getElementById("studentRubricMarksChartContainer");
      if (chartC) {
        if (evalData && evalData.is_published) {
          const criteria = [
            { name: "Problem Statement (15)", score: evalData.problem_statement_score, max: 15 },
            { name: "Implementation (25)", score: evalData.implementation_score, max: 25 },
            { name: "Innovation (15)", score: evalData.innovation_score, max: 15 },
            { name: "Documentation (15)", score: evalData.documentation_score, max: 15 },
            { name: "UI/UX Design (10)", score: evalData.ui_ux_score, max: 10 },
            { name: "Presentation (10)", score: evalData.presentation_score, max: 10 },
            { name: "Completeness (10)", score: evalData.completeness_score, max: 10 }
          ];

          chartC.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
              ${criteria.map(c => `
                <div>
                  <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 2px;">
                    <span>${c.name}</span>
                    <strong style="color: var(--brand-blue);">${c.score} / ${c.max}</strong>
                  </div>
                  <div class="progress-bar-bg" style="height: 5px;">
                    <div class="progress-bar-fill" style="width: ${(c.score / c.max) * 100}%;"></div>
                  </div>
                </div>
              `).join("")}
            </div>
          `;
        } else {
          chartC.innerHTML = `
            <div style="text-align: center; padding: 2rem 1rem; color: var(--text-muted);">
              <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📊</div>
              <div style="font-size: 0.85rem;">Marks chart will populate once faculty publishes evaluation.</div>
              <div style="font-size: 0.75rem; margin-top: 0.25rem;">Standard 100-mark rubric: 15 + 25 + 15 + 15 + 10 + 10 + 10</div>
            </div>
          `;
        }
      }

      // 6. G. Progress Timeline Chart
      const chartG = document.getElementById("studentProgressTimelineContainer");
      if (chartG) {
        chartG.innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 0.5rem;">
            ${history.map((h, i) => `
              <div style="display: flex; align-items: center; gap: 0.75rem; font-size: 0.8rem;">
                <span style="width: 20px; height: 20px; border-radius: 50%; background: var(--bg-card); border: 1px solid var(--brand-blue); color: var(--brand-blue); display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700;">${i + 1}</span>
                <span style="font-weight: 600; color: var(--text-primary); width: 110px;">${h.to_status}</span>
                <span style="color: var(--text-muted); font-size: 0.725rem;">${new Date(h.created_at).toLocaleDateString()}</span>
              </div>
            `).join("")}
          </div>
        `;
      }

      // 7. H. Provenance & Version Ledger
      const chartH = document.getElementById("studentVersionHistoryContainer");
      if (chartH) {
        if (versions.length === 0) {
          chartH.innerHTML = `<div style="font-size: 0.8rem; color: var(--text-muted);">Current active version: v${p.submission_version || 1}</div>`;
        } else {
          chartH.innerHTML = versions.map(v => `
            <div style="background: var(--bg-card); padding: 0.65rem 0.85rem; border-radius: var(--radius-sm); border: 1px solid var(--border-app); font-size: 0.8rem;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: var(--brand-blue);">Version ${v.version_number}</strong>
                <span style="font-size: 0.7rem; color: var(--text-muted);">${new Date(v.submitted_at).toLocaleDateString()}</span>
              </div>
              <div style="color: var(--text-secondary); font-size: 0.75rem; margin-top: 3px;">${v.changelog || 'Project submission snapshot'}</div>
              ${v.doc_file ? `<a href="${v.doc_file}" target="_blank" style="font-size: 0.725rem; color: var(--brand-blue); text-decoration: none; margin-top: 4px; display: inline-block;">📄 Spec PDF</a>` : ''}
            </div>
          `).join("");
        }
      }


      // 5. E. Admin Feedback Panel
      const feedbackPanel = document.getElementById("trackingAdminFeedbackPanel");
      if (feedbackPanel) {
        if (evalData && evalData.is_published) {
          feedbackPanel.innerHTML = `
            <div class="card-panel" style="border-color: rgba(0, 212, 255, 0.3);">
              <div class="card-panel-header">
                <div class="card-panel-title"><span>💬</span> E. Faculty Evaluation Feedback</div>
                <span class="status-pill status-approved">Official Feedback</span>
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                <div style="background: var(--bg-surface); padding: 1rem; border-radius: var(--radius-md);">
                  <strong style="color: var(--accent-emerald); font-size: 0.8rem; display: block; margin-bottom: 0.35rem;">✓ Identified Strengths</strong>
                  <div style="font-size: 0.85rem; color: var(--text-secondary);">${evalData.strengths || "Strong architectural design and clear methodology."}</div>
                </div>
                <div style="background: var(--bg-surface); padding: 1rem; border-radius: var(--radius-md);">
                  <strong style="color: var(--accent-amber); font-size: 0.8rem; display: block; margin-bottom: 0.35rem;">⚠ Weaknesses &amp; Improvements</strong>
                  <div style="font-size: 0.85rem; color: var(--text-secondary);">${evalData.weaknesses || evalData.recommended_improvements || "Maintain test coverage and complete edge case benchmarks."}</div>
                </div>
              </div>
              ${evalData.overall_feedback ? `
                <div style="background: var(--bg-surface); padding: 1rem; border-radius: var(--radius-md);">
                  <strong style="color: var(--brand-blue); font-size: 0.8rem; display: block; margin-bottom: 0.35rem;">General Evaluator Comments</strong>
                  <div style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5;">${evalData.overall_feedback}</div>
                </div>
              ` : ''}
            </div>
          `;
        } else {
          feedbackPanel.innerHTML = "";
        }
      }

      // 6. D. Submission History (Chronological Audit Log)
      const histDiv = document.getElementById("trackingTimelineEvents");
      if (histDiv) {
        if (history.length === 0) {
          histDiv.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">No lifecycle audit events recorded yet.</div>`;
        } else {
          histDiv.innerHTML = history.map(h => `
            <div style="background: var(--bg-surface); padding: 1rem 1.25rem; border-radius: var(--radius-md); border-left: 3px solid var(--brand-blue);">
              <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                <span class="status-pill status-${(h.to_status || 'submitted').toLowerCase().replace(/\s+/g, '-')}">${h.to_status}</span>
                <span style="color: var(--text-muted);">${new Date(h.created_at).toLocaleString()}</span>
              </div>
              <div style="font-size: 0.85rem; color: var(--text-primary); margin-top: 0.5rem; line-height: 1.4;">${h.notes}</div>
              <div style="font-size: 0.725rem; color: var(--text-muted); margin-top: 0.35rem;">Action Author: ${h.user_name || h.user_email || 'System Authority'}</div>
            </div>
          `).join("");
        }
      }
    } catch (e) {
      console.error("Tracking Error:", e);
    }
  }

  openResubmitModal() {
    const p = this.currentTrackingProject;
    if (!p) {
      this.showToast("Please select a capstone project first.");
      return;
    }
    const pidEl = document.getElementById("resubProjectId");
    if (pidEl) pidEl.value = p.id;
    const titleModal = document.getElementById("resubModalTitle");
    if (titleModal) titleModal.innerText = `Submit Improved Revision: ${p.id}`;

    const tEl = document.getElementById("resubTitle");
    if (tEl) tEl.value = p.title || "";
    const cEl = document.getElementById("resubCategory");
    if (cEl) cEl.value = p.category || "";
    const aEl = document.getElementById("resubAbstract");
    if (aEl) aEl.value = p.abstract || "";
    const rEl = document.getElementById("resubRepo");
    if (rEl) rEl.value = p.repo_url || "";
    const lEl = document.getElementById("resubLive");
    if (lEl) lEl.value = p.live_url || "";
    const chgEl = document.getElementById("resubChangelog");
    if (chgEl) chgEl.value = "";

    document.getElementById("studentResubmitModal").classList.add("open");
  }

  async handleProjectResubmit() {
    const projectId = document.getElementById("resubProjectId").value;
    if (!projectId) {
      this.showToast("Project ID missing for resubmission.");
      return;
    }

    const changelog = document.getElementById("resubChangelog").value.trim();
    if (!changelog) {
      this.showToast("Please describe the improvements made in this revision.");
      return;
    }

    try {
      this.showToast("Uploading project files & saving revision...");
      let doc_file = await this.uploadFile("resubDocFile");
      let presentation_file = await this.uploadFile("resubPresFile");

      const payload = {
        title: document.getElementById("resubTitle").value.trim(),
        category: document.getElementById("resubCategory").value.trim(),
        abstract: document.getElementById("resubAbstract").value.trim(),
        repo_url: document.getElementById("resubRepo").value.trim(),
        live_url: document.getElementById("resubLive").value.trim(),
        changelog: changelog
      };
      if (doc_file) payload.doc_file = doc_file;
      if (presentation_file) payload.presentation_file = presentation_file;

      const res = await this.apiRequest(`/api/student/projects/${projectId}/resubmit`, "POST", payload);
      if (res.success) {
        this.showToast(`Revision submitted successfully! Project status updated.`);
        this.closeModals();
        this.projectsCache = [];
        await this.loadStudentProjects();
        this.loadProjectTracking(projectId);
      }
    } catch (err) {
      this.showToast(err.message || "Failed to resubmit project revision.");
    }
  }

  async loadStudentFeedbackView() {
    const sel = document.getElementById("feedbackProjectSelector");
    if (!sel) return;

    if (this.projectsCache.length === 0) {
      const data = await this.apiRequest("/api/student/projects");
      this.projectsCache = data.projects || [];
    }

    sel.innerHTML = this.projectsCache.map(p => `
      <option value="${p.id}" ${p.id === this.selectedProjectId ? 'selected' : ''}>${p.id} - ${p.title}</option>
    `).join("");

    const targetId = this.selectedProjectId || (this.projectsCache[0] ? this.projectsCache[0].id : null);
    if (targetId) this.loadStudentFeedback(targetId);
  }

  viewProjectFeedback(id) {
    this.selectedProjectId = id;
    this.switchStudentTab("sTabFeedback");
  }

  async loadStudentFeedback(projectId) {
    if (!projectId) return;
    try {
      const data = await this.apiRequest(`/api/student/projects/${projectId}/tracking`);
      const container = document.getElementById("studentFeedbackContent");
      if (!container) return;

      const evalData = data.evaluation;
      if (!evalData) {
        container.innerHTML = `
          <div style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
            <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">⏳</div>
            <h3>Evaluation Pending Publication</h3>
            <p style="max-width: 500px; margin: 0.5rem auto;">
              The faculty evaluation committee has not published final marks for this capstone yet. Marks and feedback will appear here immediately once verified.
            </p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; background: var(--bg-surface); padding: 1.5rem; border-radius: var(--radius-md); border: 1px solid var(--border-app); margin-bottom: 1.5rem;">
          <div>
            <div style="font-size: 0.8rem; color: var(--text-muted);">FINAL ACCREDITATION SCORE</div>
            <div style="font-size: 2.5rem; font-weight: 800; color: var(--brand-blue);">${evalData.total_score} <span style="font-size: 1.25rem; color: var(--text-muted);">/ 100</span></div>
          </div>
          <div>
            <span class="status-pill status-approved" style="font-size: 1.2rem; padding: 8px 20px;">Grade ${evalData.grade}</span>
          </div>
        </div>

        <div class="card-panel">
          <h4 style="margin-bottom: 1rem;">100-Mark Rubric Breakdown</h4>
          <div class="criteria-bar-item">
            <div class="criteria-bar-header"><span>1. Problem Statement (Max 15)</span><strong>${evalData.problem_statement_score} / 15</strong></div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${(evalData.problem_statement_score / 15) * 100}%;"></div></div>
          </div>
          <div class="criteria-bar-item">
            <div class="criteria-bar-header"><span>2. Implementation &amp; Synthesis (Max 25)</span><strong>${evalData.implementation_score} / 25</strong></div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${(evalData.implementation_score / 25) * 100}%;"></div></div>
          </div>
          <div class="criteria-bar-item">
            <div class="criteria-bar-header"><span>3. Innovation &amp; Optimization (Max 15)</span><strong>${evalData.innovation_score} / 15</strong></div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${(evalData.innovation_score / 15) * 100}%;"></div></div>
          </div>
          <div class="criteria-bar-item">
            <div class="criteria-bar-header"><span>4. Documentation &amp; Logs (Max 15)</span><strong>${evalData.documentation_score} / 15</strong></div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${(evalData.documentation_score / 15) * 100}%;"></div></div>
          </div>
          <div class="criteria-bar-item">
            <div class="criteria-bar-header"><span>5. UI/UX Design &amp; Telemetry (Max 10)</span><strong>${evalData.ui_ux_score} / 10</strong></div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${(evalData.ui_ux_score / 10) * 100}%;"></div></div>
          </div>
          <div class="criteria-bar-item">
            <div class="criteria-bar-header"><span>6. Presentation &amp; Viva Voce (Max 10)</span><strong>${evalData.presentation_score} / 10</strong></div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${(evalData.presentation_score / 10) * 100}%;"></div></div>
          </div>
          <div class="criteria-bar-item">
            <div class="criteria-bar-header"><span>7. Deliverables &amp; Completeness (Max 10)</span><strong>${evalData.completeness_score} / 10</strong></div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${(evalData.completeness_score / 10) * 100}%;"></div></div>
          </div>
        </div>

        <div class="card-panel">
          <h4 style="margin-bottom: 0.5rem;">Faculty Feedback &amp; Suggestions</h4>
          <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.6;">${evalData.overall_feedback || 'No written feedback provided.'}</p>
          
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
            <div style="background: var(--bg-surface); padding: 1rem; border-radius: var(--radius-md);">
              <div style="font-weight: 700; color: var(--accent-emerald); font-size: 0.85rem;">Key Strengths</div>
              <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">${evalData.strengths || 'N/A'}</div>
            </div>
            <div style="background: var(--bg-surface); padding: 1rem; border-radius: var(--radius-md);">
              <div style="font-weight: 700; color: var(--accent-amber); font-size: 0.85rem;">Recommended Improvements</div>
              <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">${evalData.recommended_improvements || 'N/A'}</div>
            </div>
          </div>
        </div>
      `;
    } catch (e) {
      console.error(e);
    }
  }

  async loadStudentNotifications() {
    try {
      const data = await this.apiRequest("/api/student/notifications");
      const list = document.getElementById("studentNotificationsList");
      const badge = document.getElementById("studentNotifBadge");
      if (!list) return;

      const notifs = data.notifications || [];
      const unreadCount = notifs.filter(n => !n.is_read).length;
      if (badge) badge.innerText = unreadCount;

      if (notifs.length === 0) {
        list.innerHTML = `<div style="text-align:center; padding: 2rem; color: var(--text-muted);">No notifications yet.</div>`;
        return;
      }

      list.innerHTML = notifs.map(n => `
        <div style="background: var(--bg-surface); padding: 1rem; border-radius: var(--radius-md); border-left: 3px solid ${n.is_read ? 'var(--border-app)' : 'var(--brand-blue)'};">
          <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
            <strong>${n.title}</strong>
            <span style="color: var(--text-muted); font-size: 0.75rem;">${new Date(n.created_at).toLocaleString()}</span>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.35rem;">${n.message}</div>
        </div>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  async markAllNotificationsRead() {
    try {
      await this.apiRequest("/api/student/notifications/read", "POST", {});
      this.loadStudentNotifications();
      this.showToast("Notifications marked as read");
    } catch (e) {}
  }

  // ==========================================================================
  // ADMIN PORTAL NAVIGATION & ACTIONS (NO DEPLOY OPTION)
  // ==========================================================================
  switchAdminTab(tabId) {
    this.currentAdminTab = tabId;
    document.querySelectorAll(".sidebar-nav-item").forEach(item => {
      if (item.dataset.atab === tabId) item.classList.add("active");
      else item.classList.remove("active");
    });

    document.querySelectorAll(".admin-page-panel").forEach(p => {
      p.style.display = p.id === tabId ? "block" : "none";
    });

    const titles = {
      aTabDashboard: "Faculty Admin Command Center &bull; Cohort Overview",
      aTabStudents: "All Registered B.Tech Students",
      aTabProjects: "All Submitted Capstones Directory",
      aTabPending: "Priority Review Queue &bull; Awaiting Faculty Action",
      aTabReview: "Capstones Under Technical Review",
      aTabEvaluation: "Standardized 100-Mark Rubric Evaluator",
      aTabApproved: "Approved Capstones Cleared for Viva Voce",
      aTabRejected: "Rejected Capstone Submissions",
      aTabAnalytics: "Cohort Performance Analytics &amp; Reports"
    };
    document.getElementById("adminTopTitle").innerHTML = titles[tabId] || "Faculty Command";

    if (tabId === "aTabDashboard") this.loadAdminDashboard();
    if (tabId === "aTabStudents") this.loadAdminStudents();
    if (tabId === "aTabTeachers") this.loadAdminTeachers();
    if (tabId === "aTabAssignments") this.loadAdminAssignments();
    if (tabId === "aTabProjects") this.loadAdminProjects();
    if (tabId === "aTabPending") this.loadAdminFilteredProjects("Submitted", "adminPendingTable");
    if (tabId === "aTabReview") this.loadAdminFilteredProjects("Under Review", "adminUnderReviewTable");
    if (tabId === "aTabEvaluation") this.loadAdminEvaluationView();
    if (tabId === "aTabApproved") this.loadAdminFilteredProjects("Approved", "adminApprovedTable");
    if (tabId === "aTabRejected") this.loadAdminFilteredProjects("Rejected", "adminRejectedTable");
    if (tabId === "aTabAnalytics") this.loadAdminAnalytics();
    if (tabId === "aTabSettings") this.loadInstitutionSettings();
  }

  async loadAdminDashboard() {
    try {
      const data = await this.apiRequest("/api/admin/dashboard");
      if (!data.success) return;

      const m = data.metrics;
      document.getElementById("aKpiStudents").innerText = m.total_students;
      document.getElementById("aKpiProjects").innerText = m.total_projects;
      document.getElementById("aKpiPending").innerText = m.pending_reviews;
      const appEl = document.getElementById("aKpiApproved");
      if (appEl) appEl.innerText = m.approved;
      const rejEl = document.getElementById("aKpiRejected");
      if (rejEl) rejEl.innerText = m.rejected;
      const avgEl = document.getElementById("aKpiAvgScore");
      if (avgEl) avgEl.innerText = m.average_score !== null && m.average_score !== undefined ? m.average_score.toFixed(1) : "N/A";

      const badge = document.getElementById("adminPendingBadge");
      if (badge) badge.innerText = m.pending_reviews;

      const tbody = document.getElementById("adminQuickReviewTable");
      if (!tbody) return;

      const recent = data.recent_projects || [];
      if (recent.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 2rem; color: var(--text-muted);">No submissions awaiting review in queue.</td></tr>`;
        return;
      }

      tbody.innerHTML = recent.map(p => {
        let actionBtn = `<button class="btn btn-purple" style="font-size: 0.75rem; padding: 3px 8px;" onclick="app.openAdminReviewModal('${p.id}')">Review &amp; Verify</button>`;
        if (p.status === "Under Review") {
          actionBtn = `<button class="btn btn-emerald" style="font-size: 0.75rem; padding: 3px 8px;" onclick="app.openAdminReviewModal('${p.id}')">Continue Review</button>`;
        } else if (p.status === "Changes Requested") {
          actionBtn = `<button class="btn btn-quiet" style="font-size: 0.75rem; padding: 3px 8px; color: var(--accent-amber);" onclick="app.openAdminReviewModal('${p.id}')">Awaiting Resubmission</button>`;
        } else if (p.status === "Approved") {
          actionBtn = `<button class="btn btn-primary" style="font-size: 0.75rem; padding: 3px 8px;" onclick="app.openAdminReviewModal('${p.id}')">Schedule Viva</button>`;
        } else if (p.status === "Graded") {
          actionBtn = `<button class="btn btn-quiet" style="font-size: 0.75rem; padding: 3px 8px;" onclick="app.openAdminReviewModal('${p.id}')">View Evaluation</button>`;
        }
        return `
        <tr>
          <td>
            <div style="font-weight: 700;">${p.title}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${p.id}</div>
          </td>
          <td>${p.student_name} (${p.enrollment_no})</td>
          <td>${p.department}</td>
          <td><span class="status-pill status-${p.status.toLowerCase().replace(/\s+/g, '-')}">${p.status}</span></td>
          <td>${actionBtn}</td>
        </tr>
      `}).join("");
    } catch (e) {
      console.error(e);
    }
  }

  async loadAdminStudents() {
    try {
      const data = await this.apiRequest("/api/admin/students");
      this.adminStudentsCache = data.students || [];
      this.renderAdminStudentsTable(this.adminStudentsCache);
    } catch (e) {
      console.error(e);
      this.showToast("Failed to load students", "error");
    }
  }

  renderAdminStudentsTable(students) {
    const tbody = document.getElementById("adminStudentsTable");
    if (!tbody) return;

    if (!students || students.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No students found matching current filter.</td></tr>`;
      return;
    }

    tbody.innerHTML = students.map(s => `
      <tr>
        <td>
          <strong>${s.full_name}</strong><br>
          <span style="font-size:0.75rem; color: var(--brand-blue);">${s.enrollment_no}</span>
        </td>
        <td>
          ${s.email}<br>
          <span style="font-size:0.75rem; color: var(--text-muted);">${s.phone || 'No phone'}</span>
        </td>
        <td>
          ${s.department}<br>
          <span style="font-size:0.75rem; color: var(--text-muted);">${s.branch} · Sem ${s.semester} ${s.section ? `(${s.section})` : ''}</span>
        </td>
        <td>
          ${s.assigned_teacher ? `<span style="color: #10B981; font-weight: 600;">👨‍🏫 ${s.assigned_teacher}</span>` : `<span style="color: var(--text-muted); font-size: 0.8rem;">Unassigned</span>`}
        </td>
        <td>
          <span class="badge-counter">${s.total_projects || 0}</span>
        </td>
        <td>
          <span class="badge ${s.is_active ? 'badge-success' : 'badge-danger'}">
            ${s.is_active ? 'Active' : 'Inactive'}
          </span>
        </td>
        <td>
          <div style="display: flex; gap: 0.35rem; flex-wrap: wrap;">
            <button class="btn btn-quiet" style="font-size: 0.72rem; padding: 3px 8px;" onclick="app.adminToggleStudentStatus(${s.id}, ${s.is_active ? 1 : 0})">
              ${s.is_active ? 'Deactivate' : 'Activate'}
            </button>
            <button class="btn btn-quiet" style="font-size: 0.72rem; padding: 3px 8px; color: var(--brand-purple);" onclick="app.adminOpenResetPassword(${s.id}, '${s.full_name.replace(/'/g, "\\'")}', 'student')">
              Reset Key
            </button>
          </div>
        </td>
      </tr>
    `).join("");
  }

  filterAdminStudents() {
    const q = (document.getElementById("adminStudentSearch")?.value || "").toLowerCase().trim();
    const dept = document.getElementById("adminStudentDeptFilter")?.value || "all";

    let list = this.adminStudentsCache || [];
    if (dept !== "all") {
      list = list.filter(s => s.department === dept);
    }
    if (q) {
      list = list.filter(s =>
        (s.full_name && s.full_name.toLowerCase().includes(q)) ||
        (s.enrollment_no && s.enrollment_no.toLowerCase().includes(q)) ||
        (s.email && s.email.toLowerCase().includes(q))
      );
    }
    this.renderAdminStudentsTable(list);
  }

  openAddStudentModal() {
    this.closeModals();
    const modal = document.getElementById("adminAddStudentModal");
    if (modal) modal.classList.add("active");
  }

  async handleAdminAddStudent() {
    const payload = {
      full_name: document.getElementById("mStudentName").value.trim(),
      enrollment_no: document.getElementById("mStudentEnr").value.trim(),
      email: document.getElementById("mStudentEmail").value.trim(),
      phone: document.getElementById("mStudentPhone").value.trim(),
      department: document.getElementById("mStudentDept").value,
      branch: document.getElementById("mStudentBranch").value.trim(),
      semester: parseInt(document.getElementById("mStudentSemester").value, 10),
      section: document.getElementById("mStudentSection").value.trim(),
      temp_password: document.getElementById("mStudentTempPassword").value
    };

    try {
      const res = await this.apiRequest("/api/admin/students", "POST", payload);
      if (res.success) {
        this.showToast(`Student created: ${payload.full_name}`);
        this.closeModals();
        this.loadAdminStudents();
      }
    } catch (err) {
      this.showToast(err.message, "error");
    }
  }

  async adminToggleStudentStatus(studentId, isCurrentlyActive) {
    const newStatus = isCurrentlyActive ? 0 : 1;
    try {
      const res = await this.apiRequest(`/api/admin/students/${studentId}/status`, "POST", { is_active: newStatus });
      if (res.success) {
        this.showToast(res.message);
        this.loadAdminStudents();
      }
    } catch (err) {
      this.showToast(err.message, "error");
    }
  }

  // ==========================================================================
  // ADMIN TEACHER MANAGEMENT
  // ==========================================================================
  async loadAdminTeachers() {
    try {
      const data = await this.apiRequest("/api/admin/teachers");
      this.adminTeachersCache = data.teachers || [];
      this.renderAdminTeachersTable(this.adminTeachersCache);
    } catch (e) {
      console.error(e);
      this.showToast("Failed to load teachers", "error");
    }
  }

  renderAdminTeachersTable(teachers) {
    const tbody = document.getElementById("adminTeachersTable");
    if (!tbody) return;

    if (!teachers || teachers.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No faculty records registered yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = teachers.map(t => `
      <tr>
        <td>
          <strong style="color: #10B981;">${t.full_name}</strong><br>
          <span style="font-size:0.75rem; color: var(--text-muted);">${t.faculty_id}</span>
        </td>
        <td>
          ${t.email}<br>
          <span style="font-size:0.75rem; color: var(--text-muted);">${t.phone || 'No phone'}</span>
        </td>
        <td>
          ${t.department}<br>
          <span style="font-size:0.75rem; color: var(--brand-purple);">${t.designation}</span>
        </td>
        <td>
          <span style="font-size: 0.85rem;">${t.specialization || 'General'}</span>
        </td>
        <td>
          <span class="badge-counter" style="background: rgba(16, 185, 129, 0.2); color: #10B981;">
            ${t.assigned_students || 0} Students
          </span>
        </td>
        <td>
          <span class="badge ${t.is_active ? 'badge-success' : 'badge-danger'}">
            ${t.is_active ? 'Active' : 'Inactive'}
          </span>
        </td>
        <td>
          <div style="display: flex; gap: 0.35rem; flex-wrap: wrap;">
            <button class="btn btn-quiet" style="font-size: 0.72rem; padding: 3px 8px;" onclick="app.adminToggleTeacherStatus(${t.id}, ${t.is_active ? 1 : 0})">
              ${t.is_active ? 'Deactivate' : 'Activate'}
            </button>
            <button class="btn btn-quiet" style="font-size: 0.72rem; padding: 3px 8px; color: var(--brand-purple);" onclick="app.adminOpenResetPassword(${t.id}, '${t.full_name.replace(/'/g, "\\'")}', 'teacher')">
              Reset Key
            </button>
          </div>
        </td>
      </tr>
    `).join("");
  }

  filterAdminTeachers() {
    const q = (document.getElementById("adminTeacherSearch")?.value || "").toLowerCase().trim();
    let list = this.adminTeachersCache || [];
    if (q) {
      list = list.filter(t =>
        (t.full_name && t.full_name.toLowerCase().includes(q)) ||
        (t.faculty_id && t.faculty_id.toLowerCase().includes(q)) ||
        (t.email && t.email.toLowerCase().includes(q)) ||
        (t.department && t.department.toLowerCase().includes(q))
      );
    }
    this.renderAdminTeachersTable(list);
  }

  openAddTeacherModal() {
    this.closeModals();
    const modal = document.getElementById("adminAddTeacherModal");
    if (modal) modal.classList.add("active");
  }

  async handleAdminAddTeacher() {
    const payload = {
      full_name: document.getElementById("mTeacherName").value.trim(),
      faculty_id: document.getElementById("mTeacherFacId").value.trim(),
      email: document.getElementById("mTeacherEmail").value.trim(),
      phone: document.getElementById("mTeacherPhone").value.trim(),
      department: document.getElementById("mTeacherDept").value,
      designation: document.getElementById("mTeacherDesignation").value,
      specialization: document.getElementById("mTeacherSpec").value.trim(),
      temp_password: document.getElementById("mTeacherTempPassword").value
    };

    try {
      const res = await this.apiRequest("/api/admin/teachers", "POST", payload);
      if (res.success) {
        this.showToast(`Faculty registered: ${payload.full_name}`);
        this.closeModals();
        this.loadAdminTeachers();
      }
    } catch (err) {
      this.showToast(err.message, "error");
    }
  }

  async adminToggleTeacherStatus(teacherId, isCurrentlyActive) {
    const newStatus = isCurrentlyActive ? 0 : 1;
    try {
      const res = await this.apiRequest(`/api/admin/teachers/${teacherId}/status`, "POST", { is_active: newStatus });
      if (res.success) {
        this.showToast(res.message);
        this.loadAdminTeachers();
      }
    } catch (err) {
      this.showToast(err.message, "error");
    }
  }

  // ==========================================================================
  // ADMIN ASSIGNMENT MANAGEMENT
  // ==========================================================================
  async loadAdminAssignments() {
    try {
      const data = await this.apiRequest("/api/admin/assignments");
      const tbody = document.getElementById("adminAssignmentsTable");
      if (!tbody) return;

      if (!data.assignments || data.assignments.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No teacher-student assignments created yet.</td></tr>`;
        return;
      }

      tbody.innerHTML = data.assignments.map(a => `
        <tr>
          <td>
            <strong style="color: #10B981;">${a.teacher_name}</strong><br>
            <span style="font-size: 0.75rem; color: var(--text-muted);">${a.faculty_id}</span>
          </td>
          <td>
            <strong>${a.student_name}</strong><br>
            <span style="font-size: 0.75rem; color: var(--brand-blue);">${a.enrollment_no}</span>
          </td>
          <td>
            ${a.project_title ? `<strong>${a.project_title}</strong><br><span style="font-size:0.75rem; color:var(--text-muted);">${a.project_id} · ${a.project_status}</span>` : '<span style="color:var(--text-muted); font-size:0.8rem;">All Cohort Projects</span>'}
          </td>
          <td>
            ${a.deadline ? `<span style="color: var(--status-warning); font-size: 0.85rem; font-weight: 600;">📅 ${a.deadline}</span>` : '<span style="color:var(--text-muted); font-size:0.8rem;">Open</span>'}
          </td>
          <td>
            <span class="badge ${a.status === 'Active' ? 'badge-success' : 'badge-danger'}">${a.status}</span>
          </td>
          <td>
            <span style="font-size: 0.75rem; color: var(--text-muted);">${a.created_at ? a.created_at.substring(0, 10) : ''}</span>
          </td>
          <td>
            ${a.status === 'Active' ? `
              <button class="btn btn-quiet" style="font-size: 0.72rem; padding: 3px 8px; color: var(--status-danger);" onclick="app.adminRevokeAssignment(${a.id})">
                Revoke
              </button>
            ` : '<span style="color: var(--text-muted); font-size: 0.75rem;">Inactive</span>'}
          </td>
        </tr>
      `).join("");
    } catch (e) {
      console.error(e);
      this.showToast("Failed to load assignments", "error");
    }
  }

  async openAssignModal() {
    this.closeModals();
    const modal = document.getElementById("adminAssignModal");
    if (!modal) return;

    try {
      const [tRes, sRes] = await Promise.all([
        this.apiRequest("/api/admin/teachers"),
        this.apiRequest("/api/admin/students")
      ]);

      const tSelect = document.getElementById("mAssignTeacherSelect");
      const sSelect = document.getElementById("mAssignStudentSelect");

      if (tSelect) {
        tSelect.innerHTML = `<option value="">-- Choose Faculty Guide --</option>` +
          (tRes.teachers || []).filter(t => t.is_active).map(t =>
            `<option value="${t.id}">${t.full_name} (${t.department} - ${t.designation})</option>`
          ).join("");
      }

      if (sSelect) {
        sSelect.innerHTML = `<option value="">-- Choose Student --</option>` +
          (sRes.students || []).filter(s => s.is_active).map(s =>
            `<option value="${s.id}">${s.full_name} (${s.enrollment_no} - ${s.department})</option>`
          ).join("");
      }

      modal.classList.add("active");
    } catch (e) {
      this.showToast("Failed to populate assignment options", "error");
    }
  }

  async onAssignStudentChanged(studentId) {
    const pSelect = document.getElementById("mAssignProjectSelect");
    if (!pSelect) return;
    pSelect.innerHTML = `<option value="">-- General / All Projects --</option>`;
    if (!studentId) return;

    try {
      const res = await this.apiRequest(`/api/admin/projects`);
      if (res.success && res.projects) {
        const studentProjects = res.projects.filter(p => String(p.student_id) === String(studentId));
        studentProjects.forEach(p => {
          pSelect.innerHTML += `<option value="${p.id}">${p.id} - ${p.title} (${p.status})</option>`;
        });
      }
    } catch (e) {}
  }

  async handleAdminSaveAssignment() {
    const teacherId = document.getElementById("mAssignTeacherSelect").value;
    const studentId = document.getElementById("mAssignStudentSelect").value;
    const projectId = document.getElementById("mAssignProjectSelect").value || null;
    const deadline = document.getElementById("mAssignDeadline").value || null;
    const notes = document.getElementById("mAssignNotes").value.trim();

    if (!teacherId || !studentId) {
      this.showToast("Teacher and Student selections are required", "error");
      return;
    }

    try {
      const res = await this.apiRequest("/api/admin/assignments", "POST", {
        teacher_id: parseInt(teacherId, 10),
        student_id: parseInt(studentId, 10),
        project_id: projectId,
        deadline,
        notes
      });
      if (res.success) {
        this.showToast("Guide assignment confirmed");
        this.closeModals();
        this.loadAdminAssignments();
      }
    } catch (err) {
      this.showToast(err.message, "error");
    }
  }

  async adminRevokeAssignment(assignId) {
    try {
      const res = await this.apiRequest(`/api/admin/assignments/${assignId}/revoke`, "POST");
      if (res.success) {
        this.showToast("Assignment revoked");
        this.loadAdminAssignments();
      }
    } catch (err) {
      this.showToast(err.message, "error");
    }
  }

  // ==========================================================================
  // ADMIN PASSWORD RESET
  // ==========================================================================
  adminOpenResetPassword(userId, userName, role) {
    this.closeModals();
    const modal = document.getElementById("adminResetPasswordModal");
    if (!modal) return;
    document.getElementById("mResetUserId").value = userId;
    document.getElementById("mResetUserType").value = role;
    document.getElementById("mResetUserLabel").innerText = `Set a new temporary password for ${userName} (${role}).`;
    document.getElementById("mResetNewPassword").value = role === 'teacher' ? 'Teacher@2026!' : 'Student@2026!';
    modal.classList.add("active");
  }

  async handleAdminSubmitResetPassword() {
    const userId = document.getElementById("mResetUserId").value;
    const userType = document.getElementById("mResetUserType").value;
    const newPassword = document.getElementById("mResetNewPassword").value;

    const endpoint = userType === 'teacher' ?
      `/api/admin/teachers/${userId}/reset-password` :
      `/api/admin/students/${userId}/reset-password`;

    try {
      const res = await this.apiRequest(endpoint, "POST", { new_password: newPassword });
      if (res.success) {
        this.showToast("Password reset successfully. Active sessions invalidated.");
        this.closeModals();
      }
    } catch (err) {
      this.showToast(err.message, "error");
    }
  }

  // ==========================================================================
  // TEACHER AUTH & PORTAL METHODS
  // ==========================================================================
  openTeacherAuthModal() {
    this.closeModals();
    const modal = document.getElementById("teacherAuthModal");
    if (modal) modal.classList.add("active");
  }

  fillDemoTeacherCreds() {
    const e = document.getElementById("tLoginEmail");
    const p = document.getElementById("tLoginPassword");
    if (e) e.value = "teacher@univ.edu";
    if (p) p.value = "Teacher@2026!";
  }

  async handleTeacherLogin() {
    const email = document.getElementById("tLoginEmail").value.trim();
    const password = document.getElementById("tLoginPassword").value;
    try {
      const res = await this.apiRequest("/api/auth/login", "POST", {
        email,
        password,
        portal_type: "teacher"
      });
      if (res.success) {
        this.token = res.token;
        this.currentUser = res.user;
        localStorage.setItem("apts_token", this.token);
        this.closeModals();
        this.showToast(`Authenticated as ${res.user.teacher_name || res.user.email}`);
        window.location.hash = "/teacher/dashboard";
        this.showTeacherPortal();
      }
    } catch (err) {
      this.showToast(err.message, "error");
    }
  }

  switchTeacherTab(tabId) {
    this.currentTeacherTab = tabId;
    document.querySelectorAll(".sidebar-nav-item").forEach(item => {
      if (item.dataset.ttab === tabId) item.classList.add("active");
      else if (item.dataset.ttab) item.classList.remove("active");
    });

    document.querySelectorAll("#teacherMainContent .admin-page-panel").forEach(p => {
      p.style.display = p.id === tabId ? "block" : "none";
    });

    const titles = {
      tTabDashboard: "Faculty Mentor &bull; Cohort Supervision Overview",
      tTabStudents: "My Supervised Student Roster",
      tTabProjects: "Assigned Student Capstone Projects",
      tTabPending: "Priority Verification Queue &bull; Student Submissions",
      tTabReview: "Capstones Under Active Review",
      tTabEvaluation: "Standardized 100-Mark Rubric Evaluator",
      tTabNotifs: "Faculty Activity &amp; Submissions Feed",
      tTabProfile: "Faculty Profile &amp; Credentials"
    };
    const crumb = document.getElementById("teacherCrumbCurrent");
    if (crumb) crumb.innerHTML = titles[tabId] || "Faculty Guide Workspace";

    if (tabId === "tTabDashboard") this.loadTeacherDashboard();
    if (tabId === "tTabStudents") this.loadTeacherStudents();
    if (tabId === "tTabProjects") this.loadTeacherProjects();
    if (tabId === "tTabPending") this.loadTeacherPendingReviews();
    if (tabId === "tTabReview") this.loadTeacherUnderReview();
    if (tabId === "tTabEvaluation") this.loadTeacherEvaluationView();
    if (tabId === "tTabNotifs") this.loadTeacherNotifications();
    if (tabId === "tTabProfile") this.loadTeacherProfile();
  }

  async loadTeacherDashboard() {
    try {
      const data = await this.apiRequest("/api/teacher/dashboard");
      if (!data.success) return;

      const m = data.metrics;
      const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
      setVal("tKpiStudents", m.assigned_students);
      setVal("tKpiTotalProjects", m.total_projects);
      setVal("tKpiPending", m.pending_reviews);
      setVal("tKpiUnderReview", m.under_review);
      setVal("tKpiApproved", m.approved);
      setVal("tKpiGraded", m.graded);

      const badge = document.getElementById("teacherPendingBadge");
      if (badge) badge.innerText = m.pending_reviews;

      const tbody = document.getElementById("teacherDashboardQueueTable");
      if (tbody) {
        if (!data.recent_projects || data.recent_projects.length === 0) {
          tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">No pending submissions in your queue. All caught up!</td></tr>`;
        } else {
          tbody.innerHTML = data.recent_projects.map(p => `
            <tr>
              <td><span style="font-family: monospace; color: var(--brand-blue);">${p.id}</span></td>
              <td><strong>${p.title}</strong></td>
              <td>${p.student_name} (${p.enrollment_no})</td>
              <td>${this.renderStatusPill(p.status)}</td>
              <td>
                <div style="display: flex; gap: 0.35rem;">
                  <button class="btn btn-quiet" style="font-size: 0.72rem; padding: 3px 8px;" onclick="app.teacherStartReview('${p.id}')">
                    Review
                  </button>
                  <button class="btn btn-purple" style="font-size: 0.72rem; padding: 3px 8px;" onclick="app.loadTeacherEvaluationView('${p.id}')">
                    Evaluate
                  </button>
                </div>
              </td>
            </tr>
          `).join("");
        }
      }
    } catch (e) {
      console.error(e);
    }
  }

  async loadTeacherStudents() {
    try {
      const data = await this.apiRequest("/api/teacher/students");
      const tbody = document.getElementById("teacherStudentsTable");
      if (!tbody) return;

      if (!data.students || data.students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">No students assigned to you yet by the department administrator.</td></tr>`;
        return;
      }

      tbody.innerHTML = data.students.map(s => `
        <tr>
          <td>
            <strong>${s.full_name}</strong><br>
            <span style="font-size: 0.75rem; color: var(--brand-blue);">${s.enrollment_no}</span>
          </td>
          <td>${s.email}</td>
          <td>${s.department} (${s.branch}) · Sem ${s.semester}</td>
          <td><span class="badge-counter">${s.total_projects || 0}</span></td>
          <td>${s.deadline ? `<span style="color: var(--status-warning); font-weight:600;">📅 ${s.deadline}</span>` : '<span style="color:var(--text-muted);">Open</span>'}</td>
          <td><span style="font-size: 0.8rem; color: var(--text-muted);">${s.assignment_notes || 'Major Capstone Guidance'}</span></td>
        </tr>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  async loadTeacherProjects(status = "all") {
    try {
      const data = await this.apiRequest(`/api/teacher/projects?status=${encodeURIComponent(status)}`);
      const tbody = document.getElementById("teacherProjectsTable");
      if (!tbody) return;

      if (!data.projects || data.projects.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">No projects matching the selected status.</td></tr>`;
        return;
      }

      tbody.innerHTML = data.projects.map(p => `
        <tr>
          <td><span style="font-family: monospace; color: var(--brand-blue);">${p.id}</span></td>
          <td><strong>${p.title}</strong></td>
          <td>${p.student_name} (${p.enrollment_no})</td>
          <td>${this.renderStatusPill(p.status)}</td>
          <td>${p.total_score !== null && p.total_score !== undefined ? `<strong style="color: var(--brand-blue);">${p.total_score}/100 (${p.eval_grade})</strong>` : '<span style="color:var(--text-muted);">Not Graded</span>'}</td>
          <td>
            <div style="display: flex; gap: 0.35rem; flex-wrap: wrap;">
              <button class="btn btn-quiet" style="font-size: 0.72rem; padding: 3px 8px;" onclick="app.teacherStartReview('${p.id}')">
                🔍 Review
              </button>
              <button class="btn btn-quiet" style="font-size: 0.72rem; padding: 3px 8px; color: var(--status-warning);" onclick="app.teacherPromptChanges('${p.id}')">
                ✏️ Changes
              </button>
              <button class="btn btn-quiet" style="font-size: 0.72rem; padding: 3px 8px; color: var(--status-success);" onclick="app.teacherApprove('${p.id}')">
                ✓ Approve
              </button>
              <button class="btn btn-purple" style="font-size: 0.72rem; padding: 3px 8px;" onclick="app.loadTeacherEvaluationView('${p.id}')">
                ★ Grade
              </button>
            </div>
          </td>
        </tr>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  filterTeacherProjects(status) {
    this.loadTeacherProjects(status);
  }

  async loadTeacherPendingReviews() {
    try {
      const data = await this.apiRequest("/api/teacher/projects?status=pending");
      const tbody = document.getElementById("teacherPendingReviewsTable");
      if (!tbody) return;

      if (!data.projects || data.projects.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">No pending submissions in queue.</td></tr>`;
        return;
      }

      tbody.innerHTML = data.projects.map(p => `
        <tr>
          <td><span style="font-family: monospace; color: var(--brand-blue);">${p.id}</span></td>
          <td><strong>${p.title}</strong></td>
          <td>${p.student_name} (${p.enrollment_no})</td>
          <td>${this.renderStatusPill(p.status)}</td>
          <td>
            <div style="display: flex; gap: 0.35rem;">
              <button class="btn btn-quiet" style="font-size: 0.72rem; padding: 3px 8px;" onclick="app.teacherStartReview('${p.id}')">
                Start Review
              </button>
              <button class="btn btn-quiet" style="font-size: 0.72rem; padding: 3px 8px; color: var(--status-warning);" onclick="app.teacherPromptChanges('${p.id}')">
                Request Changes
              </button>
            </div>
          </td>
        </tr>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  async loadTeacherUnderReview() {
    try {
      const data = await this.apiRequest("/api/teacher/projects?status=Under Review");
      const tbody = document.getElementById("teacherUnderReviewTable");
      if (!tbody) return;

      if (!data.projects || data.projects.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 2rem;">No capstones currently under review.</td></tr>`;
        return;
      }

      tbody.innerHTML = data.projects.map(p => `
        <tr>
          <td><span style="font-family: monospace; color: var(--brand-blue);">${p.id}</span></td>
          <td><strong>${p.title}</strong></td>
          <td>${p.student_name} (${p.enrollment_no})</td>
          <td>
            <div style="display: flex; gap: 0.35rem;">
              <button class="btn btn-purple" style="font-size: 0.72rem; padding: 3px 8px;" onclick="app.loadTeacherEvaluationView('${p.id}')">
                ★ Rubric Evaluation
              </button>
              <button class="btn btn-quiet" style="font-size: 0.72rem; padding: 3px 8px; color: var(--status-success);" onclick="app.teacherApprove('${p.id}')">
                Approve
              </button>
            </div>
          </td>
        </tr>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  async loadTeacherEvaluationView(projectId = null) {
    const container = document.getElementById("teacherEvaluationContainer");
    if (!container) return;

    if (!projectId) {
      // Pick first assigned project or show dropdown
      try {
        const res = await this.apiRequest("/api/teacher/projects");
        if (res.projects && res.projects.length > 0) {
          projectId = res.projects[0].id;
        } else {
          container.innerHTML = `<p style="color: var(--text-muted);">No assigned projects to evaluate.</p>`;
          return;
        }
      } catch (e) {
        return;
      }
    }

    try {
      const data = await this.apiRequest(`/api/teacher/projects/${projectId}`);
      if (!data.success) return;

      const p = data.project;
      const ev = data.evaluation || {};

      container.innerHTML = `
        <div style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-app);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
            <div>
              <span style="font-family: monospace; color: var(--brand-blue); font-size: 0.85rem;">${p.id}</span>
              <h3 style="margin: 0.25rem 0;">${p.title}</h3>
              <p style="color: var(--text-muted); font-size: 0.85rem;">Candidate: <strong>${p.student_name}</strong> (${p.enrollment_no}) · ${p.department}</p>
            </div>
            <div>
              ${this.renderStatusPill(p.status)}
            </div>
          </div>
        </div>

        <form onsubmit="event.preventDefault(); app.saveTeacherRubricEvaluation('${p.id}');">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
            <div>
              <label class="form-label">1. Problem Statement (max 15)</label>
              <input type="number" id="tScore1" class="form-control" value="${ev.problem_statement_score || 12}" min="0" max="15" step="0.5" oninput="app.calculateTeacherRubricTotal()" />
            </div>
            <div>
              <label class="form-label">2. Architecture &amp; Impl (max 25)</label>
              <input type="number" id="tScore2" class="form-control" value="${ev.implementation_score || 20}" min="0" max="25" step="0.5" oninput="app.calculateTeacherRubricTotal()" />
            </div>
            <div>
              <label class="form-label">3. Innovation (max 15)</label>
              <input type="number" id="tScore3" class="form-control" value="${ev.innovation_score || 12}" min="0" max="15" step="0.5" oninput="app.calculateTeacherRubricTotal()" />
            </div>
            <div>
              <label class="form-label">4. Documentation (max 15)</label>
              <input type="number" id="tScore4" class="form-control" value="${ev.documentation_score || 12}" min="0" max="15" step="0.5" oninput="app.calculateTeacherRubricTotal()" />
            </div>
            <div>
              <label class="form-label">5. UI/UX Design (max 10)</label>
              <input type="number" id="tScore5" class="form-control" value="${ev.ui_ux_score || 8}" min="0" max="10" step="0.5" oninput="app.calculateTeacherRubricTotal()" />
            </div>
            <div>
              <label class="form-label">6. Presentation (max 10)</label>
              <input type="number" id="tScore6" class="form-control" value="${ev.presentation_score || 8}" min="0" max="10" step="0.5" oninput="app.calculateTeacherRubricTotal()" />
            </div>
            <div>
              <label class="form-label">7. Completeness (max 10)</label>
              <input type="number" id="tScore7" class="form-control" value="${ev.completeness_score || 8}" min="0" max="10" step="0.5" oninput="app.calculateTeacherRubricTotal()" />
            </div>
          </div>

          <div style="background: var(--bg-card); border: 1px solid var(--border-app); border-radius: var(--radius-md); padding: 1rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center;">
            <div>
              <span style="font-size: 0.85rem; color: var(--text-muted);">Calculated Aggregate Score:</span>
              <div style="font-size: 1.5rem; font-weight: 800; color: #10B981;" id="tRubricTotalDisplay">80.0 / 100</div>
            </div>
            <div>
              <span style="font-size: 0.85rem; color: var(--text-muted);">Assigned Grade:</span>
              <div style="font-size: 1.5rem; font-weight: 800; color: var(--brand-purple);" id="tRubricGradeDisplay">Grade A</div>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Faculty Supervisor Overall Evaluation &amp; Feedback *</label>
            <textarea id="tEvalFeedback" class="form-control" rows="3" required placeholder="Comprehensive evaluation notes for student capstone defense...">${ev.overall_feedback || ''}</textarea>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Key Strengths</label>
              <input type="text" id="tEvalStrengths" class="form-control" value="${ev.strengths || ''}" placeholder="e.g. Robust hardware testbench, clean modularity" />
            </div>
            <div class="form-group">
              <label class="form-label">Recommended Improvements</label>
              <input type="text" id="tEvalImprovements" class="form-control" value="${ev.recommended_improvements || ''}" placeholder="e.g. Optimize corner cases in branch prediction" />
            </div>
          </div>

          <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1rem;">
            <button type="submit" class="btn btn-quiet" onclick="app._teacherEvalPublish = false;">
              💾 Save Draft Evaluation
            </button>
            <button type="submit" class="btn btn-purple" onclick="app._teacherEvalPublish = true;">
              ★ Publish Official Grade
            </button>
          </div>
        </form>
      `;

      this.calculateTeacherRubricTotal();
    } catch (e) {
      console.error(e);
    }
  }

  calculateTeacherRubricTotal() {
    const s1 = parseFloat(document.getElementById("tScore1")?.value || 0);
    const s2 = parseFloat(document.getElementById("tScore2")?.value || 0);
    const s3 = parseFloat(document.getElementById("tScore3")?.value || 0);
    const s4 = parseFloat(document.getElementById("tScore4")?.value || 0);
    const s5 = parseFloat(document.getElementById("tScore5")?.value || 0);
    const s6 = parseFloat(document.getElementById("tScore6")?.value || 0);
    const s7 = parseFloat(document.getElementById("tScore7")?.value || 0);

    const total = Math.round((s1 + s2 + s3 + s4 + s5 + s6 + s7) * 10) / 10;
    let grade = "Needs Improvement";
    if (total >= 90) grade = "A+";
    else if (total >= 80) grade = "A";
    else if (total >= 70) grade = "B+";
    else if (total >= 60) grade = "B";
    else if (total >= 50) grade = "C";

    const tDisp = document.getElementById("tRubricTotalDisplay");
    const gDisp = document.getElementById("tRubricGradeDisplay");
    if (tDisp) tDisp.innerText = `${total.toFixed(1)} / 100`;
    if (gDisp) gDisp.innerText = `Grade ${grade}`;
  }

  async saveTeacherRubricEvaluation(projectId) {
    const isPublished = !!this._teacherEvalPublish;
    const payload = {
      problem_statement_score: parseFloat(document.getElementById("tScore1").value),
      implementation_score: parseFloat(document.getElementById("tScore2").value),
      innovation_score: parseFloat(document.getElementById("tScore3").value),
      documentation_score: parseFloat(document.getElementById("tScore4").value),
      ui_ux_score: parseFloat(document.getElementById("tScore5").value),
      presentation_score: parseFloat(document.getElementById("tScore6").value),
      completeness_score: parseFloat(document.getElementById("tScore7").value),
      overall_feedback: document.getElementById("tEvalFeedback").value.trim(),
      strengths: document.getElementById("tEvalStrengths").value.trim(),
      recommended_improvements: document.getElementById("tEvalImprovements").value.trim(),
      is_published: isPublished
    };

    try {
      const res = await this.apiRequest(`/api/teacher/projects/${projectId}/evaluate`, "POST", payload);
      if (res.success) {
        this.showToast(isPublished ? `Grade ${res.grade} published successfully!` : "Evaluation draft saved");
        this.switchTeacherTab("tTabProjects");
      }
    } catch (err) {
      this.showToast(err.message, "error");
    }
  }

  async teacherStartReview(projectId) {
    try {
      const res = await this.apiRequest(`/api/teacher/projects/${projectId}/status`, "POST", {
        status: "Under Review",
        notes: "Faculty Guide commenced milestone review and verification."
      });
      if (res.success) {
        this.showToast("Project moved to Under Review");
        this.loadTeacherDashboard();
        if (this.currentTeacherTab === "tTabProjects") this.loadTeacherProjects();
        if (this.currentTeacherTab === "tTabPending") this.loadTeacherPendingReviews();
      }
    } catch (err) {
      this.showToast(err.message, "error");
    }
  }

  async teacherApprove(projectId) {
    try {
      const res = await this.apiRequest(`/api/teacher/projects/${projectId}/status`, "POST", {
        status: "Approved",
        notes: "Approved by Faculty Guide. Deliverables meet capstone criteria."
      });
      if (res.success) {
        this.showToast("Project approved!");
        this.loadTeacherDashboard();
        if (this.currentTeacherTab === "tTabProjects") this.loadTeacherProjects();
      }
    } catch (err) {
      this.showToast(err.message, "error");
    }
  }

  teacherPromptChanges(projectId) {
    this.closeModals();
    this._teacherPromptProjectId = projectId;
    this._teacherPromptStatus = "Changes Requested";

    const modal = document.getElementById("teacherActionPromptModal");
    const title = document.getElementById("teacherActionPromptTitle");
    const sub = document.getElementById("teacherActionPromptSubtitle");
    const label = document.getElementById("teacherActionPromptLabel");
    const notes = document.getElementById("teacherActionPromptNotes");

    if (title) title.innerText = "Request Technical Revisions";
    if (sub) sub.innerText = `Provide specific directives for project ${projectId}. Student will be notified and allowed to resubmit.`;
    if (label) label.innerText = "Required Changes / Guidance *";
    if (notes) notes.value = "";

    if (modal) modal.classList.add("active");
  }

  teacherPromptReject(projectId) {
    this.closeModals();
    this._teacherPromptProjectId = projectId;
    this._teacherPromptStatus = "Rejected";

    const modal = document.getElementById("teacherActionPromptModal");
    const title = document.getElementById("teacherActionPromptTitle");
    const sub = document.getElementById("teacherActionPromptSubtitle");
    const label = document.getElementById("teacherActionPromptLabel");
    const notes = document.getElementById("teacherActionPromptNotes");

    if (title) title.innerText = "Reject Capstone Submission";
    if (sub) sub.innerText = `Specify grounds for rejection for project ${projectId}.`;
    if (label) label.innerText = "Rejection Grounds / Reason *";
    if (notes) notes.value = "";

    if (modal) modal.classList.add("active");
  }

  async submitTeacherActionPrompt() {
    const projectId = this._teacherPromptProjectId;
    const status = this._teacherPromptStatus;
    const notes = (document.getElementById("teacherActionPromptNotes")?.value || "").trim();

    if (!notes) {
      this.showToast("Written feedback directive is required", "error");
      return;
    }

    try {
      const res = await this.apiRequest(`/api/teacher/projects/${projectId}/status`, "POST", {
        status,
        notes
      });
      if (res.success) {
        this.showToast(`Status updated to ${status}`);
        this.closeModals();
        this.loadTeacherDashboard();
        if (this.currentTeacherTab === "tTabProjects") this.loadTeacherProjects();
        if (this.currentTeacherTab === "tTabPending") this.loadTeacherPendingReviews();
      }
    } catch (err) {
      this.showToast(err.message, "error");
    }
  }

  async loadTeacherNotifications() {
    try {
      const data = await this.apiRequest("/api/teacher/notifications");
      const list = document.getElementById("teacherNotifsList");
      if (!list) return;

      if (!data.notifications || data.notifications.length === 0) {
        list.innerHTML = `<p style="color: var(--text-muted); padding: 1.5rem; text-align: center;">No activity notifications.</p>`;
        return;
      }

      list.innerHTML = data.notifications.map(n => `
        <div style="padding: 0.85rem; border-bottom: 1px solid var(--border-app); display: flex; justify-content: space-between; align-items: flex-start;">
          <div>
            <strong>${n.title}</strong>
            <p style="margin: 0.25rem 0 0; font-size: 0.85rem; color: var(--text-muted);">${n.message}</p>
          </div>
          <span style="font-size: 0.7rem; color: var(--text-muted);">${n.created_at ? n.created_at.substring(0, 16).replace("T", " ") : ''}</span>
        </div>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  async loadTeacherProfile() {
    try {
      const data = await this.apiRequest("/api/teacher/profile");
      const card = document.getElementById("teacherProfileCard");
      if (!card || !data.profile) return;

      const p = data.profile;
      card.innerHTML = `
        <div style="display: flex; gap: 1.5rem; align-items: center; margin-bottom: 2rem;">
          <div style="font-size: 3rem; background: rgba(16, 185, 129, 0.15); border-radius: var(--radius-full); width: 80px; height: 80px; display: flex; align-items: center; justify-content: center;">
            👨‍🏫
          </div>
          <div>
            <h2 style="margin: 0;">${p.full_name}</h2>
            <p style="color: #10B981; font-weight: 600; margin: 0.25rem 0;">${p.designation} · ${p.faculty_id}</p>
            <p style="color: var(--text-muted); font-size: 0.85rem; margin: 0;">${p.department}</p>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem;">
          <div class="form-group">
            <label class="form-label">Official Email</label>
            <input type="text" class="form-control" value="${p.email}" readonly />
          </div>
          <div class="form-group">
            <label class="form-label">Phone Contact</label>
            <input type="text" class="form-control" value="${p.phone || 'Not configured'}" readonly />
          </div>
          <div class="form-group" style="grid-column: span 2;">
            <label class="form-label">Specialization / Research Domain</label>
            <input type="text" class="form-control" value="${p.specialization || 'Distributed Systems, Machine Learning'}" readonly />
          </div>
        </div>
      `;
    } catch (e) {
      console.error(e);
    }
  }


  async loadAdminProjects(status = "all", search = "") {
    try {
      let url = `/api/admin/projects?status=${encodeURIComponent(status)}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      const data = await this.apiRequest(url);
      const tbody = document.getElementById("adminAllProjectsTable");
      if (!tbody) return;

      this.adminProjectsList = data.projects || [];
      tbody.innerHTML = this.adminProjectsList.map(p => `
        <tr>
          <td><strong>${p.id}</strong></td>
          <td><div style="font-weight: 700;">${p.title}</div></td>
          <td>${p.student_name} (${p.enrollment_no})</td>
          <td>${p.category}</td>
          <td><span class="status-pill status-${p.status.toLowerCase().replace(/\s+/g, '-')}">${p.status}</span></td>
          <td><strong style="color: var(--brand-blue);">${p.is_published ? `${p.total_score} (${p.eval_grade})` : 'Pending'}</strong></td>
          <td>
            <button class="btn btn-purple" style="font-size: 0.75rem; padding: 3px 8px;" onclick="app.openAdminReviewModal('${p.id}')">Inspect</button>
            <button class="btn btn-quiet" style="font-size: 0.75rem; padding: 3px 8px; margin-left: 4px;" onclick="app.loadProjectIntoRubric('${p.id}'); app.switchAdminTab('aTabEvaluation');">Grade</button>
          </td>
        </tr>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  filterAdminProjects(val) {
    this.loadAdminProjects(val, document.getElementById("adminProjectSearch").value);
  }

  searchAdminProjects(val) {
    this.loadAdminProjects(document.getElementById("adminStatusFilter").value, val);
  }

  async loadAdminFilteredProjects(status, tableId) {
    try {
      const data = await this.apiRequest(`/api/admin/projects?status=${encodeURIComponent(status)}`);
      const tbody = document.getElementById(tableId);
      if (!tbody) return;

      const list = data.projects || [];
      if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 2rem; color: var(--text-muted);">No capstones with status '${status}'.</td></tr>`;
        return;
      }

      tbody.innerHTML = list.map(p => `
        <tr>
          <td><strong>${p.id}:</strong> ${p.title}</td>
          <td>${p.student_name} (${p.enrollment_no})</td>
          <td>${new Date(p.created_at).toLocaleDateString()}</td>
          <td><span class="status-pill status-${p.status.toLowerCase().replace(/\s+/g, '-')}">${p.status}</span></td>
          <td>
            <button class="btn btn-purple" style="font-size: 0.75rem; padding: 3px 8px;" onclick="app.openAdminReviewModal('${p.id}')">Inspect</button>
          </td>
        </tr>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  async openAdminReviewModal(projectId) {
    try {
      const data = await this.apiRequest(`/api/admin/projects/${projectId}`);
      if (!data.success) return;

      const p = data.project;
      const content = document.getElementById("adminReviewModalContent");
      document.getElementById("revModalTitle").innerText = `Capstone Verification: ${p.id}`;

      content.innerHTML = `
        <div style="background: var(--bg-surface); padding: 1.25rem; border-radius: var(--radius-md); border: 1px solid var(--border-app); margin-bottom: 1.25rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <div>
              <h3 style="font-size: 1.25rem; color: var(--text-primary);">${p.title}</h3>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">
                Candidate: <strong>${p.student_name}</strong> (${p.enrollment_no}) &bull; ${p.department} Sem ${p.semester} &bull; Revision: <strong>v${p.submission_version || 1}</strong>
              </div>
            </div>
            <span class="status-pill status-${p.status.toLowerCase().replace(/\s+/g, '-')}">${p.status}</span>
          </div>
        </div>

        ${p.versions && p.versions.length > 1 ? `
          <div style="background: rgba(0, 212, 255, 0.05); border: 1px solid rgba(0, 212, 255, 0.2); padding: 0.75rem 1rem; border-radius: var(--radius-md); margin-bottom: 1rem;">
            <div style="font-size: 0.8rem; font-weight: 700; color: var(--brand-blue); margin-bottom: 0.25rem;">Revision Provenance History (${p.versions.length} versions)</div>
            <div style="font-size: 0.775rem; color: var(--text-secondary); line-height: 1.5;">
              ${p.versions.map(v => `<span><strong>v${v.version_number}</strong>: ${v.changelog || 'Revision submitted'} (${new Date(v.submitted_at || v.created_at).toLocaleDateString()})</span>`).join("<br>")}
            </div>
          </div>
        ` : ''}

        <div class="form-group">
          <label class="form-label">Project Abstract</label>
          <div style="background: var(--bg-surface); padding: 0.85rem; border-radius: var(--radius-md); font-size: 0.85rem; line-height: 1.5; color: var(--text-secondary);">${p.abstract}</div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Problem Statement</label>
            <div style="background: var(--bg-surface); padding: 0.85rem; border-radius: var(--radius-md); font-size: 0.8rem; color: var(--text-secondary);">${p.problem_statement}</div>
          </div>
          <div class="form-group">
            <label class="form-label">Project Objectives</label>
            <div style="background: var(--bg-surface); padding: 0.85rem; border-radius: var(--radius-md); font-size: 0.8rem; color: var(--text-secondary);">${p.objectives}</div>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Technologies &amp; Simulators</label>
          <div style="font-size: 0.85rem; color: var(--brand-blue);">${p.technologies}</div>
        </div>

        <div style="display: flex; gap: 0.75rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
          ${p.repo_url ? `<a href="${p.repo_url}" target="_blank" class="btn btn-quiet" style="font-size: 0.8rem;">📦 View GitHub Code</a>` : ''}
          ${p.live_url ? `<a href="${p.live_url}" target="_blank" class="btn btn-quiet" style="font-size: 0.8rem;">🌐 Live Demonstration</a>` : ''}
          ${p.doc_file ? `<a href="${p.doc_file}" target="_blank" class="btn btn-quiet" style="font-size: 0.8rem;">📄 Spec Document (PDF)</a>` : '<button class="btn btn-quiet" style="font-size: 0.8rem;" onclick="app.showToast(\'No PDF uploaded\')">📄 No Spec Document</button>'}
          ${p.presentation_file ? `<a href="${p.presentation_file}" target="_blank" class="btn btn-quiet" style="font-size: 0.8rem;">📊 Presentation PPT</a>` : ''}
        </div>

        <div style="border-top: 1px solid var(--border-app); padding-top: 1.25rem;">
          <h4 style="margin-bottom: 0.75rem;">Faculty Governance Actions</h4>
          <div style="display: flex; gap: 0.6rem; flex-wrap: wrap;">
            <button class="btn btn-emerald" onclick="app.adminSetStatus('${p.id}', 'Under Review', 'Faculty technical review initiated')">🔍 Start Review (Under Review)</button>
            <button class="btn btn-primary" onclick="app.adminSetStatus('${p.id}', 'Approved', 'Capstone approved for Viva Voce examination')">✓ Accept &amp; Approve for Viva</button>
            <button class="btn btn-purple" onclick="app.adminPromptChanges('${p.id}')">↺ Request Changes / Improvements</button>
            <button class="btn btn-quiet" style="color: var(--accent-rose);" onclick="app.adminPromptReject('${p.id}')">✕ Reject Project</button>
            <button class="btn btn-purple" style="margin-left: auto;" onclick="app.closeModals(); app.loadProjectIntoRubric('${p.id}'); app.switchAdminTab('aTabEvaluation');">★ Grade 100-Mark Rubric</button>
          </div>
        </div>
      `;

      document.getElementById("adminReviewModal").classList.add("open");
    } catch (e) {
      console.error(e);
    }
  }

  async adminSetStatus(projectId, newStatus, notes = "") {
    try {
      const res = await this.apiRequest(`/api/admin/projects/${projectId}/status`, "POST", {
        status: newStatus,
        notes: notes || `Project moved to ${newStatus}`
      });
      if (res.success) {
        this.showToast(`Updated ${projectId} to '${newStatus}'`);
        this.closeModals();
        this.loadAdminDashboard();
        this.loadAdminProjects();
      }
    } catch (err) {
      this.showToast(err.message || "Status update failed");
    }
  }

  adminPromptChanges(projectId) {
    const pIdEl = document.getElementById("actionPromptProjectId");
    if (pIdEl) pIdEl.value = projectId;
    const stEl = document.getElementById("actionPromptStatus");
    if (stEl) stEl.value = "Changes Requested";
    const tEl = document.getElementById("actionPromptTitle");
    if (tEl) tEl.innerText = `Request Changes: ${projectId}`;
    const dEl = document.getElementById("actionPromptDesc");
    if (dEl) dEl.innerText = "Specify weaknesses, missing components, or testbench corrections the candidate must address before project approval.";
    const lEl = document.getElementById("actionPromptLabel");
    if (lEl) lEl.innerText = "Specific Revision Instructions & Deficiencies *";
    const nEl = document.getElementById("actionPromptNotes");
    if (nEl) {
      nEl.value = "";
      nEl.placeholder = "E.g. Corner cases in Booth recoding table must be verified with simulation waveforms. Fix RAW hazard forwarding stalls.";
    }
    document.getElementById("adminActionPromptModal").classList.add("open");
  }

  adminPromptReject(projectId) {
    const pIdEl = document.getElementById("actionPromptProjectId");
    if (pIdEl) pIdEl.value = projectId;
    const stEl = document.getElementById("actionPromptStatus");
    if (stEl) stEl.value = "Rejected";
    const tEl = document.getElementById("actionPromptTitle");
    if (tEl) tEl.innerText = `Reject Project Submission: ${projectId}`;
    const dEl = document.getElementById("actionPromptDesc");
    if (dEl) dEl.innerText = "State official faculty rejection rationale. This marks the project as rejected and notifies the student.";
    const lEl = document.getElementById("actionPromptLabel");
    if (lEl) lEl.innerText = "Official Rejection Rationale *";
    const nEl = document.getElementById("actionPromptNotes");
    if (nEl) {
      nEl.value = "";
      nEl.placeholder = "E.g. Project does not satisfy undergraduate senior thesis and engineering implementation requirements.";
    }
    document.getElementById("adminActionPromptModal").classList.add("open");
  }

  async submitAdminActionPrompt() {
    const projectId = document.getElementById("actionPromptProjectId").value;
    const status = document.getElementById("actionPromptStatus").value;
    const notes = document.getElementById("actionPromptNotes").value.trim();
    if (!notes) {
      this.showToast("Please enter written commentary for this action.");
      return;
    }
    await this.adminSetStatus(projectId, status, notes);
  }

  async loadAdminEvaluationView() {
    const sel = document.getElementById("evalSelectProject");
    if (!sel) return;

    const data = await this.apiRequest("/api/admin/projects");
    const projects = data.projects || [];
    sel.innerHTML = projects.map(p => `
      <option value="${p.id}">${p.id} - ${p.title} (${p.student_name})</option>
    `).join("");

    if (projects[0]) {
      this.loadProjectIntoRubric(projects[0].id);
    }
  }

  async loadProjectIntoRubric(projectId) {
    const sel = document.getElementById("evalSelectProject");
    if (sel) sel.value = projectId;

    try {
      const data = await this.apiRequest(`/api/admin/projects/${projectId}`);
      const evalData = data.evaluation;

      if (evalData) {
        document.getElementById("rubricProblem").value = evalData.problem_statement_score;
        document.getElementById("rubricImpl").value = evalData.implementation_score;
        document.getElementById("rubricInnov").value = evalData.innovation_score;
        document.getElementById("rubricDoc").value = evalData.documentation_score;
        document.getElementById("rubricUi").value = evalData.ui_ux_score;
        document.getElementById("rubricPres").value = evalData.presentation_score;
        document.getElementById("rubricComp").value = evalData.completeness_score;
        document.getElementById("evalFeedbackText").value = evalData.overall_feedback || "";
        document.getElementById("evalStrengths").value = evalData.strengths || "";
        document.getElementById("evalWeaknesses").value = evalData.weaknesses || "";
        const mf = document.getElementById("evalMissingFeatures");
        if (mf) mf.value = evalData.missing_features || "";
        const ti = document.getElementById("evalTechnicalIssues");
        if (ti) ti.value = evalData.technical_issues || "";
        const di = document.getElementById("evalDocIssues");
        if (di) di.value = evalData.documentation_issues || "";
        const ri = document.getElementById("evalImprovements");
        if (ri) ri.value = evalData.recommended_improvements || "";
      } else {
        document.getElementById("evalFeedbackText").value = "";
        document.getElementById("evalStrengths").value = "";
        document.getElementById("evalWeaknesses").value = "";
        const mf = document.getElementById("evalMissingFeatures");
        if (mf) mf.value = "";
        const ti = document.getElementById("evalTechnicalIssues");
        if (ti) ti.value = "";
        const di = document.getElementById("evalDocIssues");
        if (di) di.value = "";
        const ri = document.getElementById("evalImprovements");
        if (ri) ri.value = "";
      }
      this.calculateAdminRubric();
    } catch (e) {
      this.calculateAdminRubric();
    }
  }

  calculateAdminRubric() {
    const s1 = parseFloat(document.getElementById("rubricProblem").value) || 0;
    const s2 = parseFloat(document.getElementById("rubricImpl").value) || 0;
    const s3 = parseFloat(document.getElementById("rubricInnov").value) || 0;
    const s4 = parseFloat(document.getElementById("rubricDoc").value) || 0;
    const s5 = parseFloat(document.getElementById("rubricUi").value) || 0;
    const s6 = parseFloat(document.getElementById("rubricPres").value) || 0;
    const s7 = parseFloat(document.getElementById("rubricComp").value) || 0;

    document.getElementById("lblRubric1").innerText = `${s1} / 15`;
    document.getElementById("lblRubric2").innerText = `${s2} / 25`;
    document.getElementById("lblRubric3").innerText = `${s3} / 15`;
    document.getElementById("lblRubric4").innerText = `${s4} / 15`;
    document.getElementById("lblRubric5").innerText = `${s5} / 10`;
    document.getElementById("lblRubric6").innerText = `${s6} / 10`;
    document.getElementById("lblRubric7").innerText = `${s7} / 10`;

    const total = (s1 + s2 + s3 + s4 + s5 + s6 + s7).toFixed(1);
    document.getElementById("lblRubricTotalMarks").innerText = `${total} / 100`;

    let grade = "Needs Improvement";
    if (total >= 90) grade = "A+ (Outstanding)";
    else if (total >= 80) grade = "A (Excellent)";
    else if (total >= 70) grade = "B+ (Very Good)";
    else if (total >= 60) grade = "B (Good)";
    else if (total >= 50) grade = "C (Pass)";

    document.getElementById("lblRubricGradeLetter").innerText = `Grade ${grade}`;
  }

  async saveRubricEvaluation(publish = false) {
    const projectId = document.getElementById("evalSelectProject").value;
    const s1 = parseFloat(document.getElementById("rubricProblem").value) || 0;
    const s2 = parseFloat(document.getElementById("rubricImpl").value) || 0;
    const s3 = parseFloat(document.getElementById("rubricInnov").value) || 0;
    const s4 = parseFloat(document.getElementById("rubricDoc").value) || 0;
    const s5 = parseFloat(document.getElementById("rubricUi").value) || 0;
    const s6 = parseFloat(document.getElementById("rubricPres").value) || 0;
    const s7 = parseFloat(document.getElementById("rubricComp").value) || 0;
    const overall_feedback = document.getElementById("evalFeedbackText").value;
    const strengths = document.getElementById("evalStrengths").value;
    const weaknesses = document.getElementById("evalWeaknesses").value;
    const missing_features = document.getElementById("evalMissingFeatures") ? document.getElementById("evalMissingFeatures").value : "";
    const technical_issues = document.getElementById("evalTechnicalIssues") ? document.getElementById("evalTechnicalIssues").value : "";
    const documentation_issues = document.getElementById("evalDocIssues") ? document.getElementById("evalDocIssues").value : "";
    const recommended_improvements = document.getElementById("evalImprovements") ? document.getElementById("evalImprovements").value : "";

    try {
      const res = await this.apiRequest(`/api/admin/projects/${projectId}/evaluate`, "POST", {
        problem_statement_score: s1,
        implementation_score: s2,
        innovation_score: s3,
        documentation_score: s4,
        ui_ux_score: s5,
        presentation_score: s6,
        completeness_score: s7,
        overall_feedback,
        strengths,
        weaknesses,
        missing_features,
        technical_issues,
        documentation_issues,
        recommended_improvements,
        is_published: publish
      });

      if (res.success) {
        this.showToast(`Evaluation ${publish ? 'published' : 'saved'}! Final Score: ${res.total_score}/100 (${res.grade})`);
        this.loadAdminDashboard();
        this.loadAdminProjects();
      }
    } catch (err) {
      this.showToast(err.message || "Failed to save evaluation");
    }
  }

  async loadInstitutionSettings() {
    try {
      const res = await this.apiRequest("/api/institution/settings");
      if (!res.success || !res.settings) return;
      const s = res.settings;

      const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el && val !== undefined && val !== null) el.value = val;
      };

      setVal("cfgCollegeName", s.college_name);
      setVal("cfgDepartment", s.department);
      setVal("cfgProgram", s.degree_program);
      setVal("cfgAcademicYear", s.academic_year);
      setVal("cfgSemester", s.semester);
      setVal("cfgSession", s.project_session);
      setVal("cfgProjectTitle", s.capstone_title);
      setVal("cfgSupervisor", s.faculty_supervisor);
      setVal("cfgEvaluator", s.faculty_evaluator);
      setVal("cfgDeadline", s.submission_deadline);

      if (s.rubric_weights) {
        setVal("rubricMax1", s.rubric_weights.problem_statement);
        setVal("rubricMax2", s.rubric_weights.implementation);
        setVal("rubricMax3", s.rubric_weights.innovation);
        setVal("rubricMax4", s.rubric_weights.documentation);
        setVal("rubricMax5", s.rubric_weights.ui_ux);
        setVal("rubricMax6", s.rubric_weights.presentation);
        setVal("rubricMax7", s.rubric_weights.completeness);
      }
    } catch (err) {
      console.error("Failed to load institution settings:", err);
    }
  }

  async saveInstitutionSettings() {
    try {
      const payload = {
        college_name: document.getElementById("cfgCollegeName").value,
        department: document.getElementById("cfgDepartment").value,
        degree_program: document.getElementById("cfgProgram").value,
        academic_year: document.getElementById("cfgAcademicYear").value,
        semester: parseInt(document.getElementById("cfgSemester").value) || 6,
        project_session: document.getElementById("cfgSession").value,
        capstone_title: document.getElementById("cfgProjectTitle").value,
        faculty_supervisor: document.getElementById("cfgSupervisor").value,
        faculty_evaluator: document.getElementById("cfgEvaluator").value,
        submission_deadline: document.getElementById("cfgDeadline").value,
        rubric_weights: {
          problem_statement: parseInt(document.getElementById("rubricMax1").value) || 15,
          implementation: parseInt(document.getElementById("rubricMax2").value) || 25,
          innovation: parseInt(document.getElementById("rubricMax3").value) || 15,
          documentation: parseInt(document.getElementById("rubricMax4").value) || 15,
          ui_ux: parseInt(document.getElementById("rubricMax5").value) || 10,
          presentation: parseInt(document.getElementById("rubricMax6").value) || 10,
          completeness: parseInt(document.getElementById("rubricMax7").value) || 10
        }
      };

      const res = await this.apiRequest("/api/admin/institution/settings", "POST", payload);
      if (res.success) {
        this.showToast("Institution configuration saved successfully!");
      }
    } catch (err) {
      this.showToast(err.message || "Failed to save settings");
    }
  }

  async loadAdminAnalytics() {
    try {
      const deptEl = document.getElementById("analyticsFilterDept");
      const semEl = document.getElementById("analyticsFilterSem");
      const stEl = document.getElementById("analyticsFilterStatus");

      const dept = deptEl ? deptEl.value : "all";
      const sem = semEl ? semEl.value : "all";
      const st = stEl ? stEl.value : "all";

      let url = `/api/admin/analytics?department=${encodeURIComponent(dept)}&semester=${encodeURIComponent(sem)}&status=${encodeURIComponent(st)}`;
      const data = await this.apiRequest(url);
      if (!data.success) return;

      // 1. Monthly Project Submissions
      const mContainer = document.getElementById("analyticsMonthlyBars");
      if (mContainer) {
        const mList = data.monthly_submissions || [{ month: "2026-03", count: 8 }];
        const maxM = Math.max(...mList.map(m => m.count), 1);
        mContainer.innerHTML = mList.map(m => `
          <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px;">
            <div style="font-size: 0.75rem; font-weight: 700; color: var(--brand-blue);">${m.count}</div>
            <div style="width: 100%; max-width: 45px; height: ${Math.max(20, (m.count / maxM) * 90)}px; background: linear-gradient(180deg, var(--brand-blue), rgba(0, 212, 255, 0.3)); border-radius: 4px 4px 0 0;"></div>
            <div style="font-size: 0.7rem; color: var(--text-muted);">${m.month}</div>
          </div>
        `).join("");
      }

      // 2. Status Distribution
      const sContainer = document.getElementById("analyticsStatusBars");
      if (sContainer) {
        const statuses = data.status_distribution || {};
        const total = Object.values(statuses).reduce((a, b) => a + b, 0) || 1;
        sContainer.innerHTML = Object.entries(statuses).map(([st, cnt]) => `
          <div>
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.25rem;">
              <span>${st}</span><strong>${cnt} (${Math.round((cnt / total) * 100)}%)</strong>
            </div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${(cnt / total) * 100}%;"></div></div>
          </div>
        `).join("");
      }

      // 3. Department-wise Projects
      const dContainer = document.getElementById("analyticsDeptBars");
      if (dContainer) {
        const depts = data.department_distribution || {};
        const totalD = Object.values(depts).reduce((a, b) => a + b, 0) || 1;
        dContainer.innerHTML = Object.entries(depts).map(([dName, cnt]) => `
          <div>
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.25rem;">
              <span>${dName}</span><strong>${cnt}</strong>
            </div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${(cnt / totalD) * 100}%; background: var(--accent-emerald);"></div></div>
          </div>
        `).join("");
      }

      // 4. Grade Distribution
      const gContainer = document.getElementById("analyticsGradeBars");
      if (gContainer) {
        const grades = data.grade_distribution || {};
        const totalG = Object.values(grades).reduce((a, b) => a + b, 0) || 1;
        gContainer.innerHTML = Object.entries(grades).map(([gr, cnt]) => `
          <div>
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.25rem;">
              <span>Grade ${gr}</span><strong>${cnt}</strong>
            </div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${(cnt / totalG) * 100}%; background: var(--brand-blue);"></div></div>
          </div>
        `).join("");
      }

      // 5. Criteria Score Averages
      const cContainer = document.getElementById("analyticsCriteriaBars");
      if (cContainer) {
        const c = data.average_criteria_scores || {};
        const list = [
          { name: "Problem Statement (Max 15)", val: c.avg_problem || 0, max: 15 },
          { name: "Implementation (Max 25)", val: c.avg_impl || 0, max: 25 },
          { name: "Innovation (Max 15)", val: c.avg_innov || 0, max: 15 },
          { name: "Documentation (Max 15)", val: c.avg_doc || 0, max: 15 },
          { name: "UI/UX Design (Max 10)", val: c.avg_ui || 0, max: 10 },
          { name: "Presentation (Max 10)", val: c.avg_pres || 0, max: 10 },
          { name: "Completeness (Max 10)", val: c.avg_comp || 0, max: 10 }
        ];

        cContainer.innerHTML = list.map(item => `
          <div>
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.25rem;">
              <span>${item.name}</span><strong>${(item.val || 0).toFixed(1)} / ${item.max}</strong>
            </div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${((item.val || 0) / item.max) * 100}%;"></div></div>
          </div>
        `).join("");
      }

      // 6. Approved vs Rejected Comparison
      const arContainer = document.getElementById("analyticsApprovedRejectedBars");
      if (arContainer) {
        const ar = data.approved_vs_rejected || { approved_count: 0, rejected_count: 0 };
        const totalAR = (ar.approved_count || 0) + (ar.rejected_count || 0) || 1;
        arContainer.innerHTML = `
          <div>
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.25rem;">
              <span style="color: var(--accent-emerald);">Approved Capstones</span>
              <strong>${ar.approved_count || 0} (${Math.round(((ar.approved_count || 0) / totalAR) * 100)}%)</strong>
            </div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${((ar.approved_count || 0) / totalAR) * 100}%; background: var(--accent-emerald);"></div></div>
          </div>
          <div style="margin-top: 0.5rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.25rem;">
              <span style="color: #EF4444;">Rejected Submissions</span>
              <strong>${ar.rejected_count || 0} (${Math.round(((ar.rejected_count || 0) / totalAR) * 100)}%)</strong>
            </div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${((ar.rejected_count || 0) / totalAR) * 100}%; background: #EF4444;"></div></div>
          </div>
        `;
      }
    } catch (e) {
      console.error(e);
    }
  }

  resetAnalyticsFilters() {
    if (document.getElementById("analyticsFilterDept")) document.getElementById("analyticsFilterDept").value = "all";
    if (document.getElementById("analyticsFilterSem")) document.getElementById("analyticsFilterSem").value = "all";
    if (document.getElementById("analyticsFilterStatus")) document.getElementById("analyticsFilterStatus").value = "all";
    this.loadAdminAnalytics();
  }

  async exportCsvReport() {
    try {
      this.showToast("Generating official accreditation CSV report...");
      const res = await fetch("/api/admin/export", {
        headers: { "Authorization": `Bearer ${this.token}` }
      });
      if (!res.ok) {
        throw new Error("CSV Export failed. Unauthorized or server error.");
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `apts_capstone_export_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      this.showToast("CSV dataset downloaded successfully.");
    } catch (e) {
      this.showToast(e.message || "Export error");
    }
  }

  openDossierModal() {
    document.getElementById("dossierModal").classList.add("open");
  }

  // ==========================================================================
  // ARCHITECTURE LAB DEMOS
  // ==========================================================================
  runBoothDemo() {
    const box = document.getElementById("labOutputBox");
    if (!box) return;
    box.innerText = `>>> Running Signed Booth's Algorithm Verification (Unit 2):\n` +
      `Multiplicand M = 7 (0111), Multiplier Q = 3 (0011)\n` +
      `Step 1: Q0, Q-1 = 1,0 -> A = A - M -> ARS -> A = 1100, Q = 1001, Q-1 = 1\n` +
      `Step 2: Q0, Q-1 = 1,1 -> Pass -> ARS -> A = 1110, Q = 0100, Q-1 = 1\n` +
      `Step 3: Q0, Q-1 = 0,1 -> A = A + M -> ARS -> A = 0010, Q = 1010, Q-1 = 0\n` +
      `Step 4: Q0, Q-1 = 0,0 -> Pass -> ARS -> A = 0001, Q = 0101, Q-1 = 0\n` +
      `Verified Result: 21 (0001 0101) - 100% testbench pass against IEEE 754.`;
    this.showToast("Booth multiplier testbench passed");
  }

  runPipelineDemo() {
    const box = document.getElementById("labOutputBox");
    if (!box) return;
    box.innerText = `>>> 5-Stage RISC-V Pipeline Cycle Step (Unit 3):\n` +
      `[IF]  PC=0x00401040 : Fetching LW R1, 0(R2)\n` +
      `[ID]  PC=0x0040103C : Decoding ADD R3, R1, R4 (RAW Hazard Detected on R1!)\n` +
      `[EX]  Forwarding Unit Activated: MEM/WB bypass forwarded to EX ALU input.\n` +
      `[MEM] Memory Access Nominal (Cache Hit on L1 Data Cache).\n` +
      `[WB]  Committed 0x00000042 into Register R5. 0 Stalls inserted.`;
    this.showToast("Pipeline cycle stepped with hazard forwarding");
  }

  runMesiDemo() {
    const box = document.getElementById("labOutputBox");
    if (!box) return;
    box.innerText = `>>> MESI Cache Coherence Bus Snoop Simulation (Unit 4):\n` +
      `Core 1 issues Processor Write (PrWr) on address 0x7FFF.\n` +
      `Snoop Bus Broadcast: Invalidation signal asserted across interconnect.\n` +
      `Core 0 Cache Block transitions: Exclusive (E) -> Invalid (I)\n` +
      `Core 1 Cache Block transitions: Shared (S) -> Modified (M)\n` +
      `Bus arbitration granted in 1 cycle. Coherence maintained.`;
    this.showToast("MESI bus snoop broadcast executed");
  }

  showToast(msg) {
    let container = document.getElementById("toastContainer");
    if (!container) {
      container = document.createElement("div");
      container.id = "toastContainer";
      container.className = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = "toast-msg";
    toast.innerHTML = `<span>⚡</span> ${msg}`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      toast.style.transition = "all 0.25s ease-out";
      setTimeout(() => toast.remove(), 250);
    }, 3200);
  }
}

// Instantiate client on DOM ready
let app;
document.addEventListener("DOMContentLoaded", () => {
  app = new APTSClient();
});
