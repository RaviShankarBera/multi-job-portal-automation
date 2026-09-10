# Security Documentation

## Overview

This document outlines the security measures implemented in the Multi Job Portal Automation Tool to protect user data, credentials, and ensure safe operation.

## Authentication Mechanism

### JWT (JSON Web Tokens)

- **Access Token**: Short-lived (15 minutes) for API authentication
- **Refresh Token**: Long-lived (7 days) for obtaining new access tokens
- **Token Rotation**: Refresh tokens are rotated on each use
- **Secure Storage**: Tokens stored in httpOnly cookies (web) or secure storage (mobile)

### Password Security

- **Hashing**: bcrypt with salt rounds of 12
- **Password Policy**: Minimum 8 characters, requires uppercase, lowercase, number, and special character
- **Account Lockout**: 5 failed attempts triggers 15-minute lockout
- **Password History**: Last 5 passwords cannot be reused

### OAuth2 Integration

Supported providers:
- Google OAuth2
- LinkedIn OAuth2
- GitHub OAuth2 (for developer accounts)

## Authorization

### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| `user` | Own profile management, job applications, basic analytics |
| `premium` | Unlimited applications, advanced analytics, priority support |
| `admin` | Full system access, user management, system configuration |

### Resource-Level Authorization

- Users can only access their own profiles and applications
- API validates ownership before any modification
- Cross-user data access is blocked at the middleware level

```typescript
// Example authorization middleware
const authorize = (resourceOwnerId: string) => {
  return (req, res, next) => {
    if (req.user.id !== resourceOwnerId) {
      return res.status(403).json({
        success: false,
        error: { code: 'AUTH_004', message: 'Insufficient permissions' }
      });
    }
    next();
  };
};
```

## Data Protection

### Encryption at Rest

- **Database**: PostgreSQL Transparent Data Encryption (TDE)
- **File Storage**: AES-256 encryption for uploaded files
- **Backups**: Encrypted with separate key management

### Encryption in Transit

- **API Communication**: TLS 1.3 enforced
- **Internal Services**: mTLS between microservices
- **WebSocket**: WSS (WebSocket Secure) for real-time updates

### Sensitive Data Handling

| Data Type | Storage Method | Access Level |
|-----------|---------------|--------------|
| Passwords | bcrypt hash | Never plain text |
| API Keys | Environment variables | Runtime only |
| Portal Credentials | AES-256 encrypted | Service level |
| Resume Files | Encrypted storage | User + Admin |
| Session Data | Redis with TTL | User only |

### Data Classification

| Classification | Examples | Protection Level |
|---------------|----------|------------------|
| Critical | Passwords, API keys | Encryption + Access control |
| Confidential | Resume data, application history | Encryption + Audit logging |
| Internal | System logs, analytics | Access control |
| Public | Job listings, portal info | None required |

## Environment Variables

### Required Security Variables

```env
# JWT Configuration (minimum 32 characters)
JWT_SECRET=your-super-secret-jwt-key-minimum-32-characters
JWT_REFRESH_SECRET=your-refresh-secret-key-minimum-32-characters

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/db
DB_PASSWORD=strong-database-password

# Redis
REDIS_URL=redis://:password@localhost:6379

# API Keys (never commit to version control)
OPENAI_API_KEY=sk-your-openai-api-key
ENCRYPTION_KEY=aes-256-encryption-key-32-chars

# Portal Credentials (encrypted at rest)
LINKEDIN_USERNAME=your-linkedin-email
LINKEDIN_PASSWORD=your-linkedin-password
```

### Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use different secrets** for development and production
3. **Rotate secrets** every 90 days
4. **Use a secrets manager** (AWS Secrets Manager, HashiCorp Vault) in production
5. **Audit environment variables** regularly

### Environment Validation

```typescript
// src/config/env.ts
import { z } from 'zod';

const envSchema = z.object({
  JWT_SECRET: z.string().min(32),
  JWT_REFRESH_SECRET: z.string().min(32),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string(),
  OPENAI_API_KEY: z.string().startsWith('sk-'),
});

export const env = envSchema.parse(process.env);
```

## File Upload Security

### Allowed File Types

| File Type | Extensions | Max Size |
|-----------|------------|----------|
| Resume | .pdf, .docx, .doc | 5 MB |
| Profile Image | .jpg, .jpeg, .png | 2 MB |
| Cover Letter | .pdf, .docx | 3 MB |

### Security Measures

1. **File Type Validation**: MIME type and extension verification
2. **File Size Limits**: Configurable per file type
3. **Virus Scanning**: ClamAV integration for uploaded files
4. **Storage Location**: Outside web root, non-executable directory
5. **File Naming**: Randomized to prevent path traversal
6. **Access Control**: Signed URLs with expiration for downloads

### Upload Handler

```typescript
// Example secure upload configuration
const upload = multer({
  storage: multer.diskStorage({
    destination: './uploads/temp',
    filename: (req, file, cb) => {
      const uniqueName = `${uuid()}-${sanitize(file.originalname)}`;
      cb(null, uniqueName);
    }
  }),
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['application/pdf', 'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type'));
    }
  }
});
```

## API Security

### Rate Limiting

```typescript
// Rate limiting configuration
const rateLimitConfig = {
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: {
    success: false,
    error: {
      code: 'RATE_001',
      message: 'Too many requests, please try again later.'
    }
  }
};
```

### Input Validation

- **Request Body Validation**: Zod schemas for all endpoints
- **Query Parameter Sanitization**: SQL injection prevention
- **Header Validation**: CORS and content-type enforcement

```typescript
// Example input validation
const createApplicationSchema = z.object({
  jobId: z.string().uuid(),
  profileId: z.string().uuid(),
  coverLetter: z.string().max(5000).optional(),
  autoApply: z.boolean().default(false)
});
```

