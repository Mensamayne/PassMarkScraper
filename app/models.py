"""Pydantic models for API requests and responses."""
from pydantic import BaseModel
from typing import Optional


class BenchmarkResponse(BaseModel):
    """Response model for benchmark lookup."""
    name: str
    passmark_score: int
    normalized_score: int
    tier: str


class ScrapeResult(BaseModel):
    """Result from scraping a single component."""
    raw_data: dict
    normalized: dict
    would_insert_sql: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    db_path: str
    db_exists: bool


