"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin", "manager", "recruiter", "executive", name="user_role"), nullable=False, server_default="recruiter"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cnpj", sa.String(18), nullable=False, unique=True),
        sa.Column("razao_social", sa.String(255), nullable=False),
        sa.Column("nome_fantasia", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("uf", sa.String(2), nullable=False),
        sa.Column("cidade", sa.String(255), nullable=False),
        sa.Column("endereco", sa.Text, nullable=True),
        sa.Column("municipios_atendidos", sa.Integer, server_default="0"),
        sa.Column("contratos_ativos", sa.Integer, server_default="0"),
        sa.Column("valor_total_contratos", sa.Numeric(16, 2), server_default="0"),
        sa.Column("vagas_abertas_30d", sa.Integer, server_default="0"),
        sa.Column("vagas_abertas_90d", sa.Integer, server_default="0"),
        sa.Column("relevance_score", sa.Numeric(4, 3), server_default="0"),
        sa.Column("growth_signal", sa.Numeric(4, 3), server_default="0"),
        sa.Column("profile_completeness", sa.Numeric(4, 3), server_default="0"),
        sa.Column("e_concorrente", sa.Boolean, server_default=sa.false()),
        sa.Column("e_monitorada", sa.Boolean, server_default=sa.true()),
        sa.Column("e_verificada", sa.Boolean, server_default=sa.false()),
        sa.Column("ai_summary", sa.Text, nullable=True),
        sa.Column("ai_summary_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_companies_cnpj", "companies", ["cnpj"])
    op.create_index("ix_companies_slug", "companies", ["slug"])
    op.create_index("ix_companies_uf", "companies", ["uf"])

    op.create_table(
        "company_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("segments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("confidence_score", sa.Numeric(4, 3), server_default="0"),
    )

    op.create_table(
        "contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("orgao_contratante", sa.String(255), nullable=False),
        sa.Column("municipio", sa.String(255), nullable=False),
        sa.Column("uf", sa.String(2), nullable=False),
        sa.Column("objeto", sa.Text, nullable=False),
        sa.Column("valor", sa.Numeric(16, 2), server_default="0"),
        sa.Column("data_inicio", sa.Date, nullable=True),
        sa.Column("data_fim", sa.Date, nullable=True),
        sa.Column("status", sa.Enum("ativo", "expirado", "cancelado", name="contract_status"), server_default="ativo"),
        sa.Column("pncp_id", sa.String(255), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "market_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Enum("vaga_aberta", "novo_contrato", "expansao", "publicacao_diario_oficial", "noticia", name="signal_type"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("uf", sa.String(2), nullable=True),
        sa.Column("signal_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("priority", sa.Enum("baixa", "media", "alta", "critica", name="alert_priority"), server_default="media"),
        sa.Column("status", sa.Enum("nao_lido", "lido", "acionado", name="alert_status"), server_default="nao_lido"),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "hunting_queries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query_text", sa.Text, nullable=False),
        sa.Column("filters", postgresql.JSONB, server_default="{}"),
        sa.Column("results", postgresql.JSONB, server_default="{}"),
        sa.Column("ai_summary", sa.Text, nullable=True),
        sa.Column("saved", sa.Boolean, server_default=sa.false()),
        sa.Column("monitoring_active", sa.Boolean, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "monitorings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("criteria", postgresql.JSONB, server_default="{}"),
        sa.Column("frequency", sa.String(50), server_default="daily"),
        sa.Column("active", sa.Boolean, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("type", sa.Enum("mercado_mensal", "analise_segmento", "perfil_empresa", "resumo_executivo", name="report_type"), nullable=False),
        sa.Column("status", sa.Enum("na_fila", "gerando", "pronto", "falhou", name="report_status"), server_default="na_fila"),
        sa.Column("params", sa.Text, nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("monitorings")
    op.drop_table("hunting_queries")
    op.drop_table("alerts")
    op.drop_table("market_signals")
    op.drop_table("contracts")
    op.drop_table("company_segments")
    op.drop_table("companies")
    op.drop_table("segments")
    op.drop_table("users")

    sa.Enum(name="report_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="report_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="alert_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="alert_priority").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="signal_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="contract_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
