# PostgreSQL setup

Architecture work: [CHR-378](https://linear.app/christopear/issue/CHR-378).
The laboratory includes an explicit Alembic migration and PostgreSQL registry.
See [the laboratory guide](LABORATORY.md) for migration, testing and run commands.

## Settings needed

Create a dedicated database and login role. Suggested names are both `voynich`.
The role should own that database so later reviewed migrations can create tables;
it does not need superuser, role-management or cluster-wide privileges.

Prefer `POSTGRES_URL="postgresql:///voynich"` in the ignored local `.env` for
a local Unix socket using the OS login. A supplied URL takes precedence over
PG settings. URL passwords must be percent-encoded. SQLAlchemy uses psycopg 3.

Alternatively omit POSTGRES_URL and supply these settings:

| Variable | Suggested local value |
|---|---|
| `PGHOST` | `127.0.0.1` (or the reachable server hostname) |
| `PGPORT` | `5432` |
| `PGDATABASE` | `voynich` |
| `PGUSER` | `voynich` |
| `PGPASSWORD` | The role's password, entered locally; alternatively configure a password file |
| `PGSSLMODE` | `prefer` for a local instance; use the server's required policy for remote connections |
| `PGCONNECT_TIMEOUT` | `5` seconds |
| `PGSSLROOTCERT` | Optional trusted CA file for certificate verification |

The host must be reachable from the machine running this checkout. PostgreSQL on
another computer requires that computer's address rather than `127.0.0.1`.
Remote authenticated TLS commonly uses `verify-full` with the appropriate CA.
Do not put passwords in Git, Linear or the PR; update `.env` locally.

An administrator can provision the suggested database in psql:

```sql
CREATE ROLE voynich LOGIN;
\password voynich
CREATE DATABASE voynich OWNER voynich;
```

These commands are instructions, not operations performed by the setup code.

## Install and check explicitly

```bash
uv sync --locked
# On a fresh checkout only; preserve an existing .env:
cp -n .env.example .env
# Edit .env with your connection settings, then:
uv run --env-file .env --locked python -m voynich.storage.database
```

The checker only runs `SELECT 1` and closes the connection. It does not create
tables or run migrations. Modules do not load `.env` implicitly: uv loads it for
this command, or a deployment can supply environment variables directly. Engine
creation itself is lazy. Configuration builds a SQLAlchemy URL without string
interpolation, so password punctuation does not require URL escaping.

The initial dependency constraints are `psycopg[binary]>=3.3.4` and
`sqlalchemy>=2.0`; `uv.lock` records the resolved versions. No live database is
required by unit tests. Integration tests will use a separately provisioned test
database and explicit opt-in configuration; never reset the research database.

Schema management uses versioned Alembic migrations. There is deliberately no implicit
`metadata.create_all()` or database creation at application startup.
