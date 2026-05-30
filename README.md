# AI-Powered Job Recommender System

An intelligent full-stack job recommendation platform that matches job seekers with relevant jobs using **hybrid search combining semantic vector embeddings and BM25 keyword ranking**, fused via Reciprocal Rank Fusion (RRF).

---

## Project Status

Under active development.

---

## Key Features

### Recruiter

- JWT-based authentication with refresh token rotation (HttpOnly cookie)
- Post job listings — AI extracts skills and job summary, generates two embeddings
- View and delete posted jobs from a dedicated dashboard
- Email notification when a candidate applies

### Job Seeker

- Register, login, and reset password via tokenized email link
- Build a profile with preferred domain, experience level, and locations
- Upload a profile image (JPG/JPEG/PNG, max 5 MB)
- Upload a resume (PDF, max 5 MB) — LLM extracts skills, work experience, and projects; three separate embeddings are stored
- AI-powered job recommendations with a match score (0–100)
- Two recommendation modes:
  - **Profile Mode** — uses saved profile filters and stored resume embeddings
  - **Manual Mode** — custom filters with optional one-shot resume upload (not saved)
- Paginated job listings with a "Load More" button
- Save and unsave jobs
- Apply to jobs via a pre-filled application modal
- View saved and applied jobs in dedicated tabs
- View company details for any job posting
- Email confirmation sent on successful application

---

## AI & Matching Architecture

### Embedding Strategy

| Resume Vector | Job Vector | Weight |
|---|---|---|
| `skill_embedding` | `skill_embedding` | 50% |
| `work_embedding` | `job_embedding` | 30% |
| `project_embedding` | `job_embedding` | 20% |

Weights adjust dynamically when embeddings are absent:

| Available Vectors | Weights (skill / work / project) |
|---|---|
| All three | 0.50 / 0.30 / 0.20 |
| Skills + work only | 0.60 / 0.40 / — |
| Skills + project only | 0.65 / — / 0.35 |
| Skills only | 1.00 / — / — |

### Hybrid Ranking Pipeline

```
Resume PDF
  └─► Text extraction (PyMuPDF)
  └─► PII removal (email, phone, URLs, LinkedIn/GitHub)
  └─► LLM extraction (LLaMA 3.1 8B via Groq)
        ├─ skills          → skill_embedding   (768-dim)
        ├─ work summary    → work_embedding    (768-dim, nullable)
        └─ project summary → project_embedding (768-dim, nullable)

Job Description
  └─► LLM extraction (LLaMA 3.1 8B via Groq)
        ├─ skills      → skill_embedding  (768-dim)
        └─ job summary → job_embedding    (768-dim)

Embeddings: Google Gemini API — gemini-embedding-001
  └─► MRL-truncated to 768 dimensions
  └─► task_type: retrieval_document for all stored embeddings

Hybrid Ranking:
  ┌─ Semantic (pgvector weighted cosine similarity)
  └─ BM25 (rank_bm25 on pre-tokenised job descriptions)
  ↓ Weighted RRF (60% semantic, 40% BM25) → match score 0–100

Fallback chain:
  hybrid → bm25_only (if embeddings fail) → newest-first (no resume)
```

### LLM Extraction Details

**Resume → extracts:**
- Skills (normalized, natural-language summary)
- Work experience (employment only, one sentence per role, anonymized)
- Projects (personal/academic only, one sentence each, anonymized)

**Job Description → extracts:**
- Job role
- Skills (normalized, space-separated string)
- Job summary (responsibilities + domain context, 3–5 sentences)

---

## Email Services

| Trigger | Recipient | Content |
|---|---|---|
| Password reset | Job seeker | Tokenized reset link (15-minute expiry) |
| Job application | Job seeker | Confirmation card with job title and company |
| Job application | Recruiter | Full applicant details including resume link, LinkedIn, and cover note |

All emails use HTML Jinja2 templates rendered server-side and sent via SMTP with TLS.

---

## Authentication & Security

