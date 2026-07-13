import uuid
from datetime import datetime
from pydantic import BaseModel


class ReportCreateRequest(BaseModel):
    title: str
    type: str  # mercado_mensal, analise_segmento, perfil_empresa, resumo_executivo
    params: dict | None = None


class ReportOut(BaseModel):
    id: uuid.UUID
    title: str
    type: str
    status: str
    content: str | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
