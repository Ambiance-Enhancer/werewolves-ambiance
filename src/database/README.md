# Database Migrations (PostgreSQL)

These SQL migrations use PostgreSQL session settings (`current_setting('app.*')`)
to inject environment-specific values (users, passwords, schema, database).

## Prerequisites
- PostgreSQL client (`psql`)
- A running PostgreSQL instance
- A `.env` file with the required variables

## Required environment variables

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=werewolves
POSTGRES_SCHEMA=werewolves

POSTGRES_USER=postgres
POSTGRES_RW_USER=werewolves_rw
POSTGRES_RW_PASSWORD=strong_rw_password
POSTGRES_RO_USER=werewolves_ro
POSTGRES_RO_PASSWORD=strong_ro_password
```

## Run migrations

```bash
set -a && source .env && set +a

psql -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 \
  -c "SET app.postgres_db = '$POSTGRES_DB'" \
  -c "SET app.postgres_schema = '$POSTGRES_SCHEMA'" \
  -c "SET app.rw_user = '$POSTGRES_RW_USER'" \
  -c "SET app.rw_password = '$POSTGRES_RW_PASSWORD'" \
  -c "SET app.ro_user = '$POSTGRES_RO_USER'" \
  -c "SET app.ro_password = '$POSTGRES_RO_PASSWORD'" \
  -f src/database/migrations/001_add_rw_ro_roles.sql
```

## Notes

* Migrations are pure PostgreSQL SQL and compatible with SQLFluff.
* Identifiers and secrets are safely injected using `format()` with `%I` / `%L`.
* Execution stops immediately on error (`ON_ERROR_STOP=1`).
