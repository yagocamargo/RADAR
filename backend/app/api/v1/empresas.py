import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.company import Company
from app.models.contract import Contract
from app.models.segment import CompanySegment, Segment
from app.models.signal import MarketSignal
from app.models.user import User
from app.schemas.company import (
    CompanyListItem,
    CompanyListResponse,
    CompanyDetail,
    SegmentTag,
    ContractOut,
    SignalOut,
)
from app.services import ai_service

router = APIRouter(prefix="/empresas", tags=["empresas"])


def _to_list_item(company: Company) -> CompanyListItem:
    segments = [
        SegmentTag(id=link.segment.id, name=link.segment.name, slug=link.segment.slug, confidence_score=float(link.confidence_score))
        for link in company.segment_links
    ]
    return CompanyListItem(
        id=company.id,
        slug=company.slug,
        nome_fantasia=company.nome_fantasia,
        razao_social=company.razao_social,
        cnpj=company.cnpj,
        uf=company.uf,
        cidade=company.cidade,
        municipios_atendidos=company.municipios_atendidos,
        contratos_ativos=company.contratos_ativos,
        vagas_abertas_30d=company.vagas_abertas_30d,
        e_concorrente=company.e_concorrente,
        e_monitorada=company.e_monitorada,
        e_verificada=company.e_verificada,
        momentum=company.momentum,
        segments=segments,
    )


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    search: str | None = Query(None, description="Busca por nome ou CNPJ"),
    segmento: str | None = Query(None),
    uf: str | None = Query(None),
    concorrente: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Company).options(selectinload(Company.segment_links).selectinload(CompanySegment.segment))
    count_query = select(func.count(Company.id))

    conditions = []
    if search:
        like = f"%{search}%"
        conditions.append(or_(Company.nome_fantasia.ilike(like), Company.razao_social.ilike(like), Company.cnpj.ilike(like)))
    if uf:
        conditions.append(Company.uf == uf.upper())
    if concorrente is not None:
        conditions.append(Company.e_concorrente == concorrente)

    if segmento:
        query = query.join(CompanySegment).join(Segment).where(Segment.slug == segmento)
        count_query = count_query.join(CompanySegment).join(Segment).where(Segment.slug == segmento)

    for cond in conditions:
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Company.relevance_score.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    companies = result.unique().scalars().all()

    return CompanyListResponse(
        items=[_to_list_item(c) for c in companies],
        total=total,
        page=page,
        page_size=page_size,
    )


async def _get_company_by_slug(slug: str, db: AsyncSession) -> Company:
    result = await db.execute(
        select(Company)
        .options(selectinload(Company.segment_links).selectinload(CompanySegment.segment))
        .where(Company.slug == slug)
    )
    company = result.unique().scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada")
    return company


@router.get("/{slug}", response_model=CompanyDetail)
async def get_company(slug: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = await _get_company_by_slug(slug, db)
    item = _to_list_item(company)
    return CompanyDetail(
        **item.model_dump(),
        endereco=company.endereco,
        valor_total_contratos=float(company.valor_total_contratos),
        vagas_abertas_90d=company.vagas_abertas_90d,
        relevance_score=float(company.relevance_score),
        growth_signal=float(company.growth_signal),
        profile_completeness=float(company.profile_completeness),
        ai_summary=company.ai_summary,
        ai_summary_updated_at=company.ai_summary_updated_at,
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


@router.get("/{slug}/timeline", response_model=list[SignalOut])
async def get_company_timeline(slug: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = await _get_company_by_slug(slug, db)
    result = await db.execute(
        select(MarketSignal).where(MarketSignal.company_id == company.id).order_by(MarketSignal.signal_date.desc())
    )
    return result.scalars().all()


@router.get("/{slug}/contratos", response_model=list[ContractOut])
async def get_company_contracts(slug: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = await _get_company_by_slug(slug, db)
    result = await db.execute(
        select(Contract).where(Contract.company_id == company.id).order_by(Contract.data_inicio.desc())
    )
    return result.scalars().all()


@router.get("/{slug}/concorrentes", response_model=list[CompanyListItem])
async def get_company_competitors(slug: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = await _get_company_by_slug(slug, db)
    segment_ids = [link.segment_id for link in company.segment_links]
    if not segment_ids:
        return []

    result = await db.execute(
        select(Company)
        .join(CompanySegment)
        .options(selectinload(Company.segment_links).selectinload(CompanySegment.segment))
        .where(CompanySegment.segment_id.in_(segment_ids), Company.id != company.id)
        .distinct()
    )
    competitors = result.unique().scalars().all()
    return [_to_list_item(c) for c in competitors]


@router.post("/{slug}/gerar-resumo", response_model=CompanyDetail)
async def regenerate_ai_summary(slug: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import datetime, timezone

    company = await _get_company_by_slug(slug, db)
    company_data = {
        "nome_fantasia": company.nome_fantasia,
        "uf": company.uf,
        "cidade": company.cidade,
        "municipios_atendidos": company.municipios_atendidos,
        "contratos_ativos": company.contratos_ativos,
        "vagas_abertas_30d": company.vagas_abertas_30d,
        "segmentos": [link.segment.name for link in company.segment_links],
    }
    summary = await ai_service.generate_company_summary(company_data)
    company.ai_summary = summary
    company.ai_summary_updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(company)

    return await get_company(slug, db, current_user)
