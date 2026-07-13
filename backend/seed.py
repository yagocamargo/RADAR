"""
Popula o banco com dados iniciais:
- 3 usuarios de teste (admin, manager/recruiter, executive)
- Taxonomia de segmentos de produto GovTech
- 14 empresas seed (conforme exigido no criterio de aceite da pagina /empresas)
- Vinculos empresa-segmento
- Contratos publicos de exemplo
- Sinais de mercado de exemplo
- Alertas de exemplo

Execucao: python seed.py  (roda dentro do container backend)
"""
import asyncio
import random
import uuid
from datetime import date, timedelta, datetime, timezone

from slugify import slugify
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.segment import Segment, CompanySegment
from app.models.company import Company
from app.models.contract import Contract, ContractStatus
from app.models.signal import MarketSignal, SignalType
from app.models.alert import Alert, AlertPriority, AlertStatus

SEGMENT_NAMES = [
    "Tributos", "Folha de Pagamento", "Licitacoes", "Compras Publicas",
    "Protocolo", "Gestao Escolar", "Saude Publica", "Transparencia",
    "Contabilidade Publica", "Patrimonio", "Recursos Humanos", "Obras Publicas",
    "Assistencia Social", "Meio Ambiente", "Frotas", "Almoxarifado",
]

COMPANIES_SEED = [
    {"nome_fantasia": "Betha Sistemas", "razao_social": "Betha Sistemas Ltda", "cnpj": "01.526.759/0001-00", "uf": "SC", "cidade": "Criciuma", "segmentos": ["Tributos", "Folha de Pagamento", "Licitacoes", "Contabilidade Publica"], "e_concorrente": False, "e_monitorada": True},
    {"nome_fantasia": "Softplan", "razao_social": "Softplan Planejamento e Sistemas Ltda", "cnpj": "79.240.529/0001-15", "uf": "SC", "cidade": "Florianopolis", "segmentos": ["Licitacoes", "Obras Publicas", "Protocolo"], "e_concorrente": True, "e_monitorada": True},
    {"nome_fantasia": "Governa", "razao_social": "Governa Tecnologia Ltda", "cnpj": "07.443.478/0001-20", "uf": "SC", "cidade": "Chapeco", "segmentos": ["Tributos", "Contabilidade Publica", "Patrimonio"], "e_concorrente": True, "e_monitorada": True},
    {"nome_fantasia": "IPM Sistemas", "razao_social": "IPM Informatica Publica e Municipal Ltda", "cnpj": "82.916.550/0001-73", "uf": "SC", "cidade": "Blumenau", "segmentos": ["Tributos", "Saude Publica", "Gestao Escolar"], "e_concorrente": True, "e_monitorada": True},
    {"nome_fantasia": "Actcon Sistemas", "razao_social": "Actcon Assessoria e Consultoria Ltda", "cnpj": "05.301.615/0001-90", "uf": "SC", "cidade": "Joacaba", "segmentos": ["Contabilidade Publica", "Recursos Humanos"], "e_concorrente": True, "e_monitorada": True},
    {"nome_fantasia": "Publica Software", "razao_social": "Publica Software Ltda", "cnpj": "11.222.333/0001-44", "uf": "PR", "cidade": "Curitiba", "segmentos": ["Compras Publicas", "Licitacoes"], "e_concorrente": True, "e_monitorada": True},
    {"nome_fantasia": "GRP Sistemas", "razao_social": "GRP Tecnologia da Informacao Ltda", "cnpj": "22.333.444/0001-55", "uf": "RS", "cidade": "Porto Alegre", "segmentos": ["Frotas", "Almoxarifado", "Patrimonio"], "e_concorrente": True, "e_monitorada": True},
    {"nome_fantasia": "Elotech", "razao_social": "Elotech Sistemas Ltda", "cnpj": "33.444.555/0001-66", "uf": "PR", "cidade": "Toledo", "segmentos": ["Tributos", "Contabilidade Publica", "Folha de Pagamento"], "e_concorrente": True, "e_monitorada": True},
    {"nome_fantasia": "Sispro Publico", "razao_social": "Sispro Sistemas Ltda", "cnpj": "44.555.666/0001-77", "uf": "SP", "cidade": "Sao Paulo", "segmentos": ["Saude Publica", "Assistencia Social"], "e_concorrente": True, "e_monitorada": True},
    {"nome_fantasia": "CSU GovTech", "razao_social": "CSU GovTech Solucoes Ltda", "cnpj": "55.666.777/0001-88", "uf": "SP", "cidade": "Barueri", "segmentos": ["Transparencia", "Compras Publicas"], "e_concorrente": True, "e_monitorada": True},
    {"nome_fantasia": "Meta Governo", "razao_social": "Meta Governo Sistemas Ltda", "cnpj": "66.777.888/0001-99", "uf": "MG", "cidade": "Belo Horizonte", "segmentos": ["Gestao Escolar", "Recursos Humanos"], "e_concorrente": True, "e_monitorada": True},
    {"nome_fantasia": "Prodata Mobilidade Publica", "razao_social": "Prodata Sistemas Ltda", "cnpj": "77.888.999/0001-00", "uf": "GO", "cidade": "Goiania", "segmentos": ["Frotas", "Obras Publicas"], "e_concorrente": True, "e_monitorada": True},
    {"nome_fantasia": "Nexo Municipal", "razao_social": "Nexo Municipal Tecnologia Ltda", "cnpj": "88.999.000/0001-11", "uf": "BA", "cidade": "Salvador", "segmentos": ["Meio Ambiente", "Protocolo"], "e_concorrente": True, "e_monitorada": True},
    {"nome_fantasia": "CidadeSmart", "razao_social": "CidadeSmart Solucoes Publicas Ltda", "cnpj": "99.000.111/0001-22", "uf": "CE", "cidade": "Fortaleza", "segmentos": ["Transparencia", "Licitacoes", "Compras Publicas"], "e_concorrente": True, "e_monitorada": True},
]

