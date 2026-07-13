from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.company import Company
from app.models.contract import Contract, ContractStatus
from app.models.segment import CompanySegment, Segment
from app.models.signal import MarketSignal
from app.models.user import User
from app.schemas.dashboard import (
    DashboardResponse,
    DashboardMetrics,
    TopGrowthCompany,
    SignalFeedItem,
    SegmentActivity,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_empresas = (await db.execute(select(func.count(Company.id)))).scalar_one()

    empresas_em_expansao = (
        await db.execute(select(func.count(Company.id)).where(Company.growth_signal >= 0.66))
    ).scalar_one()

    start_of_month = date.today().replace(day=1)
    contratos_do_mes = (
        await db.execute(
            select(func.count(Contract.id)).where(
                Contract.data_inicio >= start_of_month, Contract.status == ContractStatus.ativo
            )
        )
    ).scalar_one()

    avg_growth = (await db.execute(select(func.avg(Company.growth_signal)))).scalar_one() or 0
    indice_aquecimento = round(float(avg_growth) * 100, 1)

    top_growth_result = await db.execute(
        select(Company).order_by(Company.growth_signal.desc()).limit(6)
    )
    top_growth = [
        TopGrowthCompany(
            id=c.id, slug=c.slug, nome_fantasia=c.nome_fantasia, uf=c.uf,
            growth_signal=float(c.growth_signal), vagas_abertas_30d=c.vagas_abertas_30d,
        )
        for c in top_growth_result.scalars().all()
    ]

    signals_result = await db.execute(
        select(MarketSignal, Company.nome_fantasia)
        .join(Company, MarketSignal.company_id == Company.id)
        .order_by(MarketSignal.signal_date.desc())
        .limit(10)
    )
    signal_feed = [
        SignalFeedItem(
            id=s.id, company_id=s.company_id, company_nome=nome,
            type=s.type.value, title=s.title, uf=s.uf, signal_date=s.signal_date,
        )
        for s, nome in signals_result.all()
    ]

    activity_result = await db.execute(
        select(Segment.name, func.count(CompanySegment.id))
        .join(CompanySegment, CompanySegment.segment_id == Segment.id)
        .group_by(Segment.name)
        .order_by(func.count(CompanySegment.id).desc())
    )
    activity_by_segment = [SegmentActivity(segment=name, count=count) for name, count in activity_result.all()]

    return DashboardResponse(
        metrics=DashboardMetrics(
            total_empresas=total_empresas,
            empresas_em_expansao=empresas_em_expansao,
            contratos_do_mes=contratos_do_mes,
            indice_aquecimento=indice_aquecimento,
        ),
        top_growth=top_growth,
        signal_feed=signal_feed,
        activity_by_segment=activity_by_segment,
    )
