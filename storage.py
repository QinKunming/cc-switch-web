"""App-owned storage paths (~/.cc-switch-web) + one-time migration from legacy ~/.cc-switch.

Kept separate from the desktop cc-switch app so the two tools never share state.
Agent live configs (~/.claude/settings.json etc.) are NOT affected — they stay at
their native locations, which is this tool's whole purpose.
"""
import shutil
import sqlite3
from pathlib import Path

from config_ops import get_home_dir

LEGACY_DIR_NAME = ".cc-switch"
APP_DIR_NAME = ".cc-switch-web"
DB_NAME = "cc-switch.db"
AUTH_NAME = "web-auth.json"


def get_app_data_dir() -> Path:
    return get_home_dir() / APP_DIR_NAME


def get_db_path() -> Path:
    return get_app_data_dir() / DB_NAME


def get_auth_path() -> Path:
    return get_app_data_dir() / AUTH_NAME


def get_legacy_dir() -> Path:
    """Legacy cc-switch directory. Resolved through the same home-dir hook
    (CC_SWITCH_TEST_HOME) so tests can construct deterministic fixtures — on a
    real machine the env is unset and this is simply the user's home."""
    return get_home_dir() / LEGACY_DIR_NAME


def _migrate_db(target: Path, legacy: Path) -> None:
    # Prefer the sqlite backup API: consistent snapshot even when the source is
    # in WAL mode or currently open by the desktop app.
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        src = sqlite3.connect(f"file:{legacy}?mode=ro", uri=True)
        dst = sqlite3.connect(str(target))
        try:
            with dst:
                src.backup(dst)
        finally:
            dst.close()
            src.close()
        print(f"  Migrated database: {legacy} -> {target}")
        return
    except Exception as e:
        print(f"  DB backup-API migration failed ({e}); falling back to file copy")
        if target.exists():
            try:
                target.unlink()
            except OSError:
                pass

    # Fallback: copy db + wal + shm in order; SQLite replays the WAL on open.
    try:
        shutil.copyfile(legacy, target)
        for suffix in ("-wal", "-shm"):
            side = Path(str(legacy) + suffix)
            if side.exists():
                shutil.copyfile(side, Path(str(target) + suffix))
        print(f"  Migrated database (file copy): {legacy} -> {target}")
    except Exception as e:
        print(f"  WARNING: could not migrate {legacy}: {e}; starting with an empty database")


def _migrate_file(target: Path, legacy: Path) -> None:
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.parent / (target.name + ".tmp")
        shutil.copyfile(legacy, tmp)
        import os
        os.replace(str(tmp), str(target))
        print(f"  Migrated auth file: {legacy} -> {target}")
    except Exception as e:
        print(f"  WARNING: could not migrate {legacy}: {e}")


def migrate_legacy_storage() -> None:
    """One-time copy of legacy shared storage into the independent app dir.

    Never modifies or deletes anything under the legacy directory. Safe to call
    on every startup — it is a no-op once the targets exist.
    """
    legacy_dir = get_legacy_dir()

    target_db = get_db_path()
    if not target_db.exists():
        legacy_db = legacy_dir / DB_NAME
        if legacy_db.exists():
            _migrate_db(target_db, legacy_db)

    target_auth = get_auth_path()
    if not target_auth.exists():
        legacy_auth = legacy_dir / AUTH_NAME
        if legacy_auth.exists():
            _migrate_file(target_auth, legacy_auth)
