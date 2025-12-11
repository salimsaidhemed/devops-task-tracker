# Backend – DevOps Task Tracker

Flask-based REST API that manages simple tasks and talks to Postgres + Redis.

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
export FLASK_ENV=dev
export DATABASE_URL="postgresql://user:pass@localhost:5432/tasks"
export REDIS_URL="redis://localhost:6379/0"

python -m src.app   # (we can add a CLI entry later)