TEST_USERS = [
    {"email": "admin@radar.betha.com.br", "password": "Radar@2026", "name": "Admin Radar", "role": UserRole.admin},
    {"email": "recrutador@radar.betha.com.br", "password": "Radar@2026", "name": "Recrutador Teste", "role": UserRole.recruiter},
    {"email": "executivo@radar.betha.com.br", "password": "Radar@2026", "name": "Executivo Teste", "role": UserRole.executive},
]


async def seed_users(db):
    users = {}
    for u in TEST_USERS:
        result = await db.execute(select(User).where(User.email == u["email"]))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                name=u["name"],
                role=u["role"],
            )
            db.add(user)
            await db.flush()
        users[u["email"]] = user
    await db.commit()
    return users


async def seed_segments(db):
    segments = {}
    for name in SEGMENT_NAMES:
        slug = slugify(name)
        result = await db.execute(select(Segment).where(Segment.slug == slug))
        segment = result.scalar_one_or_none()
        if not segment:
            segment = Segment(name=name, slug=slug, description=f"Solucoes de software para {name.lower()}")
            db.add(segment)
            await db.flush()
        segments[name] = segment
    await db.commit()
    return segments


async def seed_companies(db, segments):
    companies = {}
    for c in COMPANIES_SEED:
        slug = slugify(c["nome_fantasia"])
        result = await db.execute(select(Company).where(Company.slug == slug))
        company = result.scalar_one_or_none()
        if not company:
            company = Company(
                cnpj=c["cnpj"],
                razao_social=c["razao_social"],
                nome_fantasia=c["nome_fantasia"],
                slug=slug,
                uf=c["uf"],
                cidade=c["cidade"],
                endereco=f"Centro, {c['cidade']} - {c['uf']}",
                municipios_atendidos=random.randint(20, 450),
                contratos_ativos=random.randint(3, 60),
                valor_total_contratos=round(random.uniform(200_000, 15_000_000), 2),
                vagas_abertas_30d=random.randint(0, 18),
                vagas_abertas_90d=random.randint(5, 40),
                relevance_score=round(random.uniform(0.3, 0.98), 3),
                growth_signal=round(random.uniform(0.1, 0.95), 3),
                profile_completeness=round(random.uniform(0.4, 1.0), 3),
                e_concorrente=c["e_concorrente"],
                e_monitorada=c["e_monitorada"],
                e_verificada=random.choice([True, False]),
            )
            db.add(company)
            await db.flush()

            for seg_name in c["segmentos"]:
                link = CompanySegment(
                    company_id=company.id,
                    segment_id=segments[seg_name].id,
                    confidence_score=round(random.uniform(0.6, 0.99), 3),
                )
                db.add(link)

        companies[c["nome_fantasia"]] = company
    await db.commit()
    return companies


