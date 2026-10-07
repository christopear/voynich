"""Offline database setup contracts; no PostgreSQL server required."""
import contextlib
import io
import unittest
from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from voynich.storage.database import DatabaseSettings, main, make_engine


class DatabaseTests(unittest.TestCase):
    def test_defaults_and_password_redaction(self):
        settings = DatabaseSettings.from_env({"PGPASSWORD": "secret@:/#value"})
        self.assertEqual(settings.database, "voynich")
        self.assertEqual(settings.url().drivername, "postgresql+psycopg")
        self.assertEqual(settings.url().password, "secret@:/#value")
        self.assertNotIn("secret", repr(settings))
        self.assertNotIn("secret", str(settings.url()))

    def test_local_url_preserves_socket_defaults(self):
        settings = DatabaseSettings.from_env({"POSTGRES_URL": "postgresql:///voynich",
                                             "PGPORT": "invalid", "PGHOST": "wrong"})
        self.assertIsNone(settings.url().host)
        self.assertIsNone(settings.url().username)
        self.assertIsNone(settings.url().port)
        self.assertEqual(settings.database, "voynich")

    def test_url_validation_and_password(self):
        for value in ("", "sqlite:///db", "postgresql:///", "postgresql:///db?connect_timeout=0"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                DatabaseSettings.from_env({"POSTGRES_URL": value})
        settings = DatabaseSettings.from_env({
            "POSTGRES_URL": "postgres://u:secret%40word@localhost/db?sslmode=require"})
        self.assertEqual(settings.url().password, "secret@word")
        self.assertEqual(settings.url().query["sslmode"], "require")
        self.assertNotIn("secret", repr(settings))

    def test_overrides_and_certificate(self):
        settings = DatabaseSettings.from_env({"PGPORT": "5433", "PGDATABASE": "research",
                                             "PGUSER": "researcher", "PGSSLMODE": "verify-full",
                                             "PGSSLROOTCERT": "/tmp/root.crt"})
        self.assertEqual(settings.port, 5433)
        self.assertEqual(settings.url().query["sslrootcert"], "/tmp/root.crt")
        self.assertIsNone(settings.password)

    def test_invalid_values(self):
        for env in ({"PGPORT": "oops"}, {"PGPORT": "0"}, {"PGUSER": ""},
                    {"PGSSLMODE": "invalid"}, {"PGCONNECT_TIMEOUT": "0"}):
            with self.subTest(env=env), self.assertRaises(ValueError):
                DatabaseSettings.from_env(env)

    def test_engine_construction_does_not_connect(self):
        with patch("psycopg.connect") as connect:
            engine = make_engine(DatabaseSettings.from_env({}))
            self.assertEqual(engine.dialect.name, "postgresql")
            connect.assert_not_called()
            engine.dispose()

    def test_connection_error_does_not_print_secrets(self):
        output = io.StringIO()
        with patch("voynich.storage.database.make_engine", side_effect=OperationalError(
                "secret-query", {}, Exception("password=secret"))), contextlib.redirect_stdout(output):
            self.assertEqual(main(), 1)
        self.assertNotIn("secret", output.getvalue())


if __name__ == "__main__":
    unittest.main()
