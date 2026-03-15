# 🚀 AI-Powered Job Recommender System

An intelligent full-stack Job Recommendation Platform that matches job seekers with relevant jobs using **AI-powered semantic search and embeddings**.

This system uses resume parsing, skill extraction, and vector similarity search to recommend the most relevant jobs instead of simple keyword matching.

---

## 🚧 Project Status

This project is currently under active development.

## 🔥 Key Features

### 👨‍💼 Recruiter Dashboard
- Secure JWT-based authentication
- Post new job listings
- View all posted jobs
- Delete jobs
- Job description embeddings stored using pgvector

### 👩‍💻 Job Seeker Dashboard
- Register & login
- Upload resume (PDF supported)
- Resume converted to text
- Skills & responsibilities extracted using LLM
- Resume embeddings generated
- AI-based job recommendations
- Filter jobs by:
  - Location
  - Industry Domain
  - Experience

---

## 🧠 AI & Smart Matching

Instead of traditional keyword filtering, this system:

- Converts job descriptions into vector embeddings
- Converts resumes into vector embeddings
- Uses PostgreSQL + pgvector for similarity search
- Returns most relevant jobs using semantic similarity

---

## 🛠 Tech Stack

### Backend
- FastAPI
- SQLAlchemy ORM
- PostgreSQL
- pgvector (vector similarity search)
- JWT Authentication
- Sentence Transformers (for embeddings)
- LLM-based skill extraction (Gemini api)

### Frontend
- React.js
- Axios
- Custom CSS
- Role-based dashboards

---

## 📁 Project Structure

```
AI-powered-job-recommender-system/
│
├── backend/
│   ├── app/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── utils.py
│   │   ├── auth/
│   │   ├── jobs/
│   │   └── resume/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── styles/
│   └── package.json
│
├
└── README.md
```

---

## ⚙️ Setup Instructions

---

### 🧩 Prerequisites

- Python 3.9+
- Node.js 14+
- PostgreSQL installed 
- pgvector extension enabled

To enable pgvector:

```sql
CREATE EXTENSION vector;
```

---

## 🔧 Backend Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Hardinaik/AI-powered-job-recommender-system.git
cd AI-powered-job-recommender-system/backend
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

Activate:

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a `.env` file inside backend folder:

```
DATABASE_URL=postgresql://username:password@localhost:5432/jobdb
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
GEMINI_API_KEY=your_api_key_here
```

### 5️⃣ Run Server

```bash
uvicorn app.main:app --reload
```

Backend will run on:
```
http://127.0.0.1:8000
```

Swagger Docs:
```
http://127.0.0.1:8000/docs
```

---

## 💻 Frontend Setup

Navigate to frontend folder:

```bash
cd ../frontend
npm install
npm start
```

Frontend runs on:
```
http://localhost:3000
```

---

## 🔐 Authentication

- JWT-based authentication
- Role-based access control:
  - Recruiter
  - Job Seeker
- Token stored in localStorage
- Protected API routes

---

## 📌 Core API Endpoints

### 🔑 Auth
- `POST /auth/signup`
- `POST /auth/login`


### 💼 Jobs
- `POST /jobs/post`
- `GET /jobs/postedjobs`
- `DELETE /jobs/{job_id}`
- `GET /jobs/locations`
- `GET /jobs/industry-domains`

### Recommendations
- 'POST /recommendations/jobs'

### Applications

-'POST /applications/jobs/{job_id}/save'
-'POST /applications/jobs/{job_id}/apply'
-'GET /applications/saved-jobs/ids'
-'GET /applications/applied-jobs/ids'
-'GET /applications/saved-jobs/details'
-'GET /applications/applied-jobs/details'



---

## 🧪 Example Workflow

1. Recruiter logs in  
2. Recruiter posts a job  
3. Job embedding is generated and stored  
4. Job seeker uploads resume and applies filters  
5. Resume text extracted & skills parsed  
6. Resume embedding generated  
7. Similarity search performed  
8. Top matching jobs returned  

---

## 🧬 How Recommendation Works

```
Resume → Text Extraction → Skill Extraction,Work/Project Summary Extraction → Embedding
Job Description → Skill Extraction, Responsibility Summary Extraction → Embedding
Cosine Similarity (pgvector)
similar jobs returned
```

---

## 📈 Future Improvements

- Admin dashboard
- Improved ranking algorithm
- Cloud deployment (AWS/GCP)

---

## 👨‍💻 Author

**Hardi Naik**  
DA-IICT Gandhinagar  
AI & ML Enthusiast  

GitHub:
https://github.com/Hardinaik

---

⭐ If you found this project useful, please give it a star!
