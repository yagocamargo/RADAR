"""
Logica de ranking de hunting.

⚠️ Formula de negocio definida no documento de escopo do Radar. Nao alterar
sem aprovacao de produto:
  - 30% relevancia geral da empresa (relevance_score)
  - 30% sobreposicao de segmentos buscados
  - 20% match geografico (UF)
  - 12% sinal de crescimento (growth_signal)
  - 8%  vagas abertas nos ultimos 30 dias (normalizado)
"""
from app.models.company import Company

W_RELEVANCE = 0.30
W_SEGMENT_OVERLAP = 0.30
W_GEO_MATCH = 0.20
W_GROWTH = 0.12
W_JOBS_30D = 0.08

# Normalizador de vagas: consideramos 20 vagas/30d como "cheio" (score 1.0)
JOBS_30D_NORMALIZER = 20.0


def segment_overlap_score(company_segment_slugs: set[str], searched_segment_slugs: set[str]) -> float:
    if not searched_segment_slugs:
        return 0.0
    matched = company_segment_slugs & searched_segment_slugs
    return len(matched) / len(searched_segment_slugs)


def geo_match_score(company_uf: str, searched_uf: str | None) -> float:
    if not searched_uf:
        return 0.0
    return 1.0 if company_uf.upper() == searched_uf.upper() else 0.0


def jobs_score(vagas_abertas_30d: int) -> float:
    return min(vagas_abertas_30d / JOBS_30D_NORMALIZER, 1.0)


def compute_hunting_score(
    company: Company,
    company_segment_slugs: set[str],
    searched_segment_slugs: set[str],
    searched_uf: str | None,
) -> float:
    relevance = float(company.relevance_score or 0)
    overlap = segment_overlap_score(company_segment_slugs, searched_segment_slugs)
    geo = geo_match_score(company.uf, searched_uf)
    growth = float(company.growth_signal or 0)
    jobs = jobs_score(company.vagas_abertas_30d or 0)

    score = (
        relevance * W_RELEVANCE
        + overlap * W_SEGMENT_OVERLAP
        + geo * W_GEO_MATCH
        + growth * W_GROWTH
        + jobs * W_JOBS_30D
    )
    return round(min(max(score, 0.0), 1.0), 4)
