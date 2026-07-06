import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.report import Report, ReportStatus, ReportType
from app.models.company import Company
from app.models.contract import Contract
from app.models.signal import MarketSignal
from app.services import ai_service


async def _generate(report_id: str):
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as db:
        result = await db.execute(select(Report).where(Report.id == uuid.UUID(report_id)))
        report = result.scalar_one_or_none()
        if not report:
            await engine.dispose()
            return

        report.status = ReportStatus.gerando
        await db.commit()

        try:
            context: dict = {}

            if report.type == ReportType.mercado_mensal:
                total = (await db.execute(select(func.count(Company.id)))).scalar_one()
                contratos = (await db.execute(select(func.count(Contract.id)))).scalar_one()
                sinais = (await db.execute(select(func.count(MarketSignal.id)))).scalar_one()
                context = {"total_empresas": total, "total_contratos": contratos, "total_sinais": sinais}

            elif report.type == ReportType.analise_segmento:
                companies = (await db.execute(select(Company).limit(20))).scalars().all()
                context = {"empresas": [c.nome_fantasia for c in companies]}

            elif report.type == ReportType.perfil_empresa:
                companies = (await db.execute(select(Company).order_by(Company.relevance_score.desc()).limit(1))).scalars().all()
                context = {"empresa": companies[0].nome_fantasia if companies else None}

            elif report.type == ReportType.resumo_executivo:
                total = (await db.execute(select(func.count(Company.id)))).scalar_one()
                em_expansao = (await db.execute(select(func.count(Company.id)).where(Company.growth_signal >= 0.66))).scalar_one()
                context = {"total_empresas": total, "empresas_em_expansao": em_expansao}

            content = await ai_service.generate_report_content(report.type.value, {}, context)

            report.content = content
            report.status = ReportStatus.pronto
            report.completed_at = datetime.now(timezone.utc)
        except Exception as e:
            report.status = ReportStatus.falhou
            report.error_message = str(e)

        await db.commit()

    await engine.dispose()


@celery_app.task(name="app.tasks.reports.generate_report_task")
def generate_report_task(report_id: str):
    asyncio.run(_generate(report_id))
