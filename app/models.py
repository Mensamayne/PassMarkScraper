"""Pydantic models for API requests and responses."""

from pydantic import BaseModel


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


# Recommendation models


class PairingAnalysisRequest(BaseModel):
    """Request model for pairing analysis."""

    cpu: str  # CPU name
    gpu: str  # GPU name


class CategoryAnalysis(BaseModel):
    """Analysis for a single game category."""

    balance_score: int
    bottleneck: str | None
    cpu_utilization: int
    gpu_utilization: int
    performance: str
    meets_minimum: bool
    issues: list[str]


class PairingAnalysisResponse(BaseModel):
    """Response model for pairing analysis."""

    cpu: BenchmarkResponse
    gpu: BenchmarkResponse
    overall_balance_score: int
    overall_verdict: str
    overall_bottleneck: str | None
    by_category: dict[str, CategoryAnalysis]


class RecommendPairingRequest(BaseModel):
    """Request model for component pairing recommendations."""

    cpu: str | None = None
    gpu: str | None = None
    game_focus: str | None = None  # esport, aaa_gpu, balanced, simulation
    limit: int = 5


class ComponentRecommendation(BaseModel):
    """Single component recommendation."""

    name: str
    passmark_score: int
    normalized_score: int
    tier: str
    match_score: int
    balance_description: str


class RecommendPairingResponse(BaseModel):
    """Response model for pairing recommendations."""

    base_component: BenchmarkResponse
    base_component_type: str
    game_focus: str | None
    recommendations: list[ComponentRecommendation]


class GamingProfileRequest(BaseModel):
    """Request model for gaming profile."""

    cpu: str
    gpu: str
    resolution: str = "1440p"  # 1080p, 1440p, 4K


class GameCategoryPerformance(BaseModel):
    """Performance info for a game category."""

    games: list[str]
    fps_estimate: str
    settings: str
    bottleneck: str | None
    cpu_utilization: str
    gpu_utilization: str


class GamingProfileResponse(BaseModel):
    """Response model for gaming profile."""

    cpu: BenchmarkResponse
    gpu: BenchmarkResponse
    resolution: str
    overall_balance_score: int
    overall_verdict: str
    performance_by_category: dict[str, GameCategoryPerformance]
    upgrade_recommendations: dict[str, str]


class PerformanceEstimateResponse(BaseModel):
    """Response model for performance estimation."""

    component_name: str
    component_type: str
    passmark_score: int
    normalized_score: int
    tier: str
    estimated_performance: dict[str, str]
    gaming_tiers: dict[str, str]
    note: str