#!/bin/sh
set -e

# Composed here (not in docker-compose.yml's YAML) so the credentials can be
# percent-encoded — a POSTGRES_PASSWORD with a reserved character like @ or :
# would otherwise land in the wrong place in the connection string.
export DATABASE_URL=$(python3 -c "
import os, urllib.parse as u
user = u.quote(os.environ.get('POSTGRES_USER', 'crm'), safe='')
password = u.quote(os.environ.get('POSTGRES_PASSWORD', 'crm'), safe='')
db = os.environ.get('POSTGRES_DB', 'crm')
print(f'postgresql+psycopg://{user}:{password}@db:5432/{db}')
")

alembic upgrade head
exec uvicorn crm.main:app --host 0.0.0.0 --port 8000
