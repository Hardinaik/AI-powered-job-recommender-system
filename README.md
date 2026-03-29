# 🚀 AI-Powered Job Recommender System

An intelligent full-stack Job Recommendation Platform that matches job seekers with relevant jobs using **AI-powered semantic search and vector embeddings**.

Instead of simple keyword matching, this system parses resumes with an LLM, extracts structured skill and experience data, generates multiple embeddings, and ranks jobs using weighted cosine similarity via pgvector.

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

### 👩‍💻 Job Seeker Dashboard
- Register & login
- Build a profile with preferred domain, experience, and locations
- Upload resume (PDF, max 5 MB)
- Resume parsed by LLM → skills, work experience, and projects extracted separately
- Three resume embeddings generated and stored
- AI-based job recommendations with match score (0–100)
- Two recommendation modes:
  - **Profile Mode** — uses saved profile filters + stored resume embeddings
  - **Manual Mode** — custom filters with optional one-shot resume upload (not saved to DB)
- Filter jobs by Industry Domain, Experience, and multiple Locations

---

## 🧠 AI & Smart Matching

### Embedding Architecture

| Resume Vector | Job Vector | Weight |
|---|---|---|
| `skill_embedding` | `skill_embedding` | 50% |
| `work_embedding` | `job_embedding` | 30% |
| `project_embedding` | `job_embedding` | 20% |

- Resume is split into **three separate embeddings**: skills, work experience summary, and projects summary
- Job descriptions are split into **two embeddings**: skills and a combined responsibility + domain summary
- Weighted cosine distance is computed in PostgreSQL using pgvector
- Match score = `(1 − weighted_distance) × 100`

### LLM Extraction (Gemini)
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

## 🛠 Tech Stack

### Backend
- **FastAPI** — REST API framework
- **SQLAlchemy ORM** — database models
- **PostgreSQL + pgvector** — vector similarity search
- **Sentence Transformers** — `multi-qa-MiniLM-L6-cos-v1` (384-dim embeddings)
- **LangChain + Gemini API** — LLM-based structured extraction
- **PyMuPDF** — PDF text extraction
- **JWT Authentication** — role-based access control

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
│   │   ├── models.py          # SQLAlchemy models (User, Job, Resume, etc.)
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── database.py        # DB connection
│   │   ├── main.py            # App entry point
│   │   ├── utils.py           # Auth helpers
│   │   ├── auth/              # Login & signup routes
│   │   ├── jobs/              # Job posting routes + job embedding utils
│   │   ├── resume/            # Resume upload routes + resume embedding utils
│   │   └── recommendations/   # Recommendation route (profile & manual modes)
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

> **Important:** Ensure embedding columns in the `resume` and `job` tables are typed as `vector(384)`, not `varchar`. If you encounter a `StringDataRightTruncation` error, run:
> ```sql
> ALTER TABLE resume
>   ALTER COLUMN skill_embedding   TYPE vector(384) USING skill_embedding::vector,
>   ALTER COLUMN work_embedding    TYPE vector(384) USING work_embedding::vector,
>   ALTER COLUMN project_embedding TYPE vector(384) USING project_embedding::vector;
>
> ALTER TABLE job
>   ALTER COLUMN skill_embedding TYPE vector(384) USING skill_embedding::vector,
>   ALTER COLUMN job_embedding   TYPE vector(384) USING job_embedding::vector;
> ```

---

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
API_KEY=your_gemini_api_key_here
```

> Note: The Gemini API key env variable is `API_KEY` (not `GEMINI_API_KEY`).

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

---

## 📌 API Endpoints

### 🔑 Auth
| Method | Endpoint |
|---|---|
| POST | `/auth/signup` |
| POST | `/auth/login` |

### 💼 Jobs
| Method | Endpoint |
|---|---|
| POST | `/jobs/post` |
| GET | `/jobs/postedjobs` |
| DELETE | `/jobs/{job_id}` |
| GET | `/jobs/locations` |
| GET | `/jobs/industry-domains` |

### 📄 Resume
| Method | Endpoint |
|---|---|
| POST | `/resume/upload` |

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
3. LLM extracts skills + job summary → two embeddings stored in DB

**Job Seeker:**
1. Job seeker signs up and logs in
2. Fills out profile (domain, experience, preferred locations)
3. Uploads resume → LLM extracts skills, work history, projects → three embeddings stored
4. Opens job listings page:
   - **Profile mode**: checks "Recommend using profile" → backend uses saved profile filters + stored embeddings
   - **Manual mode**: selects domain, locations (multi-select), experience, and optionally uploads a resume for one-shot scoring
5. Jobs ranked by weighted cosine similarity and returned with a match score

---

## 🧬 How Recommendation Works

```
Resume PDF
  └─► Text Extraction (PyMuPDF)
  └─► PII Removal
  └─► LLM Extraction (Gemini)
        ├─ skills          → skill_embedding   (384-dim)
        ├─ work summary    → work_embedding    (384-dim)
        └─ project summary → project_embedding (384-dim)

Job Description
  └─► LLM Extraction (Gemini)
        ├─ skills      → skill_embedding  (384-dim)
        └─ job summary → job_embedding    (384-dim)

Weighted Cosine Similarity (pgvector):
  50% × cosine(resume.skill_embedding,   job.skill_embedding)
  30% × cosine(resume.work_embedding,    job.job_embedding)
  20% × cosine(resume.project_embedding, job.job_embedding)

→ Top N jobs returned ordered by match score
```

---

## 📈 Future Improvements

- Admin dashboard
- Support for multiple preferred location filtering in profile mode
- Cloud deployment (AWS / GCP)
- Resume versioning
- Email notifications for new matching jobs

---

## 👨‍💻 Author

**Hardi Naik**  
DA-IICT Gandhinagar  
AI & ML Enthusiast

GitHub: [https://github.com/Hardinaik](https://github.com/Hardinaik)

---

⭐ If you found this project useful, please give it a star!