from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routes import router as auth_router
from app.jobs.routes import router as job_router
from app.applications.routes import router as application_router
from app.recommendations.routes import router as recommendation_router
from app.profile.routes import router as profile_router
from app.resume.routes import router as resume_router
from app.auth.reset_password.routes import router as reset_pass_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(job_router)
app.include_router(application_router)
app.include_router(recommendation_router)
app.include_router(profile_router)
app.include_router(resume_router)
app.include_router(reset_pass_router)

@app.get("/")
def root():
    return {"status": "backend running"}
