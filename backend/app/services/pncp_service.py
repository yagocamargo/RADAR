"""
Integracao com o Portal Nacional de Contratacoes Publicas (PNCP).
Base: https://pncp.gov.br/api/pncp/v1 — sem autenticacao.
⚠️ Respeitar delay de 2s entre chamadas (rate limit).
"""
import asyncio
import httpx

from app.core.config import settings

PNCP_DELAY_SECONDS = 2.0


async def fetch_contracts_by_cnpj(cnpj: str) -> list[dict]:
    """
    Busca contratos publicos vinculados a um CNPJ no PNCP.
    Retorna lista vazia em caso de erro/indisponibilidade — a coleta e
    best-effort e nao deve derrubar o restante do sistema.
    """
    url = f"{settings.PNCP_BASE_URL}/contratos"
    params = {"cnpjFornecedor": cnpj}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            await asyncio.sleep(PNCP_DELAY_SECONDS)
            return data.get("data", []) if isinstance(data, dict) else data
    except (httpx.HTTPError, ValueError):
        return []