### SQL Injection Prevention

- **ORM Usage**: Prisma ORM parameterizes all queries
- **Input Sanitization**: All user inputs sanitized before processing
- **Query Building**: No raw SQL with user inputs

### XSS Prevention

- **Output Encoding**: All API responses properly encoded
- **Content Security Policy**: Strict CSP headers
- **HTTP Only Cookies**: Prevent XSS token theft

### CSRF Protection

- **SameSite Cookies**: Strict same-site policy
- **CSRF Tokens**: For form submissions
- **Origin Validation**: API validates request origins

### Security Headers

```typescript
// Helmet.js configuration
const helmetConfig = {
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
    }
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
};
```

## Browser Automation Security

### Credential Protection

1. **Never log credentials**: Credentials excluded from all logs
2. **Memory-only storage**: Credentials only in memory during automation
3. **Session cleanup**: Automatic browser session cleanup after completion
4. **No caching**: Disable browser caching for sensitive pages

### Anti-Detection Measures

```typescript
// Browser automation security settings
const browserConfig = {
  headless: process.env.HEADLESS_BROWSER === 'true',
  args: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-accelerated-2d-canvas',
    '--no-first-run',
    '--no-zygote',
    '--disable-gpu'
  ],
  // Randomize viewport
  viewport: {
    width: Math.floor(Math.random() * (1920 - 1280) + 1280),
    height: Math.floor(Math.random() * (1080 - 720) + 720)
  },
  // Rotate user agents
  userAgent: getRandomUserAgent()
};
```

### Ethical Automation Rules

1. **Respect robots.txt**: Always check and follow robots.txt
2. **Rate Limiting**: Minimum 30-second delay between applications
3. **Business Hours Only**: No automation during portal maintenance windows
4. **Human-like Behavior**: Random delays and mouse movements
5. **Session Limits**: Maximum 100 applications per session
6. **Portal Terms**: Only automate actions allowed by portal ToS

### Session Management

```typescript
// Secure session handling
class SecureSession {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;

  async create() {
    this.browser = await puppeteer.launch(browserConfig);
    this.context = await this.browser.createIncognitoBrowserContext();
  }

  async destroy() {
    if (this.context) {
      await this.context.close();
    }
    if (this.browser) {
      await this.browser.close();
    }
    // Clear any cached credentials
    this.clearCredentials();
  }

  private clearCredentials() {
    // Securely clear credential memory
    process.env.TEMP_CREDENTIALS = '';
    delete process.env.TEMP_CREDENTIALS;
  }
}
```

## Audit Logging

### Logged Events

| Event | Description | Log Level |
|-------|-------------|-----------|
| AUTH_SUCCESS | Successful login | INFO |
| AUTH_FAILURE | Failed login attempt | WARN |
| AUTH_LOCKOUT | Account locked | WARN |
| DATA_ACCESS | Sensitive data accessed | INFO |
| DATA_MODIFICATION | Data created/updated/deleted | INFO |
| API_ERROR | API error occurred | ERROR |
| AUTOMATION_START | Automation job started | INFO |
| AUTOMATION_COMPLETE | Automation job completed | INFO |
| SECURITY_VIOLATION | Security rule violation | CRITICAL |

### Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "event": "AUTH_SUCCESS",
  "userId": "uuid",
  "ip": "192.168.1.100",
  "userAgent": "Mozilla/5.0...",
  "resource": "/api/auth/login",
  "details": {
    "method": "POST",
    "provider": "local"
  }
}
```

### Log Security

- **No Credentials**: Never log passwords, tokens, or API keys
- **PII Masking**: Email and names masked in logs
- **Retention**: Logs retained for 90 days
- **Access Control**: Logs accessible only to admins

## Vulnerability Management

### Regular Security Tasks

| Task | Frequency | Responsible |
|------|-----------|-------------|
| Dependency audit | Weekly | Automated (npm audit) |
| Penetration testing | Quarterly | Security team |
| Code review | Every PR | Development team |
| Configuration review | Monthly | DevOps team |
| Access review | Monthly | Admin team |

### Security Updates

- **Immediate**: Critical vulnerabilities (CVSS > 9.0)
- **24 hours**: High vulnerabilities (CVSS 7.0-8.9)
- **1 week**: Medium vulnerabilities (CVSS 4.0-6.9)
- **1 month**: Low vulnerabilities (CVSS < 4.0)

## Incident Response

### Response Team

- **Security Lead**: Primary incident responder
- **Development Lead**: Technical investigation
- **DevOps Lead**: Infrastructure and deployment
- **Communication Lead**: User notifications

### Response Process

1. **Detection**: Automated alerts and user reports
2. **Triage**: Assess severity and impact
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threat and vulnerabilities
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Post-incident review and improvements

### Communication Templates

#### Security Advisory (Critical)

```
Subject: [CRITICAL] Security Incident Notification

We are currently investigating a security incident affecting [scope].
As a precaution, we recommend:

1. Changing your password immediately
2. Reviewing your account activity
3. Enabling two-factor authentication

We will provide updates as more information becomes available.
```

## Compliance

### Data Protection

- **GDPR**: Right to access, rectification, erasure
- **CCPA**: California consumer privacy rights
- **Data Retention**: User data deleted within 30 days of account deletion

### Security Certifications (Planned)

- SOC 2 Type II
- ISO 27001
- PCI DSS (for payment processing)

## Contact

For security concerns or to report vulnerabilities:

- **Email**: security@yourdomain.com
- **Bug Bounty**: [HackerOne Program](https://hackerone.com/your-org)
- **Response Time**: 24 hours for critical issues

---

**Last Updated**: January 2024
**Document Owner**: Security Team
**Review Cycle**: Quarterly
