import type {
  User,
  Profile,
  Resume,
  Job,
  JobMatch,
  JobSearchParams,
  Application,
  Notification,
  Recruiter,
  ScheduledSearch,
  AnalyticsSnapshot,
} from "@/types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

class ApiClient {
  private token: string | null = null

  setToken(token: string | null) {
    this.token = token
    if (token) {
      localStorage.setItem("token", token)
    } else {
      localStorage.removeItem("token")
    }
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = typeof window !== "undefined" ? localStorage.getItem("token") : null
    }
    return this.token
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken()
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    })

    if (response.status === 401) {
      this.setToken(null)
      if (typeof window !== "undefined") {
        window.location.href = "/login"
      }
      throw new Error("Unauthorized")
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }))
      throw new Error(error.detail || "Request failed")
    }

    return response.json()
  }

  // Auth
  async register(email: string, password: string, fullName?: string) {
    return this.request<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    })
  }

  async login(email: string, password: string) {
    return this.request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
  }

  async getMe() {
    return this.request<User>("/auth/me")
  }

  // Profile
  async getProfile() {
    return this.request<Profile>("/profile")
  }

  async updateProfile(data: Partial<Profile>) {
    return this.request<Profile>("/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    })
  }

  // Resumes
  async uploadResume(file: File) {
    const formData = new FormData()
    formData.append("file", file)
    const token = this.getToken()
    const response = await fetch(`${API_BASE_URL}/resumes/upload`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })
    if (!response.ok) throw new Error("Upload failed")
    return response.json() as Promise<Resume>
  }

  async getResumes() {
    return this.request<Resume[]>("/resumes")
  }

  async getResume(id: number) {
    return this.request<Resume>(`/resumes/${id}`)
  }

  async deleteResume(id: number) {
    return this.request<void>(`/resumes/${id}`, { method: "DELETE" })
  }

  async setPrimaryResume(id: number) {
    return this.request<Resume>(`/resumes/${id}/primary`, { method: "PUT" })
  }

  // Jobs
  async searchJobs(params: JobSearchParams) {
    return this.request<Job[]>("/jobs/search", {
      method: "POST",
      body: JSON.stringify(params),
    })
  }

  async getJobs(skip = 0, limit = 20) {
    return this.request<Job[]>(`/jobs?skip=${skip}&limit=${limit}`)
  }

  async getJob(id: number) {
    return this.request<Job>(`/jobs/${id}`)
  }

  async createJob(data: Partial<Job>) {
    return this.request<Job>("/jobs", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async saveJob(jobId: number) {
    return this.request<any>(`/jobs/${jobId}/save`, { method: "POST" })
  }

  async unsaveJob(jobId: number) {
    return this.request<void>(`/jobs/${jobId}/save`, { method: "DELETE" })
  }

  async getSavedJobs() {
    return this.request<any[]>("/jobs/saved")
  }

  async matchJob(jobId: number) {
    return this.request<JobMatch>(`/jobs/${jobId}/match`, { method: "POST" })
  }

  async getJobStats() {
    return this.request<any>("/jobs/stats")
  }

  // Applications
  async createApplication(data: { job_id: number; resume_id?: number }) {
    return this.request<Application>("/applications", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async getApplications(status?: string, skip = 0, limit = 20) {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
    if (status) params.append("status", status)
    return this.request<Application[]>(`/applications?${params}`)
  }

  async getApplication(id: number) {
    return this.request<Application>(`/applications/${id}`)
  }

  async updateApplicationStatus(id: number, status: string, notes?: string) {
    return this.request<Application>(`/applications/${id}/status`, {
      method: "PUT",
      body: JSON.stringify({ status, notes }),
    })
  }

  async getApplicationStats() {
    return this.request<any>("/applications/stats")
  }

  async getPipeline() {
    return this.request<any>("/applications/pipeline")
  }

  async getFollowUps() {
    return this.request<any[]>("/applications/follow-ups")
  }

  // Analytics
  async getDashboardSummary() {
    return this.request<AnalyticsSnapshot>("/analytics/dashboard")
  }

  async getSkillsDemand() {
    return this.request<any[]>("/analytics/skills-demand")
  }

  async getJobMarket() {
    return this.request<any>("/analytics/job-market")
  }

  async getSkillCoverage() {
    return this.request<any>("/analytics/skill-coverage")
  }

  async getResumePerformance() {
    return this.request<any>("/analytics/resume-performance")
  }

  // AI
  async tailorResume(resumeId: number, jobId: number) {
    return this.request<any>("/ai/tailor-resume", {
      method: "POST",
      body: JSON.stringify({ resume_id: resumeId, job_id: jobId }),
    })
  }

  async generateCoverLetter(resumeId: number, jobId: number) {
    return this.request<any>("/ai/cover-letter", {
      method: "POST",
      body: JSON.stringify({ resume_id: resumeId, job_id: jobId }),
    })
  }

  async analyzeSkillGap(targetRole: string) {
    return this.request<any>("/ai/skill-gap", {
      method: "POST",
      body: JSON.stringify({ target_role: targetRole }),
    })
  }

  // Notifications
  async getNotifications(unreadOnly = false) {
    return this.request<Notification[]>(`/notifications?unread_only=${unreadOnly}`)
  }

  async getUnreadCount() {
    return this.request<{ count: number }>("/notifications/unread-count")
  }

  async markNotificationRead(id: number) {
    return this.request<any>(`/notifications/${id}/read`, { method: "PUT" })
  }

  // Recruiters
  async getRecruiters() {
    return this.request<any[]>("/recruiters")
  }

  async createRecruiter(data: any) {
    return this.request<any>("/recruiters", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  // Scheduled Searches
  async getScheduledSearches() {
    return this.request<ScheduledSearch[]>("/scheduled-searches")
  }

  async createScheduledSearch(data: any) {
    return this.request<ScheduledSearch>("/scheduled-searches", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }
}

export const api = new ApiClient()
export default api
