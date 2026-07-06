import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.alert import Alert, AlertStatus
from app.models.user import User
from app.schemas.alert import AlertOut, AlertListResponse

router = APIRouter(prefix="/alertas", tags=["alertas"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    filtro: str = Query("todos", pattern="^(todos|nao_lidos|lidos|acionados)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Alert).where(Alert.user_id == current_user.id)

    if filtro == "nao_lidos":
        query = query.where(Alert.status == AlertStatus.nao_lido)
    elif filtro == "lidos":
        query = query.where(Alert.status == AlertStatus.lido)
    elif filtro == "acionados":
        query = query.where(Alert.status == AlertStatus.acionado)

    query = query.order_by(Alert.created_at.desc())
    result = await db.execute(query)
    items = result.scalars().all()

    unread_count = (
        await db.execute(
            select(func.count(Alert.id)).where(Alert.user_id == current_user.id, Alert.status == AlertStatus.nao_lido)
        )
    ).scalar_one()

    return AlertListResponse(items=items, unread_count=unread_count)


@router.patch("/{alert_id}/marcar-lido", response_model=AlertOut)
async def mark_as_read(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta nao encontrado")

    alert.status = AlertStatus.lido
    await db.commit()
    await db.refresh(alert)
    return alert


@router.post("/marcar-todos-lidos")
async def mark_all_as_read(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await db.execute(
        update(Alert)
        .where(Alert.user_id == current_user.id, Alert.status == AlertStatus.nao_lido)
        .values(status=AlertStatus.lido)
    )
    await db.commit()
    return {"ok": True}
