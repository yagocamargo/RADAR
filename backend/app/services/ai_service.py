"""
Integracao com OpenAI. Todas as funcoes tem fallback funcional quando
OPENAI_API_KEY nao esta configurada (app.core.config.settings.ai_enabled == False),
conforme exigido no escopo: "sem a chave, as funcoes de IA ficam desabilitadas
mas o restante do sistema funciona".
"""
import json
import re
from typing import Optional

from openai import AsyncOpenAI, OpenAIError

from app.core.config import settings

_client: Optional[AsyncOpenAI] = None


def get_client() -> Optional[AsyncOpenAI]:
    global _client
    if not settings.ai_enabled:
        return None
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


# Lista de segmentos conhecidos usada tanto pelo fallback de interpretacao
# de busca quanto para geracao de sugestoes.
KNOWN_SEGMENTS = [
    "tributos", "folha de pagamento", "licitacoes", "compras publicas",
    "protocolo", "gestao escolar", "saude publica", "transparencia",
    "contabilidade publica", "patrimonio", "recursos humanos", "obras publicas",
    "assistencia social", "meio ambiente", "frotas", "almoxarifado",
]

UF_LIST = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
]


def keyword_interpret_query(query: str) -> tuple[list[str], Optional[str]]:
    """Fallback sem IA: extrai segmentos e UF por correspondencia de palavras-chave."""
    text = query.lower()
    found_segments = [seg for seg in KNOWN_SEGMENTS if seg in text]

    found_uf = None
    for uf in UF_LIST:
        if re.search(rf"\b{uf.lower()}\b", text):
            found_uf = uf
            break

    return found_segments, found_uf


async def interpret_hunting_query(query: str) -> tuple[list[str], Optional[str]]:
    client = get_client()
    if client is None:
        return keyword_interpret_query(query)

    try:
        prompt = (
            "Extraia da consulta abaixo, em JSON estrito, os campos "
            '{"segments": [...], "uf": "SIGLA_OU_NULL"}. '
            f"Segmentos possiveis: {', '.join(KNOWN_SEGMENTS)}. "
            f"Consulta: {query}"
        )
        resp = await client.chat.completions.create(
            model=settings.OPENAI_TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200,
        )
        content = resp.choices[0].message.content or "{}"
        content = content.strip().strip("`").replace("json\n", "")
        data = json.loads(content)
        return data.get("segments", []), data.get("uf")
    except (OpenAIError, json.JSONDecodeError, Exception):
        return keyword_interpret_query(query)


async def generate_hunting_summary(query: str, companies: list[dict]) -> Optional[str]:
    client = get_client()
    if client is None:
        return None
    try:
        top = companies[:5]
        prompt = (
            f"Resuma em 3 frases objetivas o mercado para a busca de recrutamento: '{query}'. "
            f"As empresas mais aderentes encontradas foram: {json.dumps(top, ensure_ascii=False)}. "
            "Foque em onde estao os profissionais e por que essas empresas se destacam."
        )
        resp = await client.chat.completions.create(
            model=settings.OPENAI_TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=300,
        )
        return resp.choices[0].message.content
    except Exception:
        return None


async def generate_hunting_suggestions(query: str, companies: list[dict]) -> list[str]:
    client = get_client()
    if client is None:
        return [
            "Configure a chave da OpenAI para receber sugestoes de acao personalizadas.",
            "Priorize contato com as empresas no topo do ranking.",
        ]
    try:
        prompt = (
            f"Com base na busca '{query}' e nas empresas ranqueadas {json.dumps(companies[:5], ensure_ascii=False)}, "
            "gere uma lista JSON de ate 4 sugestoes curtas de acao para um recrutador (formato: "
            '{"suggestions": ["...", "..."]})'
        )
        resp = await client.chat.completions.create(
            model=settings.OPENAI_TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=250,
        )
        content = (resp.choices[0].message.content or "{}").strip().strip("`").replace("json\n", "")
        data = json.loads(content)
        return data.get("suggestions", [])
    except Exception:
        return ["Priorize contato com as empresas no topo do ranking."]


async def generate_company_summary(company_data: dict) -> Optional[str]:
    client = get_client()
    if client is None:
        return (
            f"{company_data.get('nome_fantasia')} atua em {company_data.get('uf')}, "
            f"com {company_data.get('municipios_atendidos', 0)} municipios atendidos e "
            f"{company_data.get('contratos_ativos', 0)} contratos ativos. "
            "(Resumo gerado sem IA — configure OPENAI_API_KEY para resumos mais ricos.)"
        )
    try:
        prompt = (
            "Gere um resumo executivo de 4 a 6 frases sobre esta empresa de GovTech para um "
            f"recrutador de talentos: {json.dumps(company_data, ensure_ascii=False, default=str)}"
        )
        resp = await client.chat.completions.create(
            model=settings.OPENAI_TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=350,
        )
        return resp.choices[0].message.content
    except Exception:
        return None


async def generate_report_content(report_type: str, params: dict, context: dict) -> str:
    client = get_client()
    base = f"Relatorio: {report_type}\nParametros: {json.dumps(params, ensure_ascii=False)}\n\n"
    if client is None:
        return base + f"Dados coletados:\n{json.dumps(context, ensure_ascii=False, indent=2, default=str)}"
    try:
        prompt = (
            f"Escreva um relatorio de inteligencia de mercado do tipo '{report_type}' "
            f"com base nestes dados: {json.dumps(context, ensure_ascii=False, default=str)}. "
            "Estruture em secoes com titulos claros, tom executivo, em portugues."
        )
        resp = await client.chat.completions.create(
            model=settings.OPENAI_TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1200,
        )
        return resp.choices[0].message.content or base
    except Exception:
        return base + f"Dados coletados:\n{json.dumps(context, ensure_ascii=False, indent=2, default=str)}"
