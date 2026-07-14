#!/bin/bash
# Este script roda automaticamente toda vez que o Codespace inicia.
# Ele descobre as URLs publicas do proprio Codespace e configura o .env
# de acordo, para que o frontend consiga falar com o backend sem erro
# de CORS ou de "localhost" incorreto.
set -e

cd /workspaces/RADAR || cd "$(dirname "$0")/.."

# Cria o .env a partir do exemplo, se ainda nao existir
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Arquivo .env criado a partir do .env.example"
fi

# Descobre o dominio de forwarding de portas do Codespace
# (normalmente "app.github.dev")
DOMAIN="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"

if [ -n "$CODESPACE_NAME" ]; then
  BACKEND_URL="https://${CODESPACE_NAME}-8000.${DOMAIN}"
  FRONTEND_URL="https://${CODESPACE_NAME}-3000.${DOMAIN}"

  echo "Backend detectado em:  $BACKEND_URL"
  echo "Frontend detectado em: $FRONTEND_URL"

  # Atualiza (ou adiciona) NEXT_PUBLIC_API_URL no .env
  if grep -q "^NEXT_PUBLIC_API_URL=" .env; then
    sed -i "s#^NEXT_PUBLIC_API_URL=.*#NEXT_PUBLIC_API_URL=${BACKEND_URL}#" .env
  else
    echo "NEXT_PUBLIC_API_URL=${BACKEND_URL}" >> .env
  fi

  # Atualiza (ou adiciona) CORS_ORIGINS no .env, incluindo a URL do frontend
  CORS_JSON="[\"http://localhost:3000\",\"http://localhost:80\",\"http://localhost\",\"${FRONTEND_URL}\"]"
  if grep -q "^CORS_ORIGINS=" .env; then
    sed -i "s#^CORS_ORIGINS=.*#CORS_ORIGINS=${CORS_JSON}#" .env
  else
    echo "CORS_ORIGINS=${CORS_JSON}" >> .env
  fi
else
  echo "Aviso: CODESPACE_NAME nao encontrado — rodando fora de um Codespace? Mantendo .env como esta."
fi

# Da permissao de execucao aos entrypoints do Celery (necessario apos
# clonar/copiar o projeto em ambientes que nao preservam permissoes)
chmod +x backend/celery_worker_entrypoint.sh backend/celery_beat_entrypoint.sh 2>/dev/null || true

echo "Subindo postgres e redis..."
docker-compose up -d postgres redis

echo "Aguardando o banco ficar pronto..."
for i in $(seq 1 20); do
  if docker-compose exec -T postgres pg_isready -U radar >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Rodando migrations..."
docker-compose run --rm backend alembic upgrade head

# Roda o seed apenas na primeira vez (usa um arquivo marcador para nao duplicar dados)
if [ ! -f .seeded ]; then
  echo "Rodando seed inicial (primeira vez)..."
  docker-compose run --rm backend python seed.py
  touch .seeded
else
  echo "Seed ja foi executado anteriormente — pulando."
fi

echo "Buildando frontend com a URL correta da API..."
docker-compose build frontend

echo "Subindo todos os servicos..."
docker-compose up -d

echo ""
echo "=========================================="
echo " Radar esta no ar!"
echo " Frontend: ${FRONTEND_URL:-http://localhost:3000}"
echo " API docs: ${BACKEND_URL:-http://localhost:8000}/api/docs"
echo "=========================================="
