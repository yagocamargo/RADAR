"""
Enriquecimento de dados cadastrais a partir do CNPJ.
Fonte primaria: ReceitaWS. Fallback: BrasilAPI.
Sem autenticacao — respeitar delay entre chamadas para evitar bloqueio.
"""
import asyncio
import httpx

from app.core.config import settings

CNPJ_DELAY_SECONDS = 1.5


async def fetch_cnpj_data(cnpj: str) -> dict | None:
    clean_cnpj = "".join(filter(str.isdigit, cnpj))

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(settings.RECEITAWS_URL.format(cnpj=clean_cnpj))
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") != "ERROR":
                    await asyncio.sleep(CNPJ_DELAY_SECONDS)
                    return data
    except httpx.HTTPError:
        pass

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(settings.BRASILAPI_URL.format(cnpj=clean_cnpj))
            if resp.status_code == 200:
                await asyncio.sleep(CNPJ_DELAY_SECONDS)
                return resp.json()
    except httpx.HTTPError:
        pass

    return None
