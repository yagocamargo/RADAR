from fastapi import APIRouter

from app.api.v1 import auth, dashboard, hunting, empresas, mercado, alertas, relatorios, admin

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(hunting.router)
api_router.include_router(empresas.router)
api_router.include_router(mercado.router)
api_router.include_router(alertas.router)
api_router.include_router(relatorios.router)
api_router.include_router(admin.router)
