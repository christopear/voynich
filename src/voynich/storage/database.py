"""Explicit PostgreSQL configuration and a read-only connection check.

Importing this module never connects or creates a schema. Load .env through uv.
"""
from dataclasses import dataclass, field
import os
from typing import Mapping

from sqlalchemy import URL, Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    database: str
    user: str
    password: str | None = field(default=None, repr=False)
    sslmode: str = "prefer"
    connect_timeout: int = 5
    sslrootcert: str | None = None

    def __post_init__(self):
        if any(not x.strip() for x in (self.host, self.database, self.user)):
            raise ValueError("PGHOST, PGDATABASE and PGUSER must be nonempty")
        if not 1 <= self.port <= 65535 or not 1 <= self.connect_timeout <= 300:
            raise ValueError("PGPORT must be 1..65535 and PGCONNECT_TIMEOUT must be 1..300")
        if self.sslmode not in {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}:
            raise ValueError("unsupported PGSSLMODE")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "DatabaseSettings":
        env = os.environ if environ is None else environ
        try:
            port = int(env.get("PGPORT", "5432"))
            timeout = int(env.get("PGCONNECT_TIMEOUT", "5"))
        except ValueError:
            raise ValueError("PGPORT and PGCONNECT_TIMEOUT must be integers") from None
        return cls(env.get("PGHOST", "127.0.0.1"), port,
                   env.get("PGDATABASE", "voynich"), env.get("PGUSER", "voynich"),
                   env.get("PGPASSWORD") or None, env.get("PGSSLMODE", "prefer"),
                   timeout, env.get("PGSSLROOTCERT") or None)

    def url(self) -> URL:
        query = {"sslmode": self.sslmode, "connect_timeout": str(self.connect_timeout)}
        if self.sslrootcert:
            query["sslrootcert"] = self.sslrootcert
        return URL.create("postgresql+psycopg", username=self.user, password=self.password,
                          host=self.host, port=self.port, database=self.database, query=query)


def make_engine(settings: DatabaseSettings | None = None) -> Engine:
    return create_engine((settings or DatabaseSettings.from_env()).url(),
                         pool_pre_ping=True, hide_parameters=True)


def main() -> int:
    engine = None
    try:
        engine = make_engine()
        with engine.connect() as connection:
            if connection.scalar(text("SELECT 1")) != 1:
                raise RuntimeError("unexpected connection-check result")
    except (SQLAlchemyError, ValueError, RuntimeError) as exc:
        # Driver exception messages can contain connection details. Do not emit them.
        print(f"PostgreSQL check failed ({type(exc).__name__}). Check local PG settings and server availability.")
        return 1
    finally:
        if engine is not None:
            engine.dispose()
    print("PostgreSQL connection successful. No schema changes were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