- **Access token** — short-lived JWT (60 min default), stored in memory only on the client
- **Refresh token** — opaque random token stored hashed (SHA-256) in the database, sent via HttpOnly cookie
- **Refresh rotation** — every `/auth/refresh` call revokes the old token and issues a new one
- **Rate limiting** via SlowAPI: signup/login at 2/minute, job posting at 2/minute, resume upload at 2/minute, recommendations at 5/minute
- **Password reset** — JWT-signed token + DB record (hash stored); used tokens are marked and all active refresh tokens are revoked on reset
- **Path traversal guards** on all file serving routes (resume, profile image)
- Role-based guards: `get_current_recruiter` and `get_current_jobseeker` dependency functions

---

## Tech Stack

### Backend

| Component | Technology |
|---|---|
| API framework | FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL + pgvector |
| Embeddings | Gemini API (`gemini-embedding-001`, 768-dim via LangChain) |
| LLM | Groq API + LLaMA 3.1 8B Instant via LangChain |
| Keyword ranking | rank_bm25 (BM25Okapi, k1=1.5, b=0.75) |
| PDF extraction | PyMuPDF (via LangChain PyMuPDFLoader) |
| Auth | python-jose (JWT), passlib/bcrypt |
| Email | aiosmtplib + Jinja2 HTML templates |
| Rate limiting | SlowAPI |
| Validation | Pydantic v2 |

### Frontend

| Component | Technology |
|---|---|
| Framework | React (Create React App) |
| Routing | React Router v6 |
| HTTP client | Axios with request/response interceptors |
| Multi-select | react-select |
| Icons | react-icons (Material Design, Font Awesome) |
| Styling | Custom CSS with design tokens (CSS variables) |
| Auth storage | In-memory token store (not localStorage) |

---

## Project Structure

```
AI-powered-job-recommender-system/
│
├── backend/
│   ├── app/
│   │   ├── applications/       # Save, unsave, apply, company details routes
│   │   ├── auth/               # Login, signup, refresh, logout routes
│   │   │   └── passwords/      # Forgot/reset password routes & utils
│   │   ├── jobs/               # Job post/delete/list routes + embedding utils
│   │   ├── notifications/      # Prefill + notify routes for job applications
│   │   ├── profile/            # Personal info, preferences, company, image routes
│   │   ├── recommendations/    # Hybrid recommendation engine (profile & manual)
│   │   ├── resume/             # Resume upload, delete, view, status routes
│   │   ├── services/
│   │   │   └── email_services.py   # SMTP send functions for all email types
│   │   ├── templates/          # Jinja2 HTML email templates
│   │   │   ├── reset_email.html
│   │   │   ├── recruiter_application.html
│   │   │   └── jobseeker_confirmation.html
│   │   ├── config.py           # Pydantic settings (reads .env)
│   │   ├── database.py         # SQLAlchemy engine + session
│   │   ├── exceptions.py       # LLMError, EmbeddingError, PDFExtractionError
│   │   ├── limiter.py          # SlowAPI limiter instance
│   │   ├── main.py             # FastAPI app, middleware, router registration
│   │   ├── modelregistry.py    # Singleton LLM + embedding model, safe_encode
│   │   ├── models.py           # All SQLAlchemy models
│   │   ├── schemas.py          # Shared Pydantic schemas (JobItem, etc.)
│   │   └── utils.py            # Password hashing, JWT helpers, role guards, tokenizer
│   ├── uploads/
│   │   ├── resumes/            # Stored resume PDFs (named by user_id)
│   │   └── images/             # Stored profile images (named by user_id)
│   ├── .env
│   └── requirements.txt
│
└── frontend/
    └── job_portal/
        └── src/
            ├── api/
            │   ├── axios.js        # Axios instance + silent refresh interceptor
            │   └── tokenStore.js   # In-memory access token + role store
            ├── components/
            │   ├── auth/
            │   │   ├── Login.jsx / SignUp.jsx / Logout.jsx
            │   │   ├── ForgotPassword.jsx / ResetPassword.jsx
            │   │   └── Auth.css / ForgotPassword.css / ResetPassword.css
            │   ├── ApplyModal.jsx / ApplyModal.css
            │   ├── CompanyCard.jsx / CompanyCard.css
            │   ├── ErrorBanner.jsx
            │   ├── ErrorBoundary.jsx
            │   ├── JobPostCard.jsx / JobPostCard.css
            │   ├── jobCard.jsx / jobCard.css
            │   └── loader.jsx / Loader.css
            ├── pages/
            │   ├── HomePage.jsx / HomePage.css
            │   ├── JobListPage.jsx / JobListPage.css
            │   ├── ProfilePage.jsx / ProfilePage.css
            │   └── RecruiterDashBoard.jsx / RecruiterDashBoard.css
            ├── utils/
            │   └── errorUtils.js   # Axios error message extractor
            ├── App.js              # Routes, silent refresh on load, role guards
            ├── index.js            # React root with ErrorBoundary
            ├── tokens.css          # Global CSS design tokens
            └── index.css
```

