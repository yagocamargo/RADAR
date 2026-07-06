import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class ReportType(str, enum.Enum):
    mercado_mensal = "mercado_mensal"
    analise_segmento = "analise_segmento"
    perfil_empresa = "perfil_empresa"
    resumo_executivo = "resumo_executivo"


class ReportStatus(str, enum.Enum):
    na_fila = "na_fila"
    gerando = "gerando"
    pronto = "pronto"
    falhou = "falhou"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[ReportType] = mapped_column(SAEnum(ReportType, name="report_type"), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(SAEnum(ReportStatus, name="report_status"), default=ReportStatus.na_fila)

    params: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
