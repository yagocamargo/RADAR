import uuid
from datetime import datetime
from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_empresas: int
    empresas_em_expansao: int
    contratos_do_mes: int
    indice_aquecimento: float


class TopGrowthCompany(BaseModel):
    id: uuid.UUID
    slug: str
    nome_fantasia: str
    uf: str
    growth_signal: float
    vagas_abertas_30d: int


class SignalFeedItem(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_nome: str
    type: str
    title: str
    uf: str | None
    signal_date: datetime


class SegmentActivity(BaseModel):
    segment: str
    count: int


class DashboardResponse(BaseModel):
    metrics: DashboardMetrics
    top_growth: list[TopGrowthCompany]
    signal_feed: list[SignalFeedItem]
    activity_by_segment: list[SegmentActivity]


class MercadoKPI(BaseModel):
    label: str
    value: float
    variation_pct: float


class RegionalBar(BaseModel):
    uf: str
    count: int


class SegmentBar(BaseModel):
    segment: str
    count: int


class MercadoResponse(BaseModel):
    kpis: list[MercadoKPI]
    by_segment: list[SegmentBar]
    by_region: list[RegionalBar]
    top_growth: list[TopGrowthCompany]
    recent_signals: list[SignalFeedItem]
