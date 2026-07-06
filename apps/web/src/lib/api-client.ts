const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const API_V1 = `${API_BASE_URL}/api/v1`;

export interface Project {
  id: string;
  name: string;
  client_name?: string;
  client_email?: string;
  client_user_id?: string;
  description?: string;
  repository_url?: string;
  jira_project_key?: string;
  status: "Draft" | "In Progress" | "Completed" | string;
  status_reason?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface RequirementVersion {
  id: string;
  requirement_id: string;
  version_number: number;
  content: string;
  change_summary?: string;
  ai_summary?: string;
  status: string;
  is_baseline: boolean;
  created_at: string;
}

export interface Requirement {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  versions?: RequirementVersion[];
  created_at: string;
}

export interface AlignmentResult {
  id: string;
  project_id: string;
  requirement_version_id: string;
  jira_story_id?: string;
  pull_request_id?: string;
  code_artifact_id?: string;

  // Human-readable chain labels returned by backend
  requirement_title?: string;
  jira_story_title?: string;
  pull_request_title?: string;
  code_artifact_name?: string;
  code_artifact_path?: string;

  requirement_jira_score?: number;
  jira_pr_score?: number;
  pr_artifact_score?: number;
  overall_alignment_score: number;
  alignment_status: "Aligned" | "Potential Drift" | "Misaligned";
  confidence: number;
  explanation?: string;
  score: number;
  summary?: string;
  created_at: string;
  updated_at: string;
}

export interface MismatchReport {
  id: string;
  project_id: string;
  alignment_result_id: string;
  requirement_title?: string;
  mismatch_type: string;
  description: string;
  suggested_fix?: string;
  status: "Open" | "Reviewed" | "Resolved";
  severity: "Critical" | "High" | "Medium" | "Low";
  reviewed_by_id?: string;
  reviewed_at?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectHealth {
  health_score: number;
  health_status: "Excellent" | "Good" | "Needs Attention" | "Critical";
  total_requirements: number;
  approved_requirements: number;
  aligned_count: number;
  drift_count: number;
  misaligned_count: number;
  open_mismatches: number;
  resolved_mismatches: number;
  avg_alignment_score: number;
  drift_percentage: number;
}

export interface ExecutiveReport {
  project_summary: {
    name: string;
    client_name: string;
    status: string;
    created_at: string;
  };
  alignment_overview: {
    total: number;
    aligned: number;
    drift: number;
    misaligned: number;
    avg_score: number;
  };
  top_risks: Array<{
    mismatch_type: string;
    description: string;
    severity: string;
    status: string;
  }>;
  health: ProjectHealth;
  narrative: string;
  recommendations: string | string[];
}

// Fetch helper that automatically includes cookies/headers
async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const url = endpoint.startsWith("http") ? endpoint : `${API_V1}${endpoint}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  async function executeFetch(useAuth: boolean) {
    const requestHeaders = new Headers(headers);
    if (!useAuth) {
      requestHeaders.delete("Authorization");
    }
    return fetch(url, {
      ...options,
      headers: requestHeaders,
      credentials: "include",
    });
  }

  let response = await executeFetch(!!token);

  if (response.status === 401 && token) {
    // Token might be expired — try to refresh it
    try {
      const refreshToken = typeof window !== "undefined" ? localStorage.getItem("refreshToken") : null;
      if (refreshToken) {
        const refreshResponse = await fetch(`${API_V1}/auth/token/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh: refreshToken }),
        });
        if (refreshResponse.ok) {
          const refreshData = await refreshResponse.json();
          if (refreshData.access) {
            localStorage.setItem("token", refreshData.access);
            headers.set("Authorization", `Bearer ${refreshData.access}`);
            response = await executeFetch(true);
          }
        }
      }
    } catch {
      // Refresh failed — fall through to error handling below
    }

    if (response.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
        localStorage.removeItem("refreshToken");
      }
      throw new Error("Session expired. Please log in again.");
    }
  } else if (response.status === 401) {
    throw new Error("Authentication credentials were not provided.");
  }

  if (!response.ok) {
    let errorDetail = "API Request failed";
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch (error: unknown) { void error; }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Auth
  async login(formData: URLSearchParams) {
    const data = await apiFetch("/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    });
    if (data.access_token) {
      localStorage.setItem("token", data.access_token);
    }
    if (data.refresh_token) {
      localStorage.setItem("refreshToken", data.refresh_token);
    }
    return data;
  },

  async register(userData: Record<string, unknown>) {
    return apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify(userData),
    });
  },

  async getMe() {
    return apiFetch("/auth/me");
  },

  async logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    try {
      return await apiFetch("/auth/logout", { method: "POST" });
    } catch (error: unknown) { void error; 
      return { message: "Logged out" };
    }
  },

  // Projects
  async getProjects(): Promise<Project[]> {
    return apiFetch("/projects");
  },

  async getProject(id: string): Promise<Project> {
    return apiFetch(`/projects/${id}`);
  },

  async createProject(project: Omit<Project, "id" | "created_at" | "updated_at" | "owner_id" | "status" | "status_reason"> & { owner_id?: string }): Promise<Project> {
    // For MVP/Demo purposes, we'll try to find a user or use a dummy owner_id if not present
    let owner_id = project.owner_id;
    if (!owner_id) {
      try {
        const me = await this.getMe();
        owner_id = me.id;
      } catch (error: unknown) { void error; 
        // Fallback to random/dummy UUID for unauthenticated dev mode
        owner_id = "00000000-0000-0000-0000-000000000000";
      }
    }
    return apiFetch("/projects", {
      method: "POST",
      body: JSON.stringify({ ...project, owner_id }),
    });
  },

  async updateProject(id: string, project: Partial<Project>): Promise<Project> {
    return apiFetch(`/projects/${id}`, {
      method: "PUT",
      body: JSON.stringify(project),
    });
  },

  async deleteProject(id: string): Promise<unknown> {
    return apiFetch(`/projects/${id}`, {
      method: "DELETE",
    });
  },

  // Requirements & Upload
  async uploadBRD(projectId: string, file: File): Promise<unknown> {
    const formData = new FormData();
    formData.append("file", file);
    return apiFetch(`/projects/${projectId}/upload-brd`, {
      method: "POST",
      body: formData,
    });
  },

  async getRequirements(projectId: string): Promise<RequirementVersion[]> {
    return apiFetch(`/requirements/project/${projectId}`);
  },

  async reviewRequirement(versionId: string, action: "approve" | "request_changes", comment?: string): Promise<unknown> {
    return apiFetch(`/requirements/${versionId}/review`, {
      method: "POST",
      body: JSON.stringify({ action, comment }),
    });
  },

  async getApprovals(): Promise<unknown[]> {
    return apiFetch("/requirements/approvals");
  },

  // Jira Integration
  async getJiraStatus() {
    return apiFetch("/jira/status");
  },

  async syncJiraStories(projectId: string) {
    return apiFetch(`/jira/projects/${projectId}/sync`, { method: "POST" });
  },

  async getJiraStories(projectId: string) {
    return apiFetch(`/jira/projects/${projectId}/stories`);
  },

  // GitHub Integration
  async getGitHubStatus() {
    return apiFetch("/github/status");
  },

  async syncPullRequests(projectId: string, state: string = "all") {
    return apiFetch(`/github/projects/${projectId}/sync-prs?state=${state}`, { method: "POST" });
  },

  async getPullRequests(projectId: string) {
    return apiFetch(`/github/projects/${projectId}/prs`);
  },

  // Code Extraction
  async extractSymbols(prId: string) {
    return apiFetch(`/github/prs/${prId}/extract-symbols`, { method: "POST" });
  },

  async getSymbols(prId: string, typeFilter?: string) {
    const url = typeFilter 
      ? `/github/prs/${prId}/symbols?artifact_type=${encodeURIComponent(typeFilter)}` 
      : `/github/prs/${prId}/symbols`;
    return apiFetch(url);
  },

  // Alignment Engine
  async runAlignment(projectId: string): Promise<{ message: string; results_generated: number }> {
    return apiFetch(`/alignment/run/${projectId}`, { method: "POST" });
  },

  async indexProjectArtifacts(projectId: string) {
    return apiFetch(`/alignment/index/${projectId}`, { method: "POST" });
  },

  async getAlignmentResults(projectId: string): Promise<AlignmentResult[]> {
    return apiFetch(`/alignment/results/${projectId}`);
  },

  async getAlignmentResultDetail(resultId: string): Promise<AlignmentResult> {
    return apiFetch(`/alignment/result/${resultId}`);
  },

  // ── Reports & Insights ────────────────────────────────────────────────────

  async generateMismatchReports(projectId: string) {
    return apiFetch(`/reporting/mismatches/generate/${projectId}`, { method: "POST" });
  },

  async getMismatchReports(projectId: string, status?: string, severity?: string): Promise<MismatchReport[]> {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (severity) params.set("severity", severity);
    const qs = params.toString();
    return apiFetch(`/reporting/mismatches/${projectId}${qs ? `?${qs}` : ""}`);
  },

  async updateMismatchReport(mismatchId: string, data: { status?: string; resolution_notes?: string }) {
    return apiFetch(`/reporting/mismatch/${mismatchId}/resolve`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async getProjectHealth(projectId: string): Promise<ProjectHealth> {
    return apiFetch(`/reporting/risk-dashboard/${projectId}`);
  },

  async getExecutiveReport(projectId: string): Promise<ExecutiveReport> {
    return apiFetch(`/reporting/executive-summary/${projectId}`);
  },

  async exportMismatchesCsv(projectId: string) {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const response = await fetch(`${API_V1}/reports/export/mismatches/${projectId}?format=csv`, {
      headers,
      credentials: "omit",
    });
    return response.blob();
  },

  async exportExecutiveCsv(projectId: string) {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const response = await fetch(`${API_V1}/reports/export/executive/${projectId}?format=csv`, {
      headers,
      credentials: "omit",
    });
    return response.blob();
  },

  // System
  async getSystemHealth() {
    return apiFetch("/system/health");
  },

  // Client
  client: {
    async getProjects() {
      return apiFetch("/client/projects");
    },

    async getRequirementVersions(projectId: string) {
      return apiFetch(`/client/projects/${projectId}/requirement-versions`);
    },

    async approveRequirementVersion(projectId: string, versionId: string, comment?: string) {
      return apiFetch(`/client/projects/${projectId}/requirement-versions/${versionId}/approve`, {
        method: "POST",
        body: JSON.stringify({ comment }),
      });
    },

    async rejectRequirementVersion(projectId: string, versionId: string, comment: string) {
      return apiFetch(`/client/projects/${projectId}/requirement-versions/${versionId}/reject`, {
        method: "POST",
        body: JSON.stringify({ comment }),
      });
    },
  },

  // Notifications
  notifications: {
    async getAll() {
      return apiFetch("/notifications");
    },

    async getUnreadCount() {
      return apiFetch("/notifications/unread/count");
    },

    async markAsRead(id: string) {
      return apiFetch(`/notifications/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_read: true }),
      });
    },

    async delete(id: string) {
      return apiFetch(`/notifications/${id}`, {
        method: "DELETE",
      });
    },
  },
};
