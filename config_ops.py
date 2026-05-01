"""Config file read/write with atomic writes, cross-platform (Windows + Linux)."""
import json
import os
import platform
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

try:
    import json5
except ImportError:
    json5 = None


# --- Path resolution ---

def get_home_dir() -> Path:
    env = os.environ.get("CC_SWITCH_TEST_HOME", "").strip()
    if env:
        return Path(env)
    return Path.home()


def get_claude_settings_path() -> Path:
    claude_dir = get_home_dir() / ".claude"
    settings = claude_dir / "settings.json"
    if settings.exists():
        return settings
    legacy = claude_dir / "claude.json"
    if legacy.exists():
        return legacy
    return settings


def get_openclaw_config_path() -> Path:
    return get_home_dir() / ".openclaw" / "openclaw.json"


# --- Atomic write ---

def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = time.time_ns()
    tmp = path.parent / f"{path.name}.tmp.{ts}"
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        if platform.system() == "Windows":
            if path.exists():
                try:
                    os.remove(path)
                except OSError:
                    pass
        os.replace(str(tmp), str(path))
    except BaseException:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def write_json(path: Path, data: Any) -> None:
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))


def read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Claude Code ---

_CLAUDE_INTERNAL_FIELDS = {"apiFormat", "api_format", "openrouter_compat_mode", "openrouterCompatMode"}


def sanitize_claude_settings(settings: dict) -> dict:
    return {k: v for k, v in settings.items() if k not in _CLAUDE_INTERNAL_FIELDS}


def read_claude_settings() -> Optional[dict]:
    return read_json(get_claude_settings_path())


def write_claude_settings(settings: dict) -> None:
    clean = sanitize_claude_settings(settings)
    path = get_claude_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write directly (not atomic) so Claude Code's file watcher detects the change.
    # Atomic write (delete + rename) can cause watchers to miss the update.
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())


# --- OpenClaw ---

def _ensure_json5():
    if json5 is None:
        raise RuntimeError("json5 package is required for OpenClaw config. Install with: pip install json5")


def read_openclaw_config() -> Optional[dict]:
    path = get_openclaw_config_path()
    if not path.exists():
        return None
    _ensure_json5()
    with open(path, "r", encoding="utf-8") as f:
        return json5.loads(f.read())


def write_openclaw_config(config: dict) -> None:
    path = get_openclaw_config_path()
    atomic_write(path, json.dumps(config, indent=2, ensure_ascii=False).encode("utf-8"))


def openclaw_get_providers(config: dict) -> dict:
    if config is None:
        return {}
    models = config.get("models", {})
    return models.get("providers", {})


def openclaw_set_provider(config: dict, provider_id: str, provider_data: dict) -> dict:
    if "models" not in config:
        config["models"] = {}
    if "providers" not in config["models"]:
        config["models"]["providers"] = {}
    config["models"]["providers"][provider_id] = provider_data
    return config


def openclaw_remove_provider(config: dict, provider_id: str) -> dict:
    providers = config.get("models", {}).get("providers", {})
    providers.pop(provider_id, None)
    return config


def openclaw_get_default_model(config: dict) -> Optional[str]:
    agents = config.get("agents", {})
    defaults = agents.get("defaults", {})
    model = defaults.get("model", {})
    return model.get("primary")


def openclaw_set_default_model(config: dict, primary: str,
                               fallbacks: Optional[list[str]] = None) -> dict:
    if "agents" not in config:
        config["agents"] = {}
    if "defaults" not in config["agents"]:
        config["agents"]["defaults"] = {}
    model = {"primary": primary}
    if fallbacks:
        model["fallbacks"] = fallbacks
    config["agents"]["defaults"]["model"] = model
    return config


# --- Live config import ---

def import_claude_live() -> Optional[dict]:
    return read_claude_settings()


def import_openclaw_live() -> Optional[dict]:
    return read_openclaw_config()
