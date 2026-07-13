from fastapi import APIRouter, Depends
import redis.asyncio as aioredis

from app.api.deps import require_admin_or_manager
from app.core.config import settings
from app.db.session import get_db
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends as FastDepends

from app.models.company import Company
from app.models.contract import Contract
from app.models.signal import MarketSignal
from app.models.user import User as UserModel
from app.models.alert import Alert, AlertStatus
from app.schemas.admin import AdminStatsResponse, AdminStats, RedisInfo, TriggerAgentResponse
from app.tasks.agents import (
    task_enrichment,
    task_monitoring,
    task_alerts,
    task_pncp_collect,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin_or_manager),
):
    total_empresas = (await db.execute(select(func.count(Company.id)))).scalar_one()
    total_contratos = (await db.execute(select(func.count(Contract.id)))).scalar_one()
    total_sinais = (await db.execute(select(func.count(MarketSignal.id)))).scalar_one()
    total_usuarios = (await db.execute(select(func.count(UserModel.id)))).scalar_one()
    alertas_nao_lidos = (
        await db.execute(select(func.count(Alert.id)).where(Alert.status == AlertStatus.nao_lido))
    ).scalar_one()

    redis_status = "indisponivel"
    used_memory = None
    try:
        client = aioredis.from_url(settings.REDIS_URL, socket_timeout=2)
        info = await client.info("memory")
        used_memory = info.get("used_memory_human")
        redis_status = "conectado"
        await client.aclose()
    except Exception:
        redis_status = "indisponivel"

    return AdminStatsResponse(
        stats=AdminStats(
            total_empresas=total_empresas,
            total_contratos=total_contratos,
            total_sinais=total_sinais,
            total_usuarios=total_usuarios,
            alertas_nao_lidos=alertas_nao_lidos,
        ),
        redis=RedisInfo(status=redis_status, used_memory_human=used_memory),
    )


@router.post("/cache/limpar")
async def clear_cache(current_user=Depends(require_admin_or_manager)):
    try:
        client = aioredis.from_url(settings.REDIS_URL, socket_timeout=2)
        await client.flushdb()
        await client.aclose()
        return {"ok": True, "message": "Cache limpo com sucesso"}
    except Exception as e:
        return {"ok": False, "message": str(e)}


@router.post("/agentes/enriquecimento", response_model=TriggerAgentResponse)
async def trigger_enrichment(current_user=Depends(require_admin_or_manager)):
    result = task_enrichment.delay()
    return TriggerAgentResponse(task_id=result.id, status="disparado", agent="enriquecimento")


@router.post("/agentes/monitoramento", response_model=TriggerAgentResponse)
async def trigger_monitoring(current_user=Depends(require_admin_or_manager)):
    result = task_monitoring.delay()
    return TriggerAgentResponse(task_id=result.id, status="disparado", agent="monitoramento")


@router.post("/agentes/alertas", response_model=TriggerAgentResponse)
async def trigger_alerts(current_user=Depends(require_admin_or_manager)):
    result = task_alerts.delay()
    return TriggerAgentResponse(task_id=result.id, status="disparado", agent="alertas")


@router.post("/agentes/pncp", response_model=TriggerAgentResponse)
async def trigger_pncp_collect(current_user=Depends(require_admin_or_manager)):
    result = task_pncp_collect.delay()
    return TriggerAgentResponse(task_id=result.id, status="disparado", agent="coleta_pncp")
