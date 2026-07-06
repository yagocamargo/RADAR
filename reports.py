import uuid
from datetime import datetime
from pydantic import BaseModel

from app.schemas.company import SegmentTag


class HuntingRequest(BaseModel):
    query: str
    segments: list[str] | None = None
    uf: str | None = None


class RankedCompany(BaseModel):
    id: uuid.UUID
    slug: str
    nome_fantasia: str
    uf: str
    cidade: str
    municipios_atendidos: int
    vagas_abertas_30d: int
    score: float
    segments: list[SegmentTag] = []


class HuntingResponse(BaseModel):
    query_id: uuid.UUID
    interpreted_segments: list[str]
    interpreted_uf: str | None
    companies: list[RankedCompany]
    regional_concentration: dict[str, int]
    trend_last_12_months: list[dict]
    ai_summary: str | None
    ai_suggestions: list[str]
    ai_enabled: bool


class SaveQueryRequest(BaseModel):
    query_id: uuid.UUID
    monitoring_active: bool = True


class HuntingHistoryItem(BaseModel):
    id: uuid.UUID
    query_text: str
    saved: bool
    monitoring_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
