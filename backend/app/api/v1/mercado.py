from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.company import Company
from app.models.contract import Contract, ContractStatus
from app.models.segment import CompanySegment, Segment
from app.models.signal import MarketSignal
from app.models.user import User
from app.schemas.dashboard import (
    MercadoResponse,
    MercadoKPI,
    SegmentBar,
    RegionalBar,
    TopGrowthCompany,
    SignalFeedItem,
)

router = APIRouter(prefix="/mercado", tags=["mercado"])


@router.get("", response_model=MercadoResponse)
async def get_mercado(
    segmento: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_empresas = (await db.execute(select(func.count(Company.id)))).scalar_one()
    em_expansao = (await db.execute(select(func.count(Company.id)).where(Company.growth_signal >= 0.66))).scalar_one()

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

    kpis = [
        MercadoKPI(label="Empresas monitoradas", value=total_empresas, variation_pct=0),
        MercadoKPI(label="Em expansao", value=em_expansao, variation_pct=0),
        MercadoKPI(label="Contratos do mes", value=contratos_do_mes, variation_pct=0),
        MercadoKPI(label="Indice de aquecimento", value=indice_aquecimento, variation_pct=0),
    ]

    by_segment_result = await db.execute(
        select(Segment.name, func.count(CompanySegment.id))
        .join(CompanySegment, CompanySegment.segment_id == Segment.id)
        .group_by(Segment.name)
        .order_by(func.count(CompanySegment.id).desc())
    )
    by_segment = [SegmentBar(segment=name, count=count) for name, count in by_segment_result.all()]

    region_query = select(Company.uf, func.count(Company.id))
    if segmento:
        region_query = region_query.join(CompanySegment).join(Segment).where(Segment.slug == segmento)
    region_query = region_query.group_by(Company.uf).order_by(func.count(Company.id).desc())
    by_region_result = await db.execute(region_query)
    by_region = [RegionalBar(uf=uf, count=count) for uf, count in by_region_result.all()]

    top_growth_result = await db.execute(select(Company).order_by(Company.growth_signal.desc()).limit(5))
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
        .limit(15)
    )
    recent_signals = [
        SignalFeedItem(
            id=s.id, company_id=s.company_id, company_nome=nome,
            type=s.type.value, title=s.title, uf=s.uf, signal_date=s.signal_date,
        )
        for s, nome in signals_result.all()
    ]

    return MercadoResponse(
        kpis=kpis, by_segment=by_segment, by_region=by_region,
        top_growth=top_growth, recent_signals=recent_signals,
    )
