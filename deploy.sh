#!/bin/bash

set -e

# ─── Defaults ────────────────────────────────────────────────────────────────
SUDO=""
COMPOSE_FILE="docker-compose.prod.yml"
GIT_BRANCH="dev-prod"

# ─── Flag parsing ─────────────────────────────────────────────────────────────
for arg in "$@"; do
  case $arg in
    --dev)
      COMPOSE_FILE="docker-compose.dev.yml"
      GIT_BRANCH="develop"
      ;;
    --root)
      SUDO="sudo"
      ;;
    --migrate)
      RUN_MIGRATE=true
      ;;
    --seed)
      RUN_SEED=true
      ;;
    --no-cache)
      NO_CACHE="--no-cache"
      ;;
    --help)
      echo "Usage: ./deploy.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --dev        Use dev compose file (docker-compose.dev.yml) and develop branch"
      echo "  --root       Prefix docker commands with sudo"
      echo "  --migrate    Run Alembic migrations after startup"
      echo "  --seed       Seed the database with initial admin user"
      echo "  --no-cache   Build Docker images without cache (default: with cache)"
      echo "  --help       Show this help message"
      exit 0
      ;;
  esac
done

echo "==> Compose file : $COMPOSE_FILE"
echo "==> Git branch   : $GIT_BRANCH"

# ─── 1. Bring down existing containers ───────────────────────────────────────
echo "==> Bringing down existing containers..."
$SUDO docker compose -f "$COMPOSE_FILE" down

# ─── 2. Pull latest code ──────────────────────────────────────────────────────
echo "==> Pulling latest code from $GIT_BRANCH..."
git pull origin "$GIT_BRANCH"

# ─── 3. Build images ─────────────────────────────────────────────────────────
echo "==> Building Docker images${NO_CACHE:+ (no-cache)}..."
$SUDO docker compose -f "$COMPOSE_FILE" build $NO_CACHE

# ─── 4. Prune unused Docker resources ────────────────────────────────────────
echo "==> Pruning unused Docker resources..."
$SUDO docker system prune -f

# ─── 5. Start containers ─────────────────────────────────────────────────────
echo "==> Starting containers..."
$SUDO docker compose -f "$COMPOSE_FILE" up -d

# ─── 6. Wait for backend to be ready ─────────────────────────────────────────
echo "==> Waiting for backend to be ready..."
RETRIES=15
until $SUDO docker compose -f "$COMPOSE_FILE" exec autotest_fastapi_backend curl -sf http://localhost:8000/health > /dev/null 2>&1; do
  RETRIES=$((RETRIES - 1))
  if [ $RETRIES -le 0 ]; then
    echo "    Backend did not become healthy in time. Check logs:"
    $SUDO docker compose -f "$COMPOSE_FILE" logs autotest_fastapi_backend --tail=50
    exit 1
  fi
  echo "    Waiting... ($RETRIES retries left)"
  sleep 5
done
echo "    Backend is ready."

# ─── 7. Run Alembic migrations ────────────────────────────────────────────────
if [ "$RUN_MIGRATE" = true ]; then
  echo "==> Running Alembic migrations..."
  $SUDO docker compose -f "$COMPOSE_FILE" exec autotest_fastapi_backend alembic upgrade head
  echo "    Migrations complete."
fi

# ─── 8. Seed initial admin user ───────────────────────────────────────────────
if [ "$RUN_SEED" = true ]; then
  echo "==> Seeding database..."
  $SUDO docker compose -f "$COMPOSE_FILE" exec autotest_fastapi_backend python seed.py
  echo "    Seeding complete."
fi

echo ""
echo "==> Deployment complete."
$SUDO docker compose -f "$COMPOSE_FILE" ps
