import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.report import Report, ReportType, ReportStatus
from app.models.user import User
from app.schemas.report import ReportCreateRequest, ReportOut
from app.tasks.reports import generate_report_task

router = APIRouter(prefix="/relatorios", tags=["relatorios"])


@router.get("", response_model=list[ReportOut])
async def list_reports(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Report).where(Report.user_id == current_user.id).order_by(Report.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ReportOut, status_code=201)
async def create_report(
    payload: ReportCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        report_type = ReportType(payload.type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Tipo de relatorio invalido")

    report = Report(
        user_id=current_user.id,
        title=payload.title,
        type=report_type,
        status=ReportStatus.na_fila,
        params=str(payload.params or {}),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    generate_report_task.delay(str(report.id))

    return report


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Report).where(Report.id == report_id, Report.user_id == current_user.id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Relatorio nao encontrado")
    return report
