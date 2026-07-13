import uuid
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.company import Company
from app.models.segment import CompanySegment, Segment
from app.models.signal import MarketSignal, SignalType
from app.models.hunting import HuntingQuery
from app.models.user import User
from app.schemas.hunting import (
    HuntingRequest,
    HuntingResponse,
    RankedCompany,
    SaveQueryRequest,
    HuntingHistoryItem,
)
from app.schemas.company import SegmentTag
from app.services import ai_service
from app.services.scoring import compute_hunting_score

router = APIRouter(prefix="/hunting", tags=["hunting"])


@router.post("", response_model=HuntingResponse)
async def run_hunting(
    payload: HuntingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Interpretar a busca (IA com fallback por palavras-chave)
    interpreted_segments, interpreted_uf = await ai_service.interpret_hunting_query(payload.query)
    if payload.segments:
        interpreted_segments = list(set(interpreted_segments) | set(s.lower() for s in payload.segments))
    if payload.uf:
        interpreted_uf = payload.uf.upper()

    searched_segment_slugs = {s.lower().replace(" ", "-") for s in interpreted_segments}

    # 2. Carregar empresas com segmentos
    result = await db.execute(
        select(Company)
        .options(selectinload(Company.segment_links).selectinload(CompanySegment.segment))
        .where(Company.e_monitorada.is_(True))
    )
    companies = result.unique().scalars().all()

    # 3. Ranquear
    ranked: list[RankedCompany] = []
    for company in companies:
        company_segment_slugs = {link.segment.slug for link in company.segment_links}
        score = compute_hunting_score(company, company_segment_slugs, searched_segment_slugs, interpreted_uf)
        ranked.append(
            RankedCompany(
                id=company.id,
                slug=company.slug,
                nome_fantasia=company.nome_fantasia,
                uf=company.uf,
                cidade=company.cidade,
                municipios_atendidos=company.municipios_atendidos,
                vagas_abertas_30d=company.vagas_abertas_30d,
                score=score,
                segments=[
                    SegmentTag(id=l.segment.id, name=l.segment.name, slug=l.segment.slug, confidence_score=float(l.confidence_score))
                    for l in company.segment_links
                ],
            )
        )

    ranked.sort(key=lambda c: c.score, reverse=True)
    top_ranked = ranked[:30]

    # 4. Concentracao regional
    regional_concentration: dict[str, int] = {}
    for c in ranked:
        regional_concentration[c.uf] = regional_concentration.get(c.uf, 0) + 1

    # 5. Tendencia de vagas nos ultimos 12 meses (agregado por mes a partir de sinais)
    twelve_months_ago = date.today() - timedelta(days=365)
    signal_result = await db.execute(
        select(MarketSignal)
        .join(Company)
        .where(
            MarketSignal.type == SignalType.vaga_aberta,
            MarketSignal.signal_date >= twelve_months_ago,
        )
    )
    signals = signal_result.scalars().all()
    monthly_counts: dict[str, int] = {}
    for s in signals:
        key = s.signal_date.strftime("%Y-%m")
        monthly_counts[key] = monthly_counts.get(key, 0) + 1
    trend = [{"month": k, "vagas": v} for k, v in sorted(monthly_counts.items())]

    # 6. Resumo e sugestoes de IA
    companies_dump = [c.model_dump() for c in top_ranked]
    ai_summary = await ai_service.generate_hunting_summary(payload.query, companies_dump)
    ai_suggestions = await ai_service.generate_hunting_suggestions(payload.query, companies_dump)

    # 7. Salvar historico da consulta
    query_record = HuntingQuery(
        user_id=current_user.id,
        query_text=payload.query,
        filters={"segments": interpreted_segments, "uf": interpreted_uf},
        results={"top_company_ids": [str(c.id) for c in top_ranked]},
        ai_summary=ai_summary,
    )
    db.add(query_record)
    await db.commit()
    await db.refresh(query_record)

    return HuntingResponse(
        query_id=query_record.id,
        interpreted_segments=interpreted_segments,
        interpreted_uf=interpreted_uf,
        companies=top_ranked,
        regional_concentration=regional_concentration,
        trend_last_12_months=trend,
        ai_summary=ai_summary,
        ai_suggestions=ai_suggestions,
        ai_enabled=settings.ai_enabled,
    )


@router.post("/salvar", response_model=HuntingHistoryItem)
async def save_query(
    payload: SaveQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HuntingQuery).where(HuntingQuery.id == payload.query_id, HuntingQuery.user_id == current_user.id)
    )
    query_record = result.scalar_one_or_none()
    if not query_record:
        raise HTTPException(status_code=404, detail="Consulta nao encontrada")

    query_record.saved = True
    query_record.monitoring_active = payload.monitoring_active
    await db.commit()
    await db.refresh(query_record)
    return query_record


@router.get("/historico", response_model=list[HuntingHistoryItem])
async def get_history(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(HuntingQuery)
        .where(HuntingQuery.user_id == current_user.id)
        .order_by(HuntingQuery.created_at.desc())
        .limit(20)
    )
    return result.scalars().all()
