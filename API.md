# API Documentation

## Base URL

```
Development: http://localhost:5000/api
Production: https://api.yourdomain.com/api
```

## Authentication

### JWT Token Authentication

All protected endpoints require a valid JWT token in the Authorization header.

```
Authorization: Bearer <access_token>
```

### Token Lifecycle

1. **Access Token**: Short-lived (15 minutes), used for API requests
2. **Refresh Token**: Long-lived (7 days), used to obtain new access tokens

### Obtaining Tokens

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123",
  "name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "createdAt": "2024-01-15T10:30:00Z"
    },
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
  },
  "message": "User registered successfully"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe"
    },
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
  },
  "message": "Login successful"
}
```

#### Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
  },
  "message": "Tokens refreshed successfully"
}
```

---

## Endpoints

### Profiles

#### Get All Profiles
```http
GET /api/profiles
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "Senior Software Engineer",
      "summary": "Experienced developer with 5+ years...",
      "resumeUrl": "/uploads/resumes/resume.pdf",
      "skills": ["JavaScript", "TypeScript", "React", "Node.js"],
      "experience": 5,
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    }
  ],
  "meta": {
    "total": 1,
    "page": 1,
    "limit": 10
  }
}
```

#### Get Profile by ID
```http
GET /api/profiles/:id
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Senior Software Engineer",
    "summary": "Experienced developer with 5+ years...",
    "resumeUrl": "/uploads/resumes/resume.pdf",
    "skills": ["JavaScript", "TypeScript", "React", "Node.js"],
    "experience": 5,
    "education": [
      {
        "institution": "University of Technology",
        "degree": "Bachelor of Science",
        "field": "Computer Science",
        "graduationYear": 2019
      }
    ],
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

#### Create Profile
```http
POST /api/profiles
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Senior Software Engineer",
  "summary": "Experienced developer with 5+ years...",
  "skills": ["JavaScript", "TypeScript", "React", "Node.js"],
  "experience": 5,
  "education": [
    {
      "institution": "University of Technology",
      "degree": "Bachelor of Science",
      "field": "Computer Science",
      "graduationYear": 2019
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Senior Software Engineer",
    "summary": "Experienced developer with 5+ years...",
    "skills": ["JavaScript", "TypeScript", "React", "Node.js"],
    "experience": 5,
    "createdAt": "2024-01-15T10:30:00Z"
  },
  "message": "Profile created successfully"
}
```

#### Update Profile
```http
PUT /api/profiles/:id
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Lead Software Engineer",
  "summary": "Updated summary..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Lead Software Engineer",
    "summary": "Updated summary...",
    "updatedAt": "2024-01-15T11:00:00Z"
  },
  "message": "Profile updated successfully"
}
```

#### Delete Profile
```http
DELETE /api/profiles/:id
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Profile deleted successfully"
}
```

#### Upload Resume
```http
POST /api/profiles/upload-resume
Authorization: Bearer <token>
Content-Type: multipart/form-data

