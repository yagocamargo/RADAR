import uuid
from datetime import datetime
from pydantic import BaseModel


class SegmentTag(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    confidence_score: float

    model_config = {"from_attributes": True}


class CompanyListItem(BaseModel):
    id: uuid.UUID
    slug: str
    nome_fantasia: str
    razao_social: str
    cnpj: str
    uf: str
    cidade: str
    municipios_atendidos: int
    contratos_ativos: int
    vagas_abertas_30d: int
    e_concorrente: bool
    e_monitorada: bool
    e_verificada: bool
    momentum: str
    segments: list[SegmentTag] = []

    model_config = {"from_attributes": True}


class CompanyDetail(CompanyListItem):
    endereco: str | None
    valor_total_contratos: float
    vagas_abertas_90d: int
    relevance_score: float
    growth_signal: float
    profile_completeness: float
    ai_summary: str | None
    ai_summary_updated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ContractOut(BaseModel):
    id: uuid.UUID
    orgao_contratante: str
    municipio: str
    uf: str
    objeto: str
    valor: float
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    status: str

    model_config = {"from_attributes": True}


class SignalOut(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    description: str | None
    uf: str | None
    signal_date: datetime

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    items: list[CompanyListItem]
    total: int
    page: int
    page_size: int
