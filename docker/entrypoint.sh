#!/bin/sh
set -e

# Composed here (not in docker-compose.yml's YAML, which can't encode) so the
# credentials are safe regardless of content, using SQLAlchemy's own URL
# builder rather than hand-rolled quoting. A plain `VAR=$(cmd)` assignment —
# not combined with `export` on the same line — is required for `set -e` to
# actually abort if this fails; `export VAR=$(cmd)` swallows the command
# substitution's exit status.
DATABASE_URL=$(python3 -c "
import os
from sqlalchemy.engine import URL

print(URL.create(
    'postgresql+psycopg',
    username=os.environ.get('POSTGRES_USER', 'crm'),
    password=os.environ.get('POSTGRES_PASSWORD', 'crm'),
    host='db',
    port=5432,
    database=os.environ.get('POSTGRES_DB', 'crm'),
).render_as_string(hide_password=False))
")
export DATABASE_URL

alembic upgrade head
exec uvicorn crm.main:app --host 0.0.0.0 --port 8000