---

## Database Models

| Model | Key Columns |
|---|---|
| `User` | `user_id`, `fullname`, `email`, `password_hash`, `user_role`, `phone`, `profile_image_path` |
| `Resume` | `user_id`, `resume_url`, `resume_text`, `skill_embedding`, `work_embedding`, `project_embedding` |
| `Job` | `job_id`, `job_title`, `company_name`, `industry_domain_id`, `job_level`, `min/max_experience`, `skill_embedding`, `job_embedding`, `bm25_tokens` |
| `JobSeekerProfile` | `user_id`, `experience`, `seniority_level`, `preferred_domain_id` |
| `RecruiterProfile` | `user_id`, `company_name`, `website`, `linkedin`, `description` |
| `Application` | `job_seeker_id`, `job_id`, `applied_at` |
| `SavedJob` | `job_seeker_id`, `job_id`, `saved_at` |
| `RefreshToken` | `user_id`, `token_hash`, `is_revoked`, `expires_at`, `user_agent`, `ip_address` |
| `PasswordResetToken` | `user_id`, `token_hash`, `used`, `expires_at` |
| `JobSeekerPreferredLocation` | `user_id`, `location_id` |

Seniority levels are derived from experience: `entry` (0–1 yr), `mid` (2–4 yr), `senior` (5–8 yr), `lead` (9+ yr). These are stored on both `JobSeekerProfile` and `Job` and used as a hard filter during recommendation.

---

## API Reference

### Auth — `/auth`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register (2/min rate limit) |
| POST | `/auth/login` | Login, returns access token + sets refresh cookie (2/min) |
| POST | `/auth/refresh` | Silent token refresh using HttpOnly cookie |
| POST | `/auth/logout` | Revoke refresh token and clear cookie |

### Password Reset — `/auth/passwords`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/passwords/forgot-password` | Send reset email (2/min) |
| POST | `/auth/passwords/reset-password` | Reset password via token, revokes all sessions (2/min) |

### Jobs — `/jobs`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/jobs/locations` | List all locations |
| GET | `/jobs/industry-domains` | List all industry domains |
| POST | `/jobs/post` | Create job with AI embeddings (recruiter, 2/min) |
| GET | `/jobs/postedjobs` | List recruiter's own jobs |
| DELETE | `/jobs/{job_id}` | Delete a job |
| GET | `/jobs/all` | Paginated job list for job seekers (`skip`, `limit`) |

### Applications — `/applications`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/applications/jobs/{job_id}/save` | Save a job |
| DELETE | `/applications/jobs/{job_id}/unsave` | Unsave a job |
| POST | `/applications/jobs/{job_id}/apply` | Apply to a job (409 if already applied) |
| GET | `/applications/saved-jobs/ids` | IDs of saved jobs (for button state) |
| GET | `/applications/applied-jobs/ids` | IDs of applied jobs (for button state) |
| GET | `/applications/saved-jobs/details` | Full saved job details |
| GET | `/applications/applied-jobs/details` | Full applied job details |
| GET | `/applications/jobs/{job_id}/company-details` | Recruiter company profile for a job |

### Notifications — `/notifications/jobs`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/notifications/jobs/{job_id}/apply/prefill` | Pre-fill apply form from DB |
| POST | `/notifications/jobs/{job_id}/apply/notify` | Send application emails (background tasks) |

### Recommendations — `/recommendations`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/recommendations/jobs` | Get ranked jobs (5/min) |

Query params: `use_profile` (bool), `domain_id`, `location_ids[]`, `experience`, `limit` (1–100, default 10).
Form field: `resume_file` (optional PDF, used only in manual mode).

