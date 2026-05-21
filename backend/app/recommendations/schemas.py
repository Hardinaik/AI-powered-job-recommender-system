
from pydantic import BaseModel
from typing import List
from app.schemas import JobItem



class RecommendationResponse(BaseModel):
    ranking_mode: str  # "hybrid" | "bm25_only" | "fallback"
    jobs: List[JobItem]