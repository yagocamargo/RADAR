import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, Numeric, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identificação
    cnpj: Mapped[str] = mapped_column(String(18), unique=True, index=True, nullable=False)
    razao_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nome_fantasia: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Localização
    uf: Mapped[str] = mapped_column(String(2), index=True, nullable=False)
    cidade: Mapped[str] = mapped_column(String(255), nullable=False)
    endereco: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Dados de mercado
    municipios_atendidos: Mapped[int] = mapped_column(Integer, default=0)
    contratos_ativos: Mapped[int] = mapped_column(Integer, default=0)
    valor_total_contratos: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    vagas_abertas_30d: Mapped[int] = mapped_column(Integer, default=0)
    vagas_abertas_90d: Mapped[int] = mapped_column(Integer, default=0)

    # Scores (0 a 1)
    relevance_score: Mapped[float] = mapped_column(Numeric(4, 3), default=0)
    growth_signal: Mapped[float] = mapped_column(Numeric(4, 3), default=0)
    profile_completeness: Mapped[float] = mapped_column(Numeric(4, 3), default=0)

    # Flags
    e_concorrente: Mapped[bool] = mapped_column(Boolean, default=False)
    e_monitorada: Mapped[bool] = mapped_column(Boolean, default=True)
    e_verificada: Mapped[bool] = mapped_column(Boolean, default=False)

    # IA
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    segment_links: Mapped[list["CompanySegment"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    signals: Mapped[list["MarketSignal"]] = relationship(back_populates="company", cascade="all, delete-orphan")

    @property
    def momentum(self) -> str:
        if self.growth_signal >= 0.66:
            return "crescendo"
        if self.growth_signal >= 0.34:
            return "estavel"
        return "retracao"