async def seed_contracts(db, companies):
    orgaos = ["Prefeitura Municipal", "Camara Municipal", "Governo do Estado", "Secretaria de Fazenda", "Secretaria de Saude"]
    objetos = [
        "Licenciamento de sistema de gestao tributaria municipal",
        "Contratacao de sistema integrado de folha de pagamento",
        "Fornecimento de software de licitacoes e compras publicas",
        "Sistema de gestao escolar e matricula digital",
        "Plataforma de transparencia e portal do cidadao",
    ]

    for company in companies.values():
        result = await db.execute(select(Contract).where(Contract.company_id == company.id))
        if result.scalars().first():
            continue
        for _ in range(random.randint(2, 6)):
            start = date.today() - timedelta(days=random.randint(10, 700))
            contract = Contract(
                company_id=company.id,
                orgao_contratante=f"{random.choice(orgaos)} de {company.cidade}",
                municipio=company.cidade,
                uf=company.uf,
                objeto=random.choice(objetos),
                valor=round(random.uniform(50_000, 2_000_000), 2),
                data_inicio=start,
                data_fim=start + timedelta(days=365 * random.choice([1, 2, 3])),
                status=ContractStatus.ativo,
            )
            db.add(contract)
    await db.commit()


async def seed_signals(db, companies):
    signal_titles = {
        SignalType.vaga_aberta: "Nova vaga aberta: Analista de Implantacao",
        SignalType.novo_contrato: "Novo contrato publico assinado",
        SignalType.expansao: "Expansao de atuacao para novos municipios",
        SignalType.publicacao_diario_oficial: "Publicacao em Diario Oficial referente a licitacao",
        SignalType.noticia: "Empresa e destaque em noticia do setor GovTech",
    }

    for company in companies.values():
        result = await db.execute(select(MarketSignal).where(MarketSignal.company_id == company.id))
        if result.scalars().first():
            continue
        for _ in range(random.randint(3, 8)):
            signal_type = random.choice(list(SignalType))
            days_ago = random.randint(0, 365)
            signal = MarketSignal(
                company_id=company.id,
                type=signal_type,
                title=f"{signal_titles[signal_type]} — {company.nome_fantasia}",
                description="Sinal gerado automaticamente pelo agente de monitoramento (dado seed).",
                uf=company.uf,
                signal_date=date.today() - timedelta(days=days_ago),
            )
            db.add(signal)
    await db.commit()


async def seed_alerts(db, users, companies):
    recruiter = users.get("recrutador@radar.betha.com.br")
    if not recruiter:
        return

    result = await db.execute(select(Alert).where(Alert.user_id == recruiter.id))
    if result.scalars().first():
        return

    sample_companies = list(companies.values())[:5]
    priorities = [AlertPriority.critica, AlertPriority.alta, AlertPriority.media, AlertPriority.baixa]

    for i, company in enumerate(sample_companies):
        alert = Alert(
            user_id=recruiter.id,
            title=f"Sinal relevante detectado: {company.nome_fantasia}",
            body=f"A empresa {company.nome_fantasia} apresentou aumento de atividade em {company.uf}.",
            type="novo_contrato" if i % 2 == 0 else "vaga_aberta",
            priority=priorities[i % len(priorities)],
            status=AlertStatus.nao_lido,
            company_id=company.id,
        )
        db.add(alert)
    await db.commit()


async def main():
    async with AsyncSessionLocal() as db:
        print("Criando usuarios de teste...")
        users = await seed_users(db)

        print("Criando taxonomia de segmentos...")
        segments = await seed_segments(db)

        print("Criando 14 empresas seed...")
        companies = await seed_companies(db, segments)

        print("Criando contratos publicos de exemplo...")
        await seed_contracts(db, companies)

        print("Criando sinais de mercado de exemplo...")
        await seed_signals(db, companies)

        print("Criando alertas de exemplo...")
        await seed_alerts(db, users, companies)

    print("\nSeed concluido com sucesso.")
    print("\nCredenciais de teste:")
    for u in TEST_USERS:
        print(f"  {u['email']} / {u['password']} ({u['role'].value})")


if __name__ == "__main__":
    asyncio.run(main())