resume: <file.pdf>
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "resumeUrl": "/uploads/resumes/uuid-resume.pdf",
    "parsedData": {
      "skills": ["JavaScript", "TypeScript", "React"],
      "experience": "5 years",
      "education": "Bachelor of Science in Computer Science"
    }
  },
  "message": "Resume uploaded and parsed successfully"
}
```

---

### Jobs

#### Search Jobs
```http
GET /api/jobs/search?query=javascript+developer&location=remote&page=1&limit=10
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| query | string | Search keywords |
| location | string | Job location filter |
| portal | string | Filter by portal (linkedin, indeed, glassdoor) |
| salary_min | number | Minimum salary |
| salary_max | number | Maximum salary |
| page | number | Page number (default: 1) |
| limit | number | Results per page (default: 10) |

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "portal": "linkedin",
      "title": "JavaScript Developer",
      "company": "Tech Corp",
      "location": "Remote",
      "salary": "$80,000 - $120,000",
      "description": "We are looking for a JavaScript developer...",
      "requirements": ["JavaScript", "React", "Node.js"],
      "url": "https://linkedin.com/jobs/view/...",
      "postedAt": "2024-01-14T09:00:00Z",
      "applied": false
    }
  ],
  "meta": {
    "total": 50,
    "page": 1,
    "limit": 10
  }
}
```

#### Get Job Details
```http
GET /api/jobs/:id
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "portal": "linkedin",
    "title": "JavaScript Developer",
    "company": "Tech Corp",
    "location": "Remote",
    "salary": "$80,000 - $120,000",
    "description": "Full job description...",
    "requirements": ["JavaScript", "React", "Node.js"],
    "benefits": ["Health insurance", "401k", "Remote work"],
    "url": "https://linkedin.com/jobs/view/...",
    "postedAt": "2024-01-14T09:00:00Z",
    "expiresAt": "2024-02-14T09:00:00Z"
  }
}
```

#### Track Job
```http
POST /api/jobs/track
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://linkedin.com/jobs/view/...",
  "notes": "Interesting position at Tech Corp"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "url": "https://linkedin.com/jobs/view/...",
    "notes": "Interesting position at Tech Corp",
    "status": "tracked",
    "createdAt": "2024-01-15T10:30:00Z"
  },
  "message": "Job tracked successfully"
}
```

---

### Applications

#### Get All Applications
```http
GET /api/applications?status=pending&page=1&limit=10
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter: pending, applied, interviewing, rejected, accepted |
| profile_id | string | Filter by profile |
| portal | string | Filter by portal |
| page | number | Page number |
| limit | number | Results per page |

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "jobId": "job-uuid",
      "profileId": "profile-uuid",
      "status": "applied",
      "appliedAt": "2024-01-15T10:30:00Z",
      "job": {
        "title": "JavaScript Developer",
        "company": "Tech Corp",
        "portal": "linkedin"
      },
      "coverLetter": "Generated cover letter...",
      "customResume": "/uploads/resumes/custom-resume.pdf"
    }
  ],
  "meta": {
    "total": 25,
    "page": 1,
    "limit": 10
  }
}
```

#### Create Application
```http
POST /api/applications
Authorization: Bearer <token>
Content-Type: application/json

{
  "jobId": "job-uuid",
  "profileId": "profile-uuid",
  "coverLetter": "Custom cover letter...",
  "autoApply": true
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "jobId": "job-uuid",
    "profileId": "profile-uuid",
    "status": "queued",
    "autoApply": true,
    "createdAt": "2024-01-15T10:30:00Z"
  },
  "message": "Application queued successfully"
}
```

#### Update Application Status
```http
PUT /api/applications/:id
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "interviewing",
  "notes": "Phone screen scheduled for Jan 20",
  "interviewDate": "2024-01-20T14:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "interviewing",
    "notes": "Phone screen scheduled for Jan 20",
    "interviewDate": "2024-01-20T14:00:00Z",
    "updatedAt": "2024-01-15T11:00:00Z"
  },
  "message": "Application updated successfully"
}
```

#### Delete Application
```http
DELETE /api/applications/:id
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Application deleted successfully"
}
```

---

### Analytics

#### Get Dashboard Analytics
```http
GET /api/analytics/dashboard
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "overview": {
      "totalApplications": 150,
      "applied": 120,
      "interviewing": 15,
      "accepted": 5,
      "rejected": 10
    },
    "responseRate": 0.25,
    "averageResponseTime": "5 days",
    "applicationsByPortal": {
      "linkedin": 60,
      "indeed": 40,
      "glassdoor": 30,
      "naukri": 20
    },
    "applicationsByMonth": [
      {
        "month": "2024-01",
        "count": 45
      },
      {
        "month": "2023-12",
        "count": 38
      }
    ],
    "topSkills": [
      {
        "skill": "JavaScript",
        "applications": 80
      },
      {
        "skill": "React",
        "applications": 65
      }
    ]
  }
}
```

#### Generate Report
```http
POST /api/analytics/reports
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "monthly",
  "dateRange": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "format": "pdf"
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "reportId": "report-uuid",
    "status": "generating",
    "estimatedCompletion": "2024-01-15T10:35:00Z"
  },
  "message": "Report generation started"
}
```

#### Download Report
```http
GET /api/analytics/reports/:id/download
Authorization: Bearer <token>
```

**Response:** Binary file (PDF/CSV)

---

### Automation

#### Start Automation
```http
POST /api/automation/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "profileId": "profile-uuid",
  "portals": ["linkedin", "indeed"],
  "filters": {
    "keywords": "javascript developer",
    "location": "remote",
    "salaryMin": 80000
  },
  "settings": {
    "maxApplicationsPerDay": 50,
    "delayBetweenApplications": 60,
    "autoGenerateCoverLetter": true
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "jobId": "automation-job-uuid",
    "status": "running",
    "startedAt": "2024-01-15T10:30:00Z",
    "estimatedDuration": "2 hours"
  },
  "message": "Automation started successfully"
}
```

#### Stop Automation
```http
POST /api/automation/stop
Authorization: Bearer <token>
Content-Type: application/json

