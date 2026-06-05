# TFI Command Center 2.0

AI-powered internship operations, analytics, and student success intelligence platform for Techno Future India.

## Overview

TFI Command Center 2.0 is an enterprise-style platform for managing internship programs end to end. It centralizes attendance imports, assignment tracking, role-based dashboards, reports, AI insights, student risk detection, mentor workflows, notification nudges, and authenticity checks.

The platform is designed for four operating roles:

- **Director**: executive analytics, forecasts, risk heatmaps, reports, and program health.
- **Host**: attendance imports, live operations, session quality, late joiners, and early leavers.
- **Mentor**: coaching queue, assignment review, risk students, nudges, AI assistant, and authenticity checks.
- **Admin**: platform governance, users, RBAC, system health, audit, and AI operations.

## Current Verification Status

Latest local verification:

```text
Backend tests: 29 passed
Frontend lint: passed
Frontend production build: passed
```

Live OpenAI/Gemini, WhatsApp, Email, and GitHub checks require provider credentials in environment variables.

## Key Features

### Core Operations

- Role-based dashboards for Director, Host, Mentor, and Admin.
- Attendance import from CSV/XLS/XLSX.
- Zoom/Meet-style attendance column normalization.
- Student, batch, attendance, assignment, submission, risk, certificate, notification, report, audit, and AI history data models.
- Certificate eligibility forecasting.
- Operational reports and audit trails.

### AI Intelligence Layer

- Attendance drop prediction.
- 7-day and 30-day attendance forecast.
- Performance forecasting.
- Certificate eligibility probability.
- Risk detection with reasoning.
- Executive AI insights and reports.
- Mentor AI assistant backed by real platform data.
- Assignment evaluation.
- Project plagiarism and authenticity check.
- Trainable Scikit-Learn models.
- Model retraining endpoint and UI control.
- Live OpenAI/Gemini provider mode with local fallback.

### Notifications and Nudges

- Auto-detect missed attendance.
- Auto-detect overdue missing assignments.
- Generate personalized student reminders.
- Escalate critical cases to mentor/parent contacts when available.
- Queue or send Email/WhatsApp nudges.
- Prevent duplicate nudges.
- Track response status.

### Authenticity and Plagiarism

- Similarity check against prior submissions using hashed fingerprints.
- AI-generated content risk scoring.
- Code-quality evidence score.
- GitHub repository activity check.
- Originality score.
- Mentor findings and review recommendations.
- Persistent authenticity audit records.

### Reporting

- AI report generation.
- Markdown export.
- HTML export.
- PDF export with ReportLab.
- Report history persistence.

## Tech Stack

| Area | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript |
| Styling | Tailwind CSS |
| Charts | Recharts |
| State | Zustand |
| Backend | FastAPI |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Database | PostgreSQL in production, SQLite for local/test |
| Auth | JWT, Firebase-ready session support |
| ML/Data | Pandas, NumPy, Scikit-Learn |
| Reports | ReportLab, HTML, Markdown |
| Notifications | Resend Email, WhatsApp Cloud API |
| AI Providers | OpenAI, Google Gemini, local fallback |

## Repository Structure

```text
.
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── ai/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── store/
│   ├── styles/
│   ├── types/
│   └── package.json
├── docs/
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- Yarn 1.x
- Docker Desktop, if using local PostgreSQL
- Optional provider accounts:
  - OpenAI or Google Gemini
  - Resend
  - WhatsApp Cloud API
  - GitHub token

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

For PowerShell, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Frontend Setup

```bash
cd frontend
yarn install
yarn dev
```

Default frontend URL:

```text
http://localhost:3000
```

Default backend URL:

```text
http://127.0.0.1:8000/api/v1
```

## Local Demo Users

When `ENVIRONMENT=local`, the backend seeds local demo users.

| Role | Email | Password |
|---|---|---|
| Director | `director@techofutureindia.com` | `TfiDemo@2026!` |
| Host | `host@techofutureindia.com` | `TfiDemo@2026!` |
| Mentor | `mentor@techofutureindia.com` | `TfiDemo@2026!` |
| Admin | `admin-demo@techofutureindia.com` | `TfiDemo@2026!` |

## Environment Variables

### Backend

Create `backend/.env`:

```env
ENVIRONMENT=local
DATABASE_URL=sqlite:///./tfi_local.db
SECRET_KEY=change-me-before-production
FRONTEND_ORIGINS=http://localhost:3000
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,backend

