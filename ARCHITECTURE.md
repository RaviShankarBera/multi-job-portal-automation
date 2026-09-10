# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Web Browser │  │ Mobile App   │  │  CLI Client  │  │  Third-Party │   │
│  │   (React)    │  │  (Future)    │  │   (Future)   │  │   Clients    │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │             │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API GATEWAY                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Load Balancer (Nginx)                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │   Rate   │  │   SSL    │  │   CORS   │  │  Request         │  │   │
│  │  │ Limiter  │  │Terminal  │  │ Handler  │  │  Validation      │  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND SERVICES                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     API Server (Express.js)                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │   Auth   │  │ Profile  │  │   Job    │  │   Application    │  │   │
│  │  │ Service  │  │ Service  │  │ Service  │  │    Service       │  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │Analytics │  │ Email    │  │  File    │  │   Notification   │  │   │
│  │  │ Service  │  │ Service  │  │ Service  │  │    Service       │  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   Automation Engine                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │ Browser  │  │  Portal  │  │    AI    │  │   Form Filler    │  │   │
│  │  │ Manager  │  │ Adapter  │  │  Engine  │  │    Engine        │  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Worker Processes                                │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │  Email   │  │  Report  │  │ Cleanup  │  │   Health Check   │  │   │
│  │  │ Worker   │  │ Worker   │  │ Worker   │  │     Worker       │  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │                                    │
          ▼                                    ▼
┌──────────────────────┐          ┌──────────────────────┐
│    DATA LAYER        │          │   EXTERNAL SERVICES   │
│                      │          │                      │
│ ┌────────────────┐  │          │ ┌────────────────┐  │
│ │  PostgreSQL    │  │          │ │  OpenAI API    │  │
│ │  (Primary DB)  │  │          │ │  (GPT-4)       │  │
│ └────────────────┘  │          │ └────────────────┘  │
│ ┌────────────────┐  │          │ ┌────────────────┐  │
│ │    Redis       │  │          │ │  Email SMTP    │  │
│ │ (Cache/Queue)  │  │          │ │  (Gmail/etc)   │  │
│ └────────────────┘  │          │ └────────────────┘  │
│ ┌────────────────┐  │          │ ┌────────────────┐  │
│ │  File Storage  │  │          │ │ Job Portals    │  │
│ │  (Local/S3)    │  │          │ │ (LinkedIn/etc) │  │
│ └────────────────┘  │          │ └────────────────┘  │
└──────────────────────┘          └──────────────────────┘
```

## Component Descriptions

### 1. Client Layer

| Component | Technology | Description |
|-----------|------------|-------------|
| Web Browser | React 18 + TypeScript | Main user interface for managing profiles, applications, and analytics |
| Mobile App | React Native (Future) | Mobile interface for on-the-go management |
| CLI Client | Node.js (Future) | Command-line interface for power users |
| Third-Party | REST API | Integration with external tools and services |

### 2. API Gateway

- **Load Balancer**: Nginx handles incoming requests and distributes load
- **Rate Limiter**: Prevents API abuse with configurable limits per user/IP
- **SSL/TLS**: HTTPS termination for all secure communications
- **CORS Handler**: Manages cross-origin resource sharing policies
- **Request Validation**: Input sanitization and validation at the gateway level

### 3. Backend Services

#### Authentication Service
- JWT token generation and validation
- Refresh token rotation
- OAuth2 integration (Google, LinkedIn)
- Password hashing with bcrypt
- Session management

#### Profile Service
- CRUD operations for user profiles
- Resume upload and parsing
- Skills extraction and matching
- Profile optimization suggestions

#### Job Service
- Job listing aggregation from multiple portals
- Job search with filters and sorting
- Job tracking and bookmarking
- Application deadline management

#### Application Service
- Application tracking and status updates
- Form data management
- Document attachment handling
- Interview scheduling integration

#### Analytics Service
- Dashboard metrics computation
- Application success rate tracking
- Response time analytics
- Custom report generation

#### Email Service
- Email monitoring and parsing
- Automatic categorization
- Response detection
- Notification dispatching

#### File Service
- Resume storage and versioning
- Document conversion (PDF, DOCX)
- File upload/download handling
- Storage quota management

#### Notification Service
- Real-time push notifications
- Email notifications
- In-app messaging
- Browser notifications

### 4. Automation Engine

#### Browser Manager
- Chromium browser pool management
- Proxy rotation support
- Browser fingerprint randomization
- Session persistence

#### Portal Adapter
- LinkedIn automation adapter
- Indeed automation adapter
- Glassdoor automation adapter
- Naukri automation adapter
- Custom portal adapter interface

#### AI Engine
- OpenAI GPT-4 integration
- Cover letter generation
- Resume tailoring
- Interview preparation

#### Form Filler Engine
- Smart field detection
- Context-aware form filling
- File upload automation
- CAPTCHA handling (ethical)

### 5. Worker Processes

- **Email Worker**: Processes incoming job-related emails
- **Report Worker**: Generates scheduled reports
- **Cleanup Worker**: Manages temporary files and old data
- **Health Check Worker**: Monitors system health and alerts

### 6. Data Layer

- **PostgreSQL**: Primary relational database for structured data
- **Redis**: Caching layer and message queue broker
- **File Storage**: Local filesystem or AWS S3 for file uploads

### 7. External Services

- **OpenAI API**: AI-powered content generation
- **Email SMTP**: Email sending capabilities
- **Job Portals**: External job listing sources

## Data Flow

### Job Application Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  User   │───▶│   API   │───▶│  Queue  │───▶│ Worker  │───▶│ Portal  │
│ Request │    │ Server  │    │ (Redis) │    │ Process │    │ Adapter │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │              │
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Submit  │    │ Validate│    │ Job     │    │ Browser │    │ Apply   │
│ Form    │    │ Data    │    │ Created │    │ Launch  │    │ to Job  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                       │
                                                       ▼
                                                ┌─────────┐
                                                │  Update │
                                                │ Status  │
                                                └─────────┘
```

