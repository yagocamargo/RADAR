"""
Agentes de coleta em background (Celery tasks), conforme secao 6.3 do escopo:
- Enriquecimento: atualiza dados cadastrais das empresas via CNPJ
- Monitoramento: recalcula scores de crescimento/relevancia
- Alertas: gera alertas a partir de sinais recentes e monitoramentos ativos
- Coleta PNCP: busca novos contratos publicos

Todas as tasks podem ser disparadas manualmente pela pagina de Admin.
"""
import asyncio
import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.company import Company
from app.models.contract import Contract, ContractStatus
from app.models.signal import MarketSignal, SignalType
from app.models.alert import Alert, AlertPriority, AlertStatus
from app.models.monitoring import Monitoring
from app.models.user import User
from app.services import cnpj_service, pncp_service
from app.services.aggregates import recompute_company_aggregates, recompute_all_aggregates


def _run_async(coro):
    return asyncio.run(coro)


def _get_session_factory():
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return async_sessionmaker(bind=engine, expire_on_commit=False), engine


async def _enrichment_job():
    session_factory, engine = _get_session_factory()
    async with session_factory() as db:
        result = await db.execute(select(Company).where(Company.e_verificada.is_(False)))
        companies = result.scalars().all()

        updated = 0
        for company in companies[:20]:  # lote limitado por execucao
            data = await cnpj_service.fetch_cnpj_data(company.cnpj)
            if data:
                company.e_verificada = True
                company.profile_completeness = min(float(company.profile_completeness) + 0.2, 1.0)
                updated += 1

        await db.commit()
    await engine.dispose()
    return {"empresas_enriquecidas": updated}


async def _monitoring_job():
    session_factory, engine = _get_session_factory()
    async with session_factory() as db:
        # Primeiro, recalcula contratos_ativos e municipios_atendidos a partir
        # da tabela real de contratos (fonte de verdade) — corrige o problema
        # de esses campos ficarem desatualizados/inventados.
        await recompute_all_aggregates(db)
        await db.commit()

        result = await db.execute(select(Company))
        companies = result.scalars().all()

        for company in companies:
            # Recalcula growth_signal com base em vagas recentes e contratos ativos
            # (agora usando o valor de contratos_ativos ja recalculado acima)
            jobs_factor = min((company.vagas_abertas_30d or 0) / 10.0, 1.0)
            contracts_factor = min((company.contratos_ativos or 0) / 15.0, 1.0)
            company.growth_signal = round(min((jobs_factor * 0.6 + contracts_factor * 0.4), 1.0), 3)

        await db.commit()
    await engine.dispose()
    return {"empresas_atualizadas": len(companies)}


async def _alerts_job():
    session_factory, engine = _get_session_factory()
    async with session_factory() as db:
        # Gera alertas para todos monitoramentos ativos com base em sinais recentes (ultimas 24h)
        since = date.today() - timedelta(days=1)

        monitorings_result = await db.execute(select(Monitoring).where(Monitoring.active.is_(True)))
        monitorings = monitorings_result.scalars().all()

        created = 0
        for monitoring in monitorings:
            criteria = monitoring.criteria or {}
            uf = criteria.get("uf")

            signal_query = select(MarketSignal, Company).join(Company).where(MarketSignal.signal_date >= since)
            if uf:
                signal_query = signal_query.where(MarketSignal.uf == uf)

            signals_result = await db.execute(signal_query)
            for signal, company in signals_result.all():
                alert = Alert(
                    user_id=monitoring.user_id,
                    title=f"Novo sinal: {company.nome_fantasia}",
                    body=signal.title,
                    type=signal.type.value,
                    priority=AlertPriority.media,
                    status=AlertStatus.nao_lido,
                    company_id=company.id,
                )
                db.add(alert)
                created += 1

        await db.commit()
    await engine.dispose()
    return {"alertas_criados": created}


async def _pncp_collect_job():
    session_factory, engine = _get_session_factory()
    async with session_factory() as db:
        result = await db.execute(select(Company).where(Company.e_monitorada.is_(True)))
        companies = result.scalars().all()

        collected = 0
        touched_company_ids = set()
        for company in companies[:15]:  # respeita rate limit do PNCP
            contracts_data = await pncp_service.fetch_contracts_by_cnpj(company.cnpj)
            for c in contracts_data:
                pncp_id = c.get("numeroControlePNCP") or c.get("id")
                if not pncp_id:
                    continue

                existing = await db.execute(select(Contract).where(Contract.pncp_id == pncp_id))
                if existing.scalar_one_or_none():
                    continue

                contract = Contract(
                    company_id=company.id,
                    orgao_contratante=c.get("orgaoEntidade", {}).get("razaoSocial", "Nao informado") if isinstance(c.get("orgaoEntidade"), dict) else "Nao informado",
                    municipio=c.get("municipio", company.cidade),
                    uf=c.get("uf", company.uf),
                    objeto=c.get("objetoContrato", "Nao informado"),
                    valor=c.get("valorGlobal", 0) or 0,
                    status=ContractStatus.ativo,
                    pncp_id=str(pncp_id),
                )
                db.add(contract)
                collected += 1
                touched_company_ids.add(company.id)

        # Grava os contratos novos antes de recalcular os agregados, para que
        # a contagem abaixo ja enxergue as linhas recem-inseridas.
        await db.commit()

        # Corrige contratos_ativos e municipios_atendidos das empresas que
        # receberam contratos novos nesta execucao, usando a tabela real
        # de contratos como fonte de verdade (nao mais numero solto/aleatorio).
        for company_id in touched_company_ids:
            await recompute_company_aggregates(db, company_id)
        await db.commit()

    await engine.dispose()
    return {"contratos_coletados": collected, "empresas_atualizadas": len(touched_company_ids)}


@celery_app.task(name="app.tasks.agents.task_enrichment")
def task_enrichment():
    return _run_async(_enrichment_job())


@celery_app.task(name="app.tasks.agents.task_monitoring")
def task_monitoring():
    return _run_async(_monitoring_job())


@celery_app.task(name="app.tasks.agents.task_alerts")
def task_alerts():
    return _run_async(_alerts_job())


@celery_app.task(name="app.tasks.agents.task_pncp_collect")
def task_pncp_collect():
    return _run_async(_pncp_collect_job())
