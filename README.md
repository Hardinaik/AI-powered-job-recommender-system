# 🚀 AI-Powered Job Recommender System

An intelligent full-stack Job Recommendation Platform that matches job seekers with relevant jobs using **AI-powered hybrid search combining semantic vector embeddings and BM25 keyword ranking**.

Instead of simple keyword matching, this system parses resumes with an LLM, extracts structured skill and experience data, generates multiple embeddings, and ranks jobs using a hybrid Reciprocal Rank Fusion (RRF) pipeline via pgvector.

---

## 🚧 Project Status

This project is currently under active development.

---

## 🔥 Key Features

### 👨‍💼 Recruiter Dashboard
- Secure JWT-based authentication
- Post new job listings with AI-generated embeddings
- View and delete posted jobs
- Job descriptions parsed into skill + summary embeddings via LLM
- **Email notification** when a job seeker applies to a posted job

### 👩‍💻 Job Seeker Dashboard
- Register & login with **password reset via email** (tokenized reset link)
- Build a profile with preferred domain, experience, and locations
- Upload resume (PDF, max 5 MB)
- Resume parsed by LLM → skills, work experience, and projects extracted separately
- Three resume embeddings generated and stored
- AI-based job recommendations with match score (0–100)
- Two recommendation modes:
  - **Profile Mode** — uses saved profile filters + stored resume embeddings
  - **Manual Mode** — custom filters with optional one-shot resume upload (not saved to DB)
- Filter jobs by Industry Domain, Experience, and multiple Locations
- **Email confirmation** sent on successful job application

---

## 🧠 AI & Smart Matching

### Hybrid Search Architecture

This system combines **semantic vector search** and **BM25 keyword ranking**, fused via **Reciprocal Rank Fusion (RRF)** for more robust, balanced recommendations.

#### Embedding Weights (Semantic Component)

| Resume Vector | Job Vector | Weight |
|---|---|---|
| `skill_embedding` | `skill_embedding` | 50% |
| `work_embedding` | `job_embedding` | 30% |
| `project_embedding` | `job_embedding` | 20% |

> Weights adjust dynamically when certain embeddings are unavailable (e.g., no work history or projects).

- Resume is split into **three separate embeddings**: skills, work experience summary, and projects summary
- Job descriptions are split into **two embeddings**: skills and a combined responsibility + domain summary
- Weighted cosine similarity is computed in PostgreSQL using pgvector
- BM25 keyword ranking (via `rank_bm25`) runs in parallel against job descriptions
- Both rankings are fused using **weighted RRF** (60% semantic, 40% BM25), rescaled to a match score of 0–100

### LLM Extraction (Groq API — LLaMA 3 8B Instant)

**Resume → extracts:**
- Skills (normalized, space-separated)
- Education
- Work experience summary (employment only, anonymized)
- Projects summary (personal/academic only, anonymized)

**Job Description → extracts:**
- Job role
- Skills (normalized, space-separated)
- Education requirement
- Job summary (responsibilities + domain context combined)

---

## 📧 Email Services

| Trigger | Recipients | Details |
|---|---|---|
| Password Reset | Job Seeker | Tokenized reset link sent to registered email |
| Job Application | Job Seeker | Confirmation email on successful application |
| Job Application | Recruiter | Notification email when a candidate applies |

---

## 🛠 Tech Stack

### Backend
- **FastAPI** — REST API framework
- **SQLAlchemy ORM** — database models
- **PostgreSQL + pgvector** — vector similarity search
- **Sentence Transformers** — `all-MiniLM-L6-v2` (384-dim embeddings)
- **Groq API + LLaMA 3 8B Instant** — LLM-based structured extraction
- **LangChain** — LLM orchestration
- **rank_bm25** — BM25 keyword ranking
- **PyMuPDF** — PDF text extraction
- **JWT Authentication** — role-based access control
- **Email (SMTP)** — password reset and application notifications

### Frontend
- **React.js** with React Router
- **Axios** — API communication
- **react-select** — multi-select location filter
- Custom CSS — role-based dashboards

---

## 📁 Project Structure

```
AI-powered-job-recommender-system/
│
├── backend/
│   ├── app/
│   │   ├── applications/      # Save/apply routes + email notifications
│   │   ├── auth/              # Login, signup & password reset routes
│   │   ├── jobs/              # Job posting routes + job embedding utils
│   │   ├── notifications/     # Email notification logic (password reset, apply alerts)
│   │   ├── profile/           # Job seeker profile routes
│   │   ├── recommendations/   # Hybrid recommendation route (profile & manual modes)
│   │   ├── resume/            # Resume upload routes + resume embedding utils
│   │   ├── services/          # Shared service utilities
│   │   ├── templates/         # Email HTML templates
│   │   ├── config.py          # App configuration & settings
│   │   ├── database.py        # DB connection
│   │   ├── main.py            # App entry point
│   │   ├── modelregistry.py   # Model/embedding registry
│   │   ├── models.py          # SQLAlchemy models (User, Job, Resume, etc.)
│   │   └── utils.py           # Auth helpers
│   ├── uploads/               # Temporary resume upload storage
│   ├── .env                   # Environment variables
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/        # JobCard, Loader, Logout, etc.
│   │   ├── pages/             # JobListPage, ProfilePage, etc.
│   │   ├── api/               # Axios instance
│   │   └── styles/
│   └── package.json
│
└── README.md
```

---

## ⚙️ Setup Instructions

### 🧩 Prerequisites