### Email Processing Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Email  │───▶│  IMAP   │───▶│ Parser  │───▶│ Categor │
│ Server  │    │ Client  │    │ Service │    │  izer   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                          │
                                          ▼
                                   ┌─────────┐
                                   │ Update  │
                                   │ App     │
                                   │ Status  │
                                   └─────────┘
```

## Database Schema Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USERS TABLE                              │
├─────────────────────────────────────────────────────────────────┤
│ id (PK) │ email │ password_hash │ name │ created_at │ updated_at│
└─────────────────────────────────────────────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       PROFILES TABLE                             │
├─────────────────────────────────────────────────────────────────┤
│ id (PK) │ user_id (FK) │ title │ summary │ resume_url │ skills │
└─────────────────────────────────────────────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATIONS TABLE                           │
├─────────────────────────────────────────────────────────────────┤
│ id (PK) │ profile_id (FK) │ job_id (FK) │ status │ applied_at │
└─────────────────────────────────────────────────────────────────┘
           │                           │
           │ N:1                       │ N:1
           ▼                           ▼
┌─────────────────────────┐  ┌─────────────────────────────────────┐
│      PROFILES           │  │            JOBS TABLE                 │
│ (referenced above)      │  ├─────────────────────────────────────┤
└─────────────────────────┘  │ id (PK) │ portal │ title │ company  │
                             │ url │ location │ salary │ posted_at │
                             └─────────────────────────────────────┘
```

## API Design Principles

### RESTful Conventions
- Resource-based URLs (`/api/profiles`, `/api/applications`)
- Proper HTTP methods (GET, POST, PUT, DELETE)
- Consistent response format
- HATEOAS links where applicable

### Response Format
```json
{
  "success": true,
  "data": {},
  "meta": {
    "page": 1,
    "limit": 10,
    "total": 100
  },
  "message": "Success"
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {}
  }
}
```

### Versioning
- API versioning via URL path (`/api/v1/...`)
- Backward compatibility maintained for 6 months
- Deprecation notices provided in response headers

## Security Architecture

