export interface User {
  id: number
  email: string
  full_name: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Profile {
  id: number
  user_id: number
  full_name: string | null
  phone: string | null
  location: string | null
  bio: string | null
  linkedin_url: string | null
  github_url: string | null
  portfolio_url: string | null
  years_experience: number | null
  education_level: string | null
  desired_salary_min: number | null
  desired_salary_max: number | null
  desired_job_types: string[] | null
  desired_locations: string[] | null
  is_remote_only: boolean
  skills: string[] | null
  created_at: string
  updated_at: string
}

export interface Resume {
  id: number
  user_id: number
  filename: string
  original_filename: string
  file_size: number
  mime_type: string
  ats_score: number | null
  is_primary: boolean
  parsed_content: string | null
  extracted_skills: string[] | null
  created_at: string
  updated_at: string
}

export interface ResumeVersion {
  id: number
  resume_id: number
  version_number: number
  content: string
  created_at: string
}

export interface Job {
  id: number
  title: string
  company: string
  location: string | null
  job_type: string | null
  description: string | null
  requirements: string | null
  salary_min: number | null
  salary_max: number | null
  url: string | null
  source: string | null
  posted_date: string | null
  is_remote: boolean
  skills_required: string[] | null
  match_score: number | null
  is_saved: boolean
  created_at: string
  updated_at: string
}

export interface JobMatch {
  job_id: number
  match_score: number
  matching_skills: string[]
  missing_skills: string[]
  recommendations: string[]
}

export interface JobSearchParams {
  query?: string
  location?: string
  job_type?: string
  min_salary?: number
  max_salary?: number
  skills?: string[]
  is_remote?: boolean
  skip?: number
  limit?: number
}

export interface Application {
  id: number
  user_id: number
  job_id: number
  resume_id: number | null
  status: string
  applied_at: string | null
  last_updated: string
  notes: string | null
  follow_up_date: string | null
  job?: Job
  resume?: Resume
}

export interface ApplicationEvent {
  id: number
  application_id: number
  event_type: string
  description: string | null
  created_at: string
}

export interface Recruiter {
  id: number
  user_id: number
  name: string
  email: string | null
  company: string | null
  linkedin_url: string | null
  notes: string | null
  created_at: string
}

export interface Communication {
  id: number
  recruiter_id: number
  application_id: number | null
  channel: string
  subject: string | null
  body: string | null
  sent_at: string
}

export interface Notification {
  id: number
  user_id: number
  title: string
  message: string
  is_read: boolean
  notification_type: string
  link: string | null
  created_at: string
}

export interface ScheduledSearch {
  id: number
  user_id: number
  name: string
  query: string | null
  location: string | null
  job_type: string | null
  min_salary: number | null
  frequency: string
  is_active: boolean
  last_run_at: string | null
  created_at: string
}

export interface AnalyticsSnapshot {
  total_jobs_found: number
  total_applications: number
  total_interviews: number
  total_offers: number
  applications_this_week: number
  applications_this_month: number
  response_rate: number
  interview_rate: number
  offer_rate: number
}

export interface AutomationRun {
  id: number
  user_id: number
  run_type: string
  status: string
  jobs_found: number
  applications_submitted: number
  started_at: string
  completed_at: string | null
  error_message: string | null
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  full_name?: string
}

export interface Settings {
  emailNotifications: boolean
  jobAlerts: boolean
  weeklyDigest: boolean
  darkMode: boolean
  language: string
}

export interface NavItem {
  title: string
  href: string
  icon: string
  badge?: number
}
