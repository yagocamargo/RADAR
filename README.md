# Radar

**Plataforma de Inteligencia de Mercado para Talent Acquisition — Betha Sistemas**

O Radar responde uma pergunta simples: **"Onde estao os melhores profissionais para essa vaga?"**

Ele monitora empresas do ecossistema de software para gestao publica brasileira, coleta contratos
publicos do PNCP, identifica segmentos e regioes de atuacao, detecta sinais de crescimento e expansao,
e entrega essa inteligencia ao recrutador via uma interface web moderna.

> ⚠️ O Radar coleta dados de **empresas (pessoas juridicas)**, nunca dados pessoais de candidatos.

---

## Sumario

- [Arquitetura](#arquitetura)
- [Stack tecnologica](#stack-tecnologica)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Como subir o sistema (passo a passo)](#como-subir-o-sistema-passo-a-passo)
- [Credenciais de teste](#credenciais-de-teste)
- [Publicar no GitHub](#publicar-no-github)
- [Publicar uma versao web (hospedagem)](#publicar-uma-versao-web-hospedagem)
- [Documentacao da API](#documentacao-da-api)
- [Logica de negocio critica](#logica-de-negocio-critica)
- [Checklist de funcionalidades](#checklist-de-funcionalidades)
- [Roadmap de evolucao](#roadmap-de-evolucao)
- [Suporte e duvidas](#suporte-e-duvidas)

---

## Arquitetura

O sistema e composto por **6 servicos** em containers Docker separados:

```
                         ┌─────────────┐
                         │   Nginx     │  :80
                         │ (proxy)     │
                         └──────┬──────┘
                    ┌───────────┴────────────┐
                    ▼                        ▼
            ┌───────────────┐        ┌───────────────┐
            │   Frontend    │        │    Backend    │
            │  Next.js :3000│        │ FastAPI :8000 │
            └───────────────┘        └───────┬───────┘
                                              │
                          ┌───────────────────┼───────────────────┐
                          ▼                   ▼                   ▼
                  ┌──────────────┐   ┌────────────────┐   ┌──────────────┐
                  │ PostgreSQL   │   │     Redis      │   │Celery Worker │
                  │   :5432      │   │     :6379      │   │  + Beat      │
                  └──────────────┘   └────────────────┘   └──────────────┘
```

**Fluxo de uma requisicao:**
1. Usuario acessa o navegador na porta 80 (ou 443 em producao)
2. Nginx recebe a requisicao
3. Se e uma rota `/api/*`, encaminha para o backend na porta 8000
4. Se e qualquer outra rota, encaminha para o frontend na porta 3000
5. O backend acessa PostgreSQL e Redis conforme necessario
6. Para tarefas pesadas (gerar relatorio, coletar dados), o backend enfileira no Redis
7. O Celery Worker pega a tarefa da fila e executa em background
8. O Celery Beat dispara automaticamente as coletas periodicas (monitoramento diario, enriquecimento semanal, coleta PNCP diaria)

O backend segue **arquitetura em camadas**, separando:
- `api/` — camada de apresentacao (routers FastAPI, dependencias de auth)
- `services/` — logica de aplicacao e integracoes externas (scoring, IA, PNCP, CNPJ)
- `models/` — camada de dominio (entidades SQLAlchemy)
- `schemas/` — contratos de entrada/saida (Pydantic)
- `tasks/` — processos assincronos (Celery)

---

## Stack tecnologica

| Camada          | Tecnologia |
|-----------------|------------|
| Frontend        | React 18, Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts, lucide-react |
| Backend         | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| Banco de dados  | PostgreSQL 16 |
| Cache / fila    | Redis 7 |
| Processamento assincrono | Celery (worker + beat) |
| Autenticacao    | JWT (access + refresh) |
| IA              | OpenAI API (`gpt-4o` para texto, `text-embedding-3-small` para embeddings) |
| Migrations      | Alembic |
| Proxy reverso   | Nginx |
| Orquestracao    | Docker Compose |

---

## Estrutura de pastas

```
radar/
├── backend/
│   ├── app/
│   │   ├── core/          # config.py, security.py, celery_app.py
│   │   ├── db/            # base_class.py, session.py
│   │   ├── models/        # entidades SQLAlchemy (User, Company, Contract, ...)
│   │   ├── schemas/       # contratos Pydantic
│   │   ├── api/
│   │   │   ├── deps.py    # autenticacao e RBAC
│   │   │   └── v1/        # routers: auth, dashboard, hunting, empresas, mercado, alertas, relatorios, admin
│   │   ├── services/      # scoring.py, ai_service.py, pncp_service.py, cnpj_service.py
│   │   ├── tasks/         # agents.py, reports.py (Celery)
│   │   └── main.py
│   ├── alembic/           # migrations
│   ├── seed.py            # popula banco com dados iniciais
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                        # App Router do Next.js
│   │   ├── auth/page.tsx           # Pagina 1: Login
│   │   ├── dashboard/page.tsx      # Pagina 2: Dashboard
│   │   ├── hunting/page.tsx        # Pagina 3: Hunting / Busca
│   │   ├── empresas/page.tsx       # Pagina 4: Ecossistema
│   │   ├── empresas/[slug]/page.tsx# Pagina 5: Ficha de Empresa
│   │   ├── mercado/page.tsx        # Pagina 6: Mercado
│   │   ├── alertas/page.tsx        # Pagina 7: Alertas
│   │   ├── relatorios/page.tsx     # Pagina 8: Relatorios
│   │   └── admin/page.tsx          # Pagina 9: Admin
│   ├── components/                 # Sidebar, ProtectedShell, MetricCard
│   ├── lib/                        # api.ts, auth-context.tsx, theme-context.tsx
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Como subir o sistema (passo a passo)

### Pre-requisitos

- Docker Desktop instalado e rodando ([docker.com](https://www.docker.com))
- Git
- Minimo 8GB de RAM disponivel para o Docker

### Passo 1 — Configurar variaveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` e preencha pelo menos:
- `SECRET_KEY` e `JWT_SECRET_KEY` (strings aleatorias de 32+ caracteres)
- `OPENAI_API_KEY` (opcional — sem ela, os recursos de IA ficam desabilitados, mas o resto do sistema funciona normalmente)

> ⚠️ Nunca commite o arquivo `.env` no GitHub.

### Passo 2 — Subir banco de dados e Redis

```bash
docker-compose up -d postgres redis
```

Aguarde ~20 segundos para os servicos inicializarem.

### Passo 3 — Criar o banco de dados (migrations)

```bash
docker-compose run --rm backend alembic upgrade head
```

Isso cria todas as tabelas.

> ⚠️ Se aparecer erro `DuplicateObjectError`, o banco tem dados de uma tentativa anterior.
> Execute `docker-compose down -v` para apagar tudo e comece o passo 2 novamente.

### Passo 4 — Popular dados iniciais (seed)

```bash
docker-compose run --rm backend python seed.py
```

Isso cria os 3 usuarios de teste, a taxonomia de segmentos, as **14 empresas seed**, contratos,
sinais de mercado e alertas de exemplo.

### Passo 5 — Subir todos os servicos

```bash
docker-compose up -d
```

Aguarde 2–3 minutos na primeira vez (build das imagens).

### Passo 6 — Verificar que esta funcionando

```bash
curl http://localhost:8000/health
```

Deve retornar: `{"status":"healthy","app":"Radar"}`

### Passo 7 — Acessar o sistema

- **Via Nginx (recomendado):** http://localhost
- **Frontend direto:** http://localhost:3000
- **API direta:** http://localhost:8000
- **Documentacao interativa da API:** http://localhost:8000/api/docs

---

## Credenciais de teste

| Perfil     | E-mail                            | Senha        |
|------------|------------------------------------|--------------|
| admin      | admin@radar.betha.com.br           | Radar@2026   |
| recruiter  | recrutador@radar.betha.com.br      | Radar@2026   |
| executive  | executivo@radar.betha.com.br       | Radar@2026   |

> ⚠️ Troque as senhas no primeiro acesso em producao.

---

## Publicar no GitHub

O projeto ja inclui `.gitignore` (exclui `.env`, `node_modules`, `__pycache__`, etc.) e um
workflow de CI em `.github/workflows/ci.yml`.

### Passo 1 — Criar o repositorio

Va em [github.com/new](https://github.com/new), crie um repositorio vazio (ex.: `radar`),
**sem** inicializar com README/gitignore/license (o projeto ja tem os seus).

### Passo 2 — Inicializar o git localmente e subir

```bash
cd radar
git init
git add .
git commit -m "Radar: versao inicial"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/radar.git
git push -u origin main
```

> ⚠️ Confirme que o arquivo `.env` (com suas chaves reais) **nao** foi commitado —
> ele deve aparecer como ignorado (`git status` nao deve lista-lo).

### O que o CI (GitHub Actions) faz a cada push

O workflow `.github/workflows/ci.yml` roda automaticamente em todo `push` e `pull_request`
e tem 3 jobs:

| Job | O que valida |
|-----|--------------|
| `backend` | Instala dependencias Python, checa sintaxe de todos os modulos, importa a aplicacao FastAPI (garante que ela sobe sem erro) e builda a imagem Docker do backend |
| `frontend` | Instala dependencias Node, roda `npm run build` (Next.js) e builda a imagem Docker do frontend |
| `compose-config` | Valida que o `docker-compose.yml` esta sintaticamente correto (`docker compose config`) |

O CI **nao** sobe banco de dados nem executa testes de integracao (isso esta no roadmap —
veja [Checklist de funcionalidades](#checklist-de-funcionalidades)). Ele funciona como uma
rede de seguranca: se alguem quebrar o build do backend, do frontend, ou o compose ficar
invalido, o Pull Request mostra falha antes do merge.

Voce pode acompanhar as execucoes na aba **Actions** do repositorio no GitHub.

---

## Publicar uma versao web (hospedagem)

Este pacote roda localmente via Docker Compose. Para publicar em uma URL publica acessivel
via HTTPS (ex.: para times remotos), algumas opcoes comuns:

- **VPS proprio** (ex.: DigitalOcean, Hetzner, AWS EC2): instale Docker no servidor, copie o
  projeto, rode `docker-compose up -d` e configure um certificado TLS (ex.: Certbot + Nginx).
- **Plataformas PaaS com suporte a Docker Compose / containers** (ex.: Railway, Render, Fly.io):
  cada uma tem seu proprio fluxo de deploy a partir de um repositorio Git — normalmente exigem
  adaptar o `docker-compose.yml` em servicos individuais e configurar variaveis de ambiente
  pelo painel da plataforma.
- **GitHub**: o codigo pode ser hospedado em um repositorio (ex.: `github.com/SEU_USUARIO/radar`)
  e a partir dele conectado a qualquer uma das opcoes acima para deploy continuo.

Recomenda-se, em qualquer opcao escolhida, habilitar HTTPS antes de expor o sistema publicamente
e revisar `CORS_ORIGINS` em `backend/app/core/config.py` para refletir o dominio real.

---

## Documentacao da API

A documentacao OpenAPI e gerada automaticamente pelo FastAPI e fica disponivel em:

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- JSON OpenAPI bruto: `http://localhost:8000/api/openapi.json`

### Principais endpoints

| Metodo | Rota                                   | Descricao |
|--------|-----------------------------------------|-----------|
| POST   | `/api/v1/auth/login`                    | Login (retorna access + refresh token) |
| POST   | `/api/v1/auth/refresh`                  | Renova o access token |
| GET    | `/api/v1/auth/me`                       | Dados do usuario logado |
| GET    | `/api/v1/dashboard`                     | Metricas e feed do dashboard |
| POST   | `/api/v1/hunting`                       | Busca de hunting (ranking de empresas) |
| POST   | `/api/v1/hunting/salvar`                | Salva consulta e ativa monitoramento |
| GET    | `/api/v1/hunting/historico`             | Historico de buscas do usuario |
| GET    | `/api/v1/empresas`                      | Lista paginada de empresas |
| GET    | `/api/v1/empresas/{slug}`               | Ficha de uma empresa |
| GET    | `/api/v1/empresas/{slug}/timeline`      | Linha do tempo de sinais |
| GET    | `/api/v1/empresas/{slug}/contratos`     | Contratos da empresa |
| GET    | `/api/v1/empresas/{slug}/concorrentes`  | Concorrentes por segmento |
| POST   | `/api/v1/empresas/{slug}/gerar-resumo`  | (Re)gera resumo de IA |
| GET    | `/api/v1/mercado`                       | Painel executivo de mercado |
| GET    | `/api/v1/alertas`                       | Lista de alertas do usuario |
| PATCH  | `/api/v1/alertas/{id}/marcar-lido`      | Marca alerta como lido |
| POST   | `/api/v1/alertas/marcar-todos-lidos`    | Marca todos como lidos |
| GET    | `/api/v1/relatorios`                    | Lista relatorios do usuario |
| POST   | `/api/v1/relatorios`                    | Solicita novo relatorio (assincrono) |
| GET    | `/api/v1/admin/stats`                   | Estatisticas do sistema (admin/manager) |
| POST   | `/api/v1/admin/agentes/*`               | Dispara agentes manualmente (admin/manager) |
| POST   | `/api/v1/admin/cache/limpar`            | Limpa o cache Redis (admin/manager) |

---

## Logica de negocio critica

### Ranking de hunting

Quando o recrutador faz uma busca, o sistema ranqueia as empresas por aderencia usando a formula:

- **30%** relevancia geral da empresa (`relevance_score`)
- **30%** sobreposicao de segmentos buscados
- **20%** match geografico (a empresa esta no estado buscado?)
- **12%** sinal de crescimento (a empresa esta contratando e expandindo?)
- **8%** vagas abertas nos ultimos 30 dias

Implementada em `backend/app/services/scoring.py`.

> ⚠️ Esta formula e uma decisao de produto e nao deve ser alterada sem aprovacao.

### Autenticacao e seguranca

- Todo endpoint da API, exceto `/health` e `/api/v1/auth/login`, exige token JWT valido
- O token de acesso expira em **60 minutos**
- O token de refresh expira em **30 dias**
- Ao expirar, o frontend usa o refresh token automaticamente para obter novo access token
  (ver `frontend/lib/api.ts`)
- Se o refresh tambem expirar, o usuario e redirecionado para o login

### Agentes de coleta (Celery)

| Agente | Frequencia (Beat) | O que faz |
|--------|--------------------|-----------|
| Enriquecimento | Semanal | Atualiza dados cadastrais via CNPJ (ReceitaWS / BrasilAPI) |
| Monitoramento | Diaria | Recalcula `growth_signal` das empresas |
| Alertas | Sob demanda | Gera alertas a partir de sinais recentes e monitoramentos ativos |
| Coleta PNCP | Diaria | Busca novos contratos publicos no PNCP |

Todos podem ser disparados manualmente pela pagina `/admin`.

### Integracoes externas

| Integracao | Uso | Observacao |
|------------|-----|------------|
| OpenAI API | Resumos de empresa, interpretacao de busca, texto de alertas/relatorios | Sem chave configurada, cai em fallback por palavras-chave — o resto do sistema continua funcionando |
| PNCP | Coleta de contratos publicos | Sem autenticacao; respeita delay de 2s entre chamadas |
| ReceitaWS / BrasilAPI | Enriquecimento cadastral por CNPJ | Sem autenticacao; ReceitaWS como primario, BrasilAPI como fallback |

---

## Checklist de funcionalidades

### Paginas
- [x] Login (`/auth`) com mostrar/ocultar senha e mensagem de erro
- [x] Dashboard (`/dashboard`) com 4 KPIs, top 6 empresas, feed de sinais, grafico de segmentos
- [x] Hunting (`/hunting`) com busca em linguagem natural, filtros, ranking, mapa regional, tendencia, IA, historico
- [x] Ecossistema (`/empresas`) com busca, filtros, cards, paginacao (20/pagina)
- [x] Ficha de Empresa (`/empresas/[slug]`) com 3 abas (Visao geral, Linha do tempo, Concorrentes)
- [x] Mercado (`/mercado`) com KPIs, graficos por segmento/regiao, ranking, sinais recentes
- [x] Alertas (`/alertas`) com filtros, marcar lido/todos, indicador de prioridade
- [x] Relatorios (`/relatorios`) com solicitacao, status assincrono e polling a cada 5s
- [x] Admin (`/admin`) restrito a admin/manager, com stats, disparo de agentes e info do Redis

### Navegacao e seguranca
- [x] Sidebar fixa com badge de alertas nao lidos
- [x] Rotas protegidas (redireciona para `/auth` se nao autenticado)
- [x] Tema claro/escuro
- [x] JWT com access (60min) + refresh (30 dias) e renovacao automatica

### Backend
- [x] 9 entidades de dominio modeladas (User, Company, Segment, Contract, MarketSignal, Alert, HuntingQuery, Monitoring, Report)
- [x] Formula de ranking de hunting conforme especificacao
- [x] Fallback funcional de IA sem chave OpenAI
- [x] Integracao PNCP com rate limit respeitado
- [x] Integracao CNPJ com fallback (ReceitaWS → BrasilAPI)
- [x] 4 agentes Celery + agendamento via Beat
- [x] Migration inicial completa
- [x] Seed com 14 empresas, usuarios, contratos, sinais e alertas
- [x] Documentacao OpenAPI automatica

### Infraestrutura
- [x] Docker Compose com 6 servicos
- [x] Nginx como proxy reverso
- [x] `.env.example` documentado
- [x] `.gitignore`

### Pendente (nao incluido nesta entrega)
- [ ] Testes automatizados (unitarios e de integracao)
- [ ] CI/CD (ex.: GitHub Actions)
- [ ] Deploy publico com HTTPS configurado
- [ ] Rate limiting na API
- [ ] Paginacao/filtros avancados em Alertas e Relatorios
- [ ] Exportacao de relatorios em PDF/Excel

---

## Roadmap de evolucao

**Curto prazo**
- Testes automatizados (pytest no backend, Playwright/Cypress no frontend)
- CI/CD com GitHub Actions (lint, testes, build de imagens)
- Rate limiting e throttling na API
- Exportacao de relatorios em PDF e Excel

**Medio prazo**
- Embeddings de vagas/empresas (`text-embedding-3-small`) para busca semantica no Hunting
- Enriquecimento automatico de segmentos via classificacao por IA (hoje e por keyword + confidence_score manual)
- Notificacoes por e-mail/Slack quando um monitoramento detecta sinal relevante
- Webhooks de saida para integracao com ATS (ex.: Gupy, Greenhouse)
- Historico de variacao de scores por empresa (serie temporal) para grafico de tendencia individual

**Longo prazo**
- Multi-tenancy (suportar mais de uma organizacao usando o Radar)
- App mobile (React Native) reaproveitando a mesma API
- Modelo de scoring configuravel via painel Admin (hoje os pesos sao fixos no codigo)
- Enriquecimento de dados via scraping de vagas publicas (com throttling e cache agressivo)

---

## Suporte e duvidas

Duvidas sobre **comportamento esperado do produto** (o que o sistema deve fazer) devem ser
direcionadas ao responsavel de produto do projeto. Duvidas **tecnicas de implementacao** podem
ser resolvidas consultando a documentacao das tecnologias listadas na secao
[Stack tecnologica](#stack-tecnologica).

---

Radar · Betha Sistemas · 2026