- Python 3.9+
- Node.js 14+
- PostgreSQL installed and running
- pgvector extension enabled

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 🔧 Backend Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Hardinaik/AI-powered-job-recommender-system.git
cd AI-powered-job-recommender-system/backend
```

### 2️⃣ Create & Activate Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a `.env` file inside the `backend/` folder:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/jobdb
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
GROQ_API_KEY=your_groq_api_key_here

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FRONTEND_URL=http://localhost:3000
```

### 5️⃣ Run Server

```bash
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger Docs: `http://127.0.0.1:8000/docs`

---

## 💻 Frontend Setup

```bash
cd ../frontend
npm install
npm start
```

Frontend runs on `http://localhost:3000`

---

## 🔐 Authentication

- JWT-based authentication
- Role-based access control: **Recruiter** / **Job Seeker**
- Token stored in localStorage
- Protected API routes
- Password reset via secure tokenized email link

---

## 📌 API Endpoints

### 🔑 Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register a new user |
| POST | `/auth/login` | Login and receive JWT |
| POST | `/auth/forgot-password` | Send password reset email |
| POST | `/auth/reset-password` | Reset password via token |

### 💼 Jobs
| Method | Endpoint |
|---|---|
| POST | `/jobs/post` |
| GET | `/jobs/postedjobs` |
| DELETE | `/jobs/{job_id}` |
| GET | `/jobs/locations` |
| GET | `/jobs/industry-domains` |

### 👤 Profile
| Method | Endpoint | Description |
|---|---|---|
| GET | `/profile/details` | Get full profile (personal + role-specific info) |
| PATCH | `/profile/personal` | Update name and phone number |
| PATCH | `/profile/preferences` | Update job seeker preferences (domain, experience, locations) |
| PATCH | `/profile/company` | Update recruiter company details |
| PATCH | `/profile/change-password` | Change password (requires current password) |
| POST | `/profile/upload-image` | Upload profile image (first time) |
| PUT | `/profile/update-image` | Replace existing profile image |
| GET | `/profile/view-image` | View profile image |
| DELETE | `/profile/delete-image` | Delete profile image |

### 📄 Resume
| Method | Endpoint | Description |
|---|---|---|
| POST | `/resume/upload` | Upload or replace resume PDF (triggers LLM embedding) |
| DELETE | `/resume/delete` | Delete stored resume and embeddings |
| GET | `/resume/status` | Check if a resume is uploaded |
| GET | `/resume/view` | View/download stored resume PDF |

### 🤖 Recommendations
| Method | Endpoint | Notes |
|---|---|---|
| POST | `/recommendations/jobs` | `use_profile=true` for profile mode, `false` for manual |

**Manual mode query params:** `domain_id`, `location_ids` (repeatable), `experience`  
**Manual mode form fields:** `use_profile`, `resume_file` (optional, not saved to DB)

### 📋 Applications
| Method | Endpoint |
|---|---|
| POST | `/applications/jobs/{job_id}/save` |
| POST | `/applications/jobs/{job_id}/apply` |
| GET | `/applications/saved-jobs/ids` |
| GET | `/applications/applied-jobs/ids` |
| GET | `/applications/saved-jobs/details` |
| GET | `/applications/applied-jobs/details` |

---

## 🧪 Example Workflow

**Recruiter:**
1. Recruiter signs up and logs in
2. Posts a job description
3. LLM (LLaMA 3 via Groq) extracts skills + job summary → two embeddings stored in DB
4. Receives an email notification when a candidate applies

**Job Seeker:**
1. Job seeker signs up and logs in (can reset password via email if forgotten)
2. Fills out profile (domain, experience, preferred locations)
3. Uploads resume → LLM extracts skills, work history, projects → three embeddings stored
4. Opens job listings page:
   - **Profile mode**: checks "Recommend using profile" → backend uses saved profile filters + stored embeddings
   - **Manual mode**: selects domain, locations (multi-select), experience, and optionally uploads a resume for one-shot scoring
5. Jobs ranked by hybrid search (semantic + BM25 via RRF) and returned with a match score
6. Clicks "Apply Now" → confirmation email sent to job seeker, notification email sent to recruiter

---

## 🧬 How Recommendation Works

```
Resume PDF
  └─► Text Extraction (PyMuPDF)
  └─► PII Removal
  └─► LLM Extraction (LLaMA 3 8B via Groq)
        ├─ skills          → skill_embedding   (384-dim)
        ├─ work summary    → work_embedding    (384-dim)
        └─ project summary → project_embedding (384-dim)

Job Description
  └─► LLM Extraction (LLaMA 3 8B via Groq)
        ├─ skills      → skill_embedding  (384-dim)
        └─ job summary → job_embedding    (384-dim)

Hybrid Ranking:
  ┌─ Semantic (pgvector weighted cosine similarity)
  │     50% × cosine(resume.skill_embedding,   job.skill_embedding)
  │     30% × cosine(resume.work_embedding,    job.job_embedding)
  │     20% × cosine(resume.project_embedding, job.job_embedding)
  │
  └─ BM25 (rank_bm25 keyword ranking on job descriptions)

  ↓ Reciprocal Rank Fusion (60% semantic, 40% BM25)

→ Top N jobs returned ordered by match score (0–100)
```

---

## 📈 Future Improvements

- Admin dashboard
- Cloud deployment (AWS / GCP)
- Resume versioning
- Real-time application status tracking

---

## 👨‍💻 Author

**Hardi Naik**  
DA-IICT Gandhinagar  
AI & ML Enthusiast

GitHub: [https://github.com/Hardinaik](https://github.com/Hardinaik)

---

⭐ If you found this project useful, please give it a star!