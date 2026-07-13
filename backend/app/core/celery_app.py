from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "radar",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.agents", "app.tasks.reports"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
)

celery_app.conf.beat_schedule = {
    "monitoramento-diario": {
        "task": "app.tasks.agents.task_monitoring",
        "schedule": 60 * 60 * 24,  # 24h
    },
    "enriquecimento-semanal": {
        "task": "app.tasks.agents.task_enrichment",
        "schedule": 60 * 60 * 24 * 7,  # 7 dias
    },
    "coleta-pncp-diaria": {
        "task": "app.tasks.agents.task_pncp_collect",
        "schedule": 60 * 60 * 24,  # 24h
    },
}