INITIAL_ADMIN_EMAIL=
INITIAL_ADMIN_PASSWORD=
INITIAL_ADMIN_NAME=TFI Administrator
INITIAL_ADMIN_ROLE=Admin

AI_LIVE_ENABLED=false
AI_PROVIDER=local
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.5
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-pro

NOTIFICATION_AUTO_SEND=false
RESEND_API_KEY=
RESEND_FROM_EMAIL=
WHATSAPP_API_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=

GITHUB_API_TOKEN=
```

### Frontend

Create `frontend/.env`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1

NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_firebase_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_firebase_messaging_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_firebase_app_id
```

## Database Migrations

Run migrations after pulling new backend changes:

```bash
cd backend
alembic upgrade head
```

Create a new migration manually only when schema changes are added:

```bash
alembic revision -m "description"
```

## API Overview

Base URL:

```text
/api/v1
```

Important route groups:

```text
/auth
/dashboard
/attendance
/reports
/intelligence
/notifications
```

AI routes:

```text
GET  /intelligence/ai/overview
GET  /intelligence/ai/attendance-prediction
GET  /intelligence/ai/performance-forecast
GET  /intelligence/ai/risk-analysis
GET  /intelligence/ai/executive-report
GET  /intelligence/ai/model-status
POST /intelligence/ai/model-retraining
POST /intelligence/ai/mentor-chat
POST /intelligence/ai/report-generation
POST /intelligence/ai/assignment-evaluation
POST /intelligence/ai/authenticity-check
```

Notification routes:

```text
GET  /notifications
POST /notifications/nudges/run
POST /notifications/{notification_id}/response
```

## Testing

Backend:

```bash
cd backend
pytest
```

Frontend lint:

```bash
cd frontend
yarn lint
```

Frontend production build:

```bash
cd frontend
yarn build
```

## Deployment Notes

### Frontend

Recommended target:

- Vercel

Required frontend environment:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend-domain/api/v1
```

### Backend

Recommended targets:

- Render
- Railway
- Fly.io
- AWS/GCP/Azure container runtime

Production requirements:

- PostgreSQL database
- Strong `SECRET_KEY`
- `ENVIRONMENT=production`
- `alembic upgrade head`
- Proper `ALLOWED_HOSTS`
- Proper `FRONTEND_ORIGINS`
- Provider credentials if live integrations are needed

## Production Checklist

- [ ] Use PostgreSQL, not SQLite.
- [ ] Run `alembic upgrade head`.
- [ ] Set a strong production `SECRET_KEY`.
- [ ] Configure `ALLOWED_HOSTS`.
- [ ] Configure `FRONTEND_ORIGINS`.
- [ ] Configure initial admin or provision users through the database.
- [ ] Add OpenAI/Gemini keys if live AI is required.
- [ ] Add Resend/WhatsApp credentials if live nudges are required.
- [ ] Add GitHub token for higher-rate GitHub activity checks.
- [ ] Move report/model artifacts to durable object storage for cloud production.
- [ ] Add monitoring and error tracking.
- [ ] Add end-to-end browser tests before large-scale rollout.

## Operational Modes

### Safe Local Mode

Default behavior:

- Local deterministic AI.
- Notifications queued, not sent.
- GitHub checks run without token when possible.
- Demo users seeded in local environment.

### Live Enterprise Mode

Enable with:

```env
AI_LIVE_ENABLED=true
AI_PROVIDER=openai
OPENAI_API_KEY=your_key
NOTIFICATION_AUTO_SEND=true
RESEND_API_KEY=your_key
WHATSAPP_API_TOKEN=your_key
```

## Known Production Gaps

The project is locally verified, but a full production rollout should still include:

- End-to-end Playwright tests.
- Formal backend coverage reporting with `pytest-cov`.
- Background worker for heavy report generation, notification sending, and model retraining.
- Durable storage for generated report/model artifacts.
- Real APM/monitoring.
- Large-cohort load testing.
- Admin user-management UI.

## Security

Implemented:

- JWT authentication.
- Firebase-ready session endpoint.
- Role-based access control.
- Password hashing with PBKDF2-SHA256.
- Login rate limiting.
- Trusted host middleware.
- Security headers.
- Environment-based secret configuration.
- Audit logs for operational actions.

## License

This project is licensed under the MIT License.

## Maintainer

Developed for Techno Future India.