{
  "jobId": "automation-job-uuid"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "jobId": "automation-job-uuid",
    "status": "stopped",
    "stoppedAt": "2024-01-15T11:00:00Z",
    "applicationsSubmitted": 25
  },
  "message": "Automation stopped successfully"
}
```

#### Get Automation Status
```http
GET /api/automation/status
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "activeJobs": [
      {
        "jobId": "automation-job-uuid",
        "status": "running",
        "progress": {
          "total": 50,
          "completed": 25,
          "failed": 2,
          "skipped": 3
        },
        "currentPortal": "linkedin",
        "startedAt": "2024-01-15T10:30:00Z",
        "estimatedCompletion": "2024-01-15T12:30:00Z"
      }
    ],
    "queueLength": 25
  }
}
```

---

### Users

#### Get Current User
```http
GET /api/users/me
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "createdAt": "2024-01-15T10:30:00Z",
    "subscription": {
      "plan": "pro",
      "expiresAt": "2025-01-15T10:30:00Z"
    }
  }
}
```

#### Update User
```http
PUT /api/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "John Smith",
  "email": "john.smith@example.com"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "john.smith@example.com",
    "name": "John Smith",
    "updatedAt": "2024-01-15T11:00:00Z"
  },
  "message": "User updated successfully"
}
```

#### Change Password
```http
POST /api/users/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "currentPassword": "oldPassword123",
  "newPassword": "newPassword456"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

## Error Codes

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (for async operations) |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request body contains invalid fields",
    "details": {
      "email": "Email format is invalid",
      "password": "Password must be at least 8 characters"
    }
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| AUTH_001 | Invalid credentials |
| AUTH_002 | Token expired |
| AUTH_003 | Token invalid |
| AUTH_004 | Insufficient permissions |
| VAL_001 | Required field missing |
| VAL_002 | Invalid field format |
| VAL_003 | Field exceeds maximum length |
| RES_001 | Resource not found |
| RES_002 | Resource already exists |
| SERV_001 | Internal server error |
| SERV_002 | External service unavailable |
| RATE_001 | Rate limit exceeded |

---

## Rate Limiting

### Limits

| Plan | Requests per Minute | Requests per Day |
|------|--------------------|--------------------|
| Free | 60 | 1,000 |
| Pro | 300 | 10,000 |
| Enterprise | 1,000 | 100,000 |

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705312200
```

### Rate Limit Response

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 30

{
  "success": false,
  "error": {
    "code": "RATE_001",
    "message": "Rate limit exceeded. Please try again in 30 seconds.",
    "retryAfter": 30
  }
}
```

---

## Pagination

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | number | 1 | Page number |
| limit | number | 10 | Results per page (max: 100) |

### Response Meta

```json
{
  "meta": {
    "total": 150,
    "page": 1,
    "limit": 10,
    "totalPages": 15,
    "hasNext": true,
    "hasPrev": false
  }
}
```

---

## Filtering

### Query Parameters

Most list endpoints support filtering:

```http
GET /api/applications?status=applied&portal=linkedin&sort=-createdAt
```

### Sort Parameters

Prefix with `-` for descending order:

```http
GET /api/jobs?sort=-postedAt
GET /api/applications?sort=status,-createdAt
```

---

## Webhooks (Coming Soon)

### Register Webhook
```http
POST /api/webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["application.status_changed", "automation.completed"]
}
```

### Webhook Events

| Event | Description |
|-------|-------------|
| application.created | New application submitted |
| application.status_changed | Application status updated |
| automation.started | Automation job started |
| automation.completed | Automation job finished |
| automation.failed | Automation job failed |

### Webhook Payload

```json
{
  "event": "application.status_changed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "applicationId": "uuid",
    "oldStatus": "applied",
    "newStatus": "interviewing"
  }
}
```
