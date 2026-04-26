from contextlib import asynccontextmanager
from fastapi import FastAPI,Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routes import router as auth_router
from app.jobs.routes import router as job_router
from app.applications.routes import router as application_router
from app.recommendations.routes import router as recommendation_router
from app.profile.routes import router as profile_router
from app.resume.routes import router as resume_router
from app.auth.passwords.routes import router as reset_pass_router
from app.notifications.routes import router as notification_router
from app.modelregistry import preload_models, cleanup_models
from app.config import settings

 

FRONTEND_URL=settings.FRONTEND_URL

@asynccontextmanager
async def lifespan(app: FastAPI):
    preload_models()       # runs on startup
    yield
    cleanup_models()


app = FastAPI(lifespan=lifespan)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
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
app.include_router(notification_router)


@app.get("/")
def root():
    return {"status": "backend running"}