### Authentication Flow
```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Login  │───▶│ Validate│───▶│ Generate│───▶│  Store  │
│ Request │    │  User   │    │  JWT    │    │ in DB   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                       │
                                                       ▼
                                                ┌─────────┐
                                                │  Return │
                                                │ Tokens  │
                                                └─────────┘
```

### Security Layers
1. **Network Security**: HTTPS, WAF, DDoS protection
2. **Application Security**: Input validation, SQL injection prevention
3. **Authentication**: JWT with refresh token rotation
4. **Authorization**: Role-based access control (RBAC)
5. **Data Security**: Encryption at rest and in transit
6. **Logging**: Audit trails for all sensitive operations

## AI Architecture

### AI Integration Points
```
┌─────────────────────────────────────────────────────────────────┐
│                        AI SERVICES                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Resume     │    │    Cover     │    │   Interview  │      │
│  │  Optimizer   │    │   Letter     │    │   Prep       │      │
│  │   Engine     │    │  Generator   │    │   Assistant  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│          │                  │                  │                 │
│          └──────────────────┼──────────────────┘                 │
│                             │                                    │
│                             ▼                                    │
│                    ┌──────────────┐                              │
│                    │   OpenAI     │                              │
│                    │   GPT-4      │                              │
│                    │   API        │                              │
│                    └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

### AI Features
1. **Resume Optimization**: Analyzes job descriptions and optimizes resume keywords
2. **Cover Letter Generation**: Creates personalized cover letters for each application
3. **Interview Preparation**: Generates potential interview questions and answers
4. **Application Response Analysis**: Parses emails and categorizes responses

## Automation Architecture

### Browser Automation Stack
```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOMATION ENGINE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Puppeteer/Playwright                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │  │
│  │  │ Browser  │  │ Page     │  │ Element  │  │ Event  │  │  │
│  │  │ Context  │  │ Navigation│  │ Selector │  │ Handler│  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Portal Adapters                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │  │
│  │  │ LinkedIn │  │  Indeed  │  │ Glassdoor│  │ Naukri │  │  │
│  │  │ Adapter  │  │ Adapter  │  │ Adapter  │  │ Adapter│  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Automation Workflow
1. **Discovery**: Scan job portals for matching jobs
2. **Selection**: Filter jobs based on user preferences
3. **Application**: Automate form filling and submission
4. **Tracking**: Monitor application status
5. **Reporting**: Generate application reports

## Deployment Architecture

### Production Deployment
```
┌─────────────────────────────────────────────────────────────────┐
│                    PRODUCTION ENVIRONMENT                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Cloud Provider (AWS/GCP)                │  │
│  │                                                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │  │
│  │  │   EC2    │  │   RDS    │  │ ElastiCache│ │   S3   │  │  │
│  │  │ Instance │  │PostgreSQL│  │  (Redis)  │  │Storage │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────┘  │  │
│  │                                                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │  │
│  │  │   ALB    │  │Route53   │  │  ACM     │               │  │
│  │  │   (LB)   │  │  (DNS)   │  │  (SSL)   │               │  │
│  │  └──────────┘  └──────────┘  └──────────┘               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Container Orchestration
```yaml
# docker compose.yml structure
services:
  nginx:        # Reverse proxy
  backend:      # API server
  frontend:     # React app
  automation:   # Browser automation
  worker:       # Background jobs
  postgres:     # Database
  redis:        # Cache/Queue
```

### Scaling Strategy
- **Horizontal**: Add more backend/worker instances
- **Vertical**: Upgrade database/cache resources
- **Auto-scaling**: Based on CPU/memory metrics
- **Load balancing**: Round-robin with health checks

## Monitoring & Observability

### Metrics Collection
- Application metrics (response time, error rate)
- Infrastructure metrics (CPU, memory, disk)
- Business metrics (applications submitted, success rate)

### Logging Strategy
- Structured JSON logging
- Centralized log aggregation
- Log retention policies
- Audit logging for security events

### Alerting
- Critical: System down, database unreachable
- Warning: High error rate, slow responses
- Info: Deployment events, configuration changes