Response includes `ranking_mode`: `hybrid`, `bm25_only`, or `fallback`.

### Profile — `/profile`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/profile/details` | Full profile including role-specific info |
| PATCH | `/profile/personal` | Update name and phone (E.164 format validated) |
| PATCH | `/profile/preferences` | Update job seeker domain, experience, locations |
| PATCH | `/profile/company` | Update recruiter company info (URL validated) |
| PATCH | `/profile/change-password` | Change password (current password required) |
| POST | `/profile/upload-image` | Upload profile image for first time |
| PUT | `/profile/update-image` | Replace existing profile image |
| GET | `/profile/view-image` | Serve profile image inline |
| DELETE | `/profile/delete-image` | Delete profile image |

### Resume — `/resume`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/resume/upload` | Upload/replace resume, triggers LLM + embeddings (2/min) |
| DELETE | `/resume/delete` | Delete resume file and DB record |
| GET | `/resume/status` | Check whether a resume exists |
| GET | `/resume/view` | Serve resume PDF inline |

---

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 14+
- PostgreSQL with pgvector extension

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Backend Setup

```bash
git clone https://github.com/Hardinaik/AI-powered-job-recommender-system.git
cd AI-powered-job-recommender-system/backend

python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```

Create `.env` in the `backend/` directory:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/jobdb
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
RESET_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
IS_PRODUCTION=false

GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FRONTEND_URL=http://localhost:3000
```

```bash
uvicorn app.main:app --reload
```

API runs at `http://127.0.0.1:8000` — Swagger docs at `/docs`.

### Frontend Setup

```bash
cd ../frontend/job_portal
npm install
```

Create `.env` in `frontend/job_portal/`:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

```bash
npm start
```

Frontend runs at `http://localhost:3000`.

---

## Example Workflow

**Recruiter:**
1. Signs up and logs in
2. Posts a job — LLM extracts skills and a job summary, two embeddings stored
3. Receives an email when a candidate applies

**Job Seeker:**
1. Signs up and logs in (can reset forgotten password via email)
2. Fills out profile: domain, experience, preferred locations
3. Uploads resume → LLM extracts skills, work history, projects → three embeddings stored
4. Job Listings page:
   - **Profile mode**: checks "Recommend using profile" → backend pulls saved filters and stored embeddings
   - **Manual mode**: selects filters manually, optionally uploads a one-shot resume
5. Jobs are ranked and returned with a match score; fallback to BM25 or newest-first if AI is unavailable
6. Clicks "Apply Now" → pre-filled modal with name, email, phone, experience, resume URL → confirmation email sent to job seeker, notification email sent to recruiter

---

## Frontend Details

### Silent Refresh
On app load, `App.js` attempts a silent `/auth/refresh` using the HttpOnly cookie. If successful, the access token and role are restored in memory and the user is returned to their last page. The Axios interceptor handles 401 responses mid-session by queuing pending requests and retrying after a successful refresh.

### Recommendation UI
The `JobListPage` shows a ranking mode banner when AI matching degrades:
- `bm25_only` → amber warning banner ("showing keyword-based recommendations")
- `fallback` → red error banner ("showing latest jobs")

The frontend only shows these banners when the user actually intended to use resume-based matching (`use_profile` or a file was selected).

### Apply Modal Flow
1. Opens → immediately fetches `/prefill` to populate name, email, phone, experience, resume URL from DB
2. User can edit any field before submitting
3. On submit: calls `/applications/.../apply` first (tolerates 409 if already applied), then calls `/notifications/.../notify` to send both emails
4. Application is considered successful even if email delivery fails

---

## Password Policy

Passwords must be at least 8 characters and include at least one uppercase letter, one lowercase letter, one digit, and one special character (`@$!%*?&`). This is validated on signup, password change, and password reset.

---

## Future Improvements

- Admin dashboard
- Real-time application status tracking
- Resume versioning
- Cloud deployment (AWS / GCP / Render + Vercel)
- Pagination for saved/applied jobs
- Job expiry and archival

---

## Author

**Hardi Naik**  
DA-IICT Gandhinagar  
GitHub: [https://github.com/Hardinaik](https://github.com/Hardinaik)