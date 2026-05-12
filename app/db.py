import json
import os
from urllib.parse import unquote, urlparse

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


POSTGRES_SCHEMES = ("postgres://", "postgresql://")


def default_database_url(base_dir):
    sqlite_path = os.path.join(base_dir, "database", "app.db")
    return "sqlite:///" + sqlite_path.replace("\\", "/")


def resolve_database_url(base_dir):
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url

    legacy_path = os.environ.get("DATABASE_PATH")
    if legacy_path:
        return "sqlite:///" + legacy_path.replace("\\", "/")

    return default_database_url(base_dir)


def is_postgres_url(database_url):
    return database_url.startswith(POSTGRES_SCHEMES)


def sqlite_path_from_url(database_url):
    parsed = urlparse(database_url)
    if parsed.scheme != "sqlite":
        raise ValueError("Expected sqlite database URL.")

    if parsed.netloc and parsed.netloc != "":
        path = f"//{parsed.netloc}{parsed.path}"
    else:
        path = parsed.path

    path = unquote(path)
    if os.name == "nt" and path.startswith("/") and len(path) > 2 and path[2] == ":":
        path = path[1:]
    return path


def ensure_database_parent(database_url):
    if is_postgres_url(database_url):
        return

    path = sqlite_path_from_url(database_url)
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def schema_path_for(base_dir, database_url):
    filename = "init_postgres.sql" if is_postgres_url(database_url) else "init.sql"
    return os.path.join(base_dir, "database", filename)


def connect_database(database_url):
    if is_postgres_url(database_url):
        return DatabaseConnection("postgres", psycopg.connect(database_url, row_factory=dict_row))

    import sqlite3

    path = sqlite_path_from_url(database_url)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return DatabaseConnection("sqlite", conn)


class DatabaseConnection:
    def __init__(self, kind, conn):
        self.kind = kind
        self.conn = conn

    def execute(self, sql, params=()):
        if self.kind == "postgres":
            sql = sql.replace("?", "%s")
        return self.conn.execute(sql, self._adapt_params(params))

    def executescript(self, sql):
        if self.kind == "sqlite":
            return self.conn.executescript(sql)
        with self.conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def _adapt_params(self, params):
        if isinstance(params, dict):
            return {key: self._adapt_value(value) for key, value in params.items()}
        return tuple(self._adapt_value(value) for value in params)

    def _adapt_value(self, value):
        if isinstance(value, (dict, list)):
            if self.kind == "postgres":
                return Jsonb(value)
            return json.dumps(value)
        return value
