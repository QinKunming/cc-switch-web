"""SQLite database layer, compatible with cc-switch schema v10."""
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional


SCHEMA_VERSION = 10

_CREATE_PROVIDERS = """CREATE TABLE IF NOT EXISTS providers (
    id TEXT NOT NULL,
    app_type TEXT NOT NULL,
    name TEXT NOT NULL,
    settings_config TEXT NOT NULL,
    website_url TEXT,
    category TEXT,
    created_at INTEGER,
    sort_index INTEGER,
    notes TEXT,
    icon TEXT,
    icon_color TEXT,
    meta TEXT NOT NULL DEFAULT '{}',
    is_current BOOLEAN NOT NULL DEFAULT 0,
    in_failover_queue BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (id, app_type)
)"""

_CREATE_SETTINGS = """CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY, value TEXT
)"""


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".cc-switch" / "cc-switch.db"
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            conn = self._connect()
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version > SCHEMA_VERSION:
                    raise RuntimeError(
                        f"Database version {version} is newer than supported {SCHEMA_VERSION}. "
                        "Please upgrade cc-switch-web."
                    )
                conn.execute(_CREATE_PROVIDERS)
                conn.execute(_CREATE_SETTINGS)
                if version < SCHEMA_VERSION:
                    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
                conn.commit()
            finally:
                conn.close()

    def _query(self, sql: str, params: tuple = ()) -> list[dict]:
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(sql, params).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def _execute(self, sql: str, params: tuple = ()) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(sql, params)
                conn.commit()
            finally:
                conn.close()

    def _execute_returning(self, sql: str, params: tuple = ()) -> Optional[dict]:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(sql, params).fetchone()
                conn.commit()
                return dict(row) if row else None
            finally:
                conn.close()

    # --- Provider CRUD ---

    def get_providers(self, app_type: str) -> list[dict]:
        rows = self._query(
            "SELECT * FROM providers WHERE app_type = ? ORDER BY sort_index, created_at",
            (app_type,),
        )
        for r in rows:
            r["settings_config"] = json.loads(r["settings_config"])
            r["is_current"] = bool(r["is_current"])
        return rows

    def get_provider(self, provider_id: str, app_type: str) -> Optional[dict]:
        r = self._execute_returning(
            "SELECT * FROM providers WHERE id = ? AND app_type = ?",
            (provider_id, app_type),
        )
        if r is None:
            return None
        r["settings_config"] = json.loads(r["settings_config"])
        r["is_current"] = bool(r["is_current"])
        return r

    def save_provider(self, provider_id: str, app_type: str, name: str,
                      settings_config: dict, **kwargs) -> None:
        sc_json = json.dumps(settings_config, ensure_ascii=False)
        now = int(time.time())

        with self._lock:
            conn = self._connect()
            try:
                existing = conn.execute(
                    "SELECT id FROM providers WHERE id = ? AND app_type = ?",
                    (provider_id, app_type),
                ).fetchone()

                if existing:
                    sets = ["name = ?", "settings_config = ?"]
                    vals = [name, sc_json]
                    for k, v in kwargs.items():
                        if v is not None:
                            sets.append(f"{k} = ?")
                            vals.append(v)
                    vals.extend([provider_id, app_type])
                    conn.execute(
                        f"UPDATE providers SET {', '.join(sets)} WHERE id = ? AND app_type = ?",
                        tuple(vals),
                    )
                else:
                    cols = ["id", "app_type", "name", "settings_config", "created_at"]
                    vals = [provider_id, app_type, name, sc_json, now]
                    for k, v in kwargs.items():
                        if v is not None:
                            cols.append(k)
                            vals.append(v)
                    placeholders = ", ".join(["?"] * len(cols))
                    col_names = ", ".join(cols)
                    conn.execute(
                        f"INSERT INTO providers ({col_names}) VALUES ({placeholders})",
                        tuple(vals),
                    )
                conn.commit()
            finally:
                conn.close()

    def delete_provider(self, provider_id: str, app_type: str) -> bool:
        with self._lock:
            conn = self._connect()
            try:
                r = conn.execute(
                    "SELECT is_current FROM providers WHERE id = ? AND app_type = ?",
                    (provider_id, app_type),
                ).fetchone()
                if r is None:
                    return False
                if bool(r["is_current"]):
                    conn.close()
                    raise ValueError("Cannot delete the currently active provider")
                conn.execute(
                    "DELETE FROM providers WHERE id = ? AND app_type = ?",
                    (provider_id, app_type),
                )
                conn.commit()
                return True
            finally:
                conn.close()

    def get_current_provider(self, app_type: str) -> Optional[dict]:
        return self.get_provider_by_current(app_type)

    def get_provider_by_current(self, app_type: str) -> Optional[dict]:
        r = self._execute_returning(
            "SELECT * FROM providers WHERE app_type = ? AND is_current = 1",
            (app_type,),
        )
        if r is None:
            return None
        r["settings_config"] = json.loads(r["settings_config"])
        r["is_current"] = bool(r["is_current"])
        return r

    def set_current_provider(self, provider_id: str, app_type: str) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE providers SET is_current = 0 WHERE app_type = ?",
                    (app_type,),
                )
                conn.execute(
                    "UPDATE providers SET is_current = 1 WHERE id = ? AND app_type = ?",
                    (provider_id, app_type),
                )
                conn.commit()
            finally:
                conn.close()

    def update_provider_config(self, provider_id: str, app_type: str,
                               settings_config: dict) -> None:
        sc_json = json.dumps(settings_config, ensure_ascii=False)
        self._execute(
            "UPDATE providers SET settings_config = ? WHERE id = ? AND app_type = ?",
            (sc_json, provider_id, app_type),
        )
