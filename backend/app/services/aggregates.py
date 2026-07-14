"""
Recalculo dos campos agregados de Company a partir da fonte de verdade real:
a tabela `contracts`.

Antes desta correcao, `Company.contratos_ativos` e `Company.municipios_atendidos`
eram apenas numeros gravados manualmente (aleatorios no seed) e nunca eram
atualizados a partir dos contratos de fato coletados/armazenados. Isso fazia
os numeros exibidos na interface nao corresponderem a nenhuma fonte real.

A partir de agora:
  - contratos_ativos      = COUNT(*) de contracts com status = 'ativo'
  - municipios_atendidos   = COUNT(DISTINCT municipio) entre todos os contratos
                             da empresa (independente do status, pois um
                             municipio ja atendido nao deixa de ter sido
                             atendido so porque um contrato especifico encerrou)
  - valor_total_contratos  = SUM(valor) de todos os contratos da empresa

Estes valores devem ser recalculados sempre que novos contratos forem
inseridos (agente de coleta do PNCP) e periodicamente pelo agente de
monitoramento, para nao ficarem desatualizados.
"""
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.contract import Contract, ContractStatus


async def recompute_company_aggregates(db: AsyncSession, company_id: uuid.UUID) -> None:
    """Recalcula os agregados de UMA empresa. Nao da commit — quem chama decide quando salvar."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        return

    contratos_ativos = (
        await db.execute(
            select(func.count(Contract.id)).where(
                Contract.company_id == company_id,
                Contract.status == ContractStatus.ativo,
            )
        )
    ).scalar_one()

    municipios_atendidos = (
        await db.execute(
            select(func.count(func.distinct(Contract.municipio))).where(
                Contract.company_id == company_id,
            )
        )
    ).scalar_one()

    valor_total_contratos = (
        await db.execute(
            select(func.coalesce(func.sum(Contract.valor), 0)).where(
                Contract.company_id == company_id,
            )
        )
    ).scalar_one()

    company.contratos_ativos = contratos_ativos
    company.municipios_atendidos = municipios_atendidos
    company.valor_total_contratos = valor_total_contratos


async def recompute_all_aggregates(db: AsyncSession) -> int:
    """Recalcula os agregados de TODAS as empresas. Nao da commit. Retorna quantas foram processadas."""
    result = await db.execute(select(Company.id))
    company_ids = [row[0] for row in result.all()]

    for company_id in company_ids:
        await recompute_company_aggregates(db, company_id)

    return len(company_ids)
