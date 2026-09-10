# Multi Job Portal Automation Tool

An AI-powered platform that automates job applications across multiple job portals (LinkedIn, Indeed, Glassdoor, etc.) with intelligent profile management, smart form filling, and real-time analytics.

## 🚀 Features

- **Multi-Portal Automation** - Apply to jobs across LinkedIn, Indeed, Glassdoor, Naukri, and more
- **AI-Powered Profile Management** - Intelligent resume parsing and profile optimization
- **Smart Form Filling** - Automated application form completion with context-aware responses
- **Real-Time Analytics** - Track application status, response rates, and performance metrics
- **Dashboard & Reporting** - Comprehensive web dashboard for managing all applications
- **Email Integration** - Monitor and categorize job-related emails automatically
- **Resume Tailoring** - AI-generated custom resumes for each job application
- **Scheduled Applications** - Set up automated application queues with rate limiting
- **Multi-Account Support** - Manage multiple job portal accounts from one interface
- **Secure Credential Storage** - Encrypted storage for all portal credentials

## 🛠 Tech Stack

### Backend
- **Runtime**: Node.js 18+ / TypeScript
- **Framework**: Express.js
- **Database**: PostgreSQL 15 + Redis 7
- **ORM**: Prisma
- **Queue**: BullMQ (Redis)
- **Auth**: JWT + Refresh Tokens

### Frontend
- **Framework**: React 18 + TypeScript
- **UI Library**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand / TanStack Query
- **Charts**: Recharts
- **Forms**: React Hook Form + Zod

### Automation Engine
- **Browser Automation**: Puppeteer / Playwright
- **AI Integration**: OpenAI API / Anthropic Claude
- **PDF Processing**: pdf-parse
- **OCR**: Tesseract.js

### DevOps
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: Winston + ELK Stack (optional)

## 📋 Prerequisites

- Node.js 18.0 or higher
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (for containerized deployment)
- Chrome/Chromium browser (for automation engine)

## ⚡ Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/job-portal-automation.git
cd job-portal-automation

# Copy environment file
cp .env.example .env

# Start all services
docker compose up -d

# Run database migrations
docker compose exec backend npm run prisma:migrate

# Seed the database
docker compose exec backend npm run seed

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:5000/api
# Dashboard: http://localhost:5000/api/dashboard
```

### Option 2: Manual Setup

```bash
# Clone the repository
git clone https://github.com/your-org/job-portal-automation.git
cd job-portal-automation

# Install backend dependencies
cd backend
npm install

# Install frontend dependencies
cd ../frontend
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Setup database
cd ../backend
npx prisma migrate dev
npx prisma db seed

# Start backend server
npm run dev

# Start frontend (in new terminal)
cd ../frontend
npm run dev
```

## 🔐 Environment Variables

### Required Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/job_portal
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
JWT_REFRESH_SECRET=your-refresh-secret-key-min-32-chars
JWT_EXPIRATION=15m
JWT_REFRESH_EXPIRATION=7d

# AI Integration
OPENAI_API_KEY=sk-your-openai-api-key
AI_MODEL=gpt-4

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# Application Settings
APP_URL=http://localhost:3000
API_URL=http://localhost:5000
NODE_ENV=development
```

### Optional Variables

```env
# Browser Automation
HEADLESS_BROWSER=true
CHROME_PATH=/usr/bin/chromium

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=5242880

# Rate Limiting
RATE_LIMIT_WINDOW=15
RATE_LIMIT_MAX=100

# Logging
LOG_LEVEL=info
LOG_DIR=./logs
```

## 📡 API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/profiles` | Get user profiles |
| POST | `/api/profiles` | Create new profile |
| PUT | `/api/profiles/:id` | Update profile |
| POST | `/api/profiles/upload-resume` | Upload resume |
| GET | `/api/applications` | List all applications |
| POST | `/api/applications` | Create application |
| PUT | `/api/applications/:id` | Update application status |
| GET | `/api/jobs/search` | Search job listings |
| POST | `/api/jobs/track` | Track a job |
| GET | `/api/analytics/dashboard` | Get dashboard analytics |
| GET | `/api/analytics/reports` | Generate reports |
| POST | `/api/automation/start` | Start automation |
| POST | `/api/automation/stop` | Stop automation |
| GET | `/api/automation/status` | Get automation status |

For detailed API documentation, see [API.md](./API.md)

## 📁 Project Structure

```
job-portal-automation/
├── backend/
│   ├── src/
│   │   ├── config/          # Configuration files
│   │   ├── controllers/     # Request handlers
│   │   ├── middleware/       # Custom middleware
│   │   ├── models/          # Database models (Prisma)
│   │   ├── routes/          # API routes
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Utility functions
│   │   └── index.ts         # Entry point
│   ├── prisma/
│   │   └── schema.prisma    # Database schema
│   ├── uploads/             # File uploads
│   └── tests/               # Test files
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API services
│   │   ├── store/           # State management
│   │   └── utils/           # Utility functions
│   └── public/              # Static assets
├── automation/
│   ├── engine/              # Browser automation core
│   ├── portals/             # Portal-specific adapters
│   └── ai/                  # AI integration
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── docs/                    # Documentation
├── .github/                 # GitHub Actions
├── docker compose.yml
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow TypeScript strict mode
- Write tests for new features
- Update documentation as needed
- Follow conventional commits format
- Ensure all CI checks pass

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/job-portal-automation/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/job-portal-automation/discussions)

## ⚠️ Disclaimer

This tool is for educational and personal use only. Always respect the Terms of Service of job portals. Use automation responsibly and ethically. The developers are not responsible for any misuse of this software.
