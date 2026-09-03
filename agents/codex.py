"""Codex agent: exclusive mode, live at ~/.codex/{auth.json, config.toml}.

settings_config shape: {"auth": {...}, "config": "<TOML text>"}.
Official entries never touch auth.json (preserves the ChatGPT OAuth login).
"""
import json
import time

from fastapi import HTTPException

from config_ops import atomic_write, get_home_dir, read_json

from agents.base import AgentSpec
from agents.toml_ops import parse_toml


def _codex_dir():
    return get_home_dir() / ".codex"


def _auth_path():
    return _codex_dir() / "auth.json"


def _config_path():
    return _codex_dir() / "config.toml"


def is_official(provider: dict) -> bool:
    return provider.get("category") == "official" or provider["id"] == "codex-official"


def read_live_settings():
    """Read both live files. None when neither exists."""
    auth = read_json(_auth_path())
    cfg = _config_path()
    config_text = cfg.read_text(encoding="utf-8") if cfg.exists() else None
    if auth is None and config_text is None:
        return None
    return {"auth": auth or {}, "config": config_text or ""}


def _validate_settings(sc: dict) -> None:
    auth = sc.get("auth")
    if auth is None:
        sc["auth"] = auth = {}
    if not isinstance(auth, dict):
        raise HTTPException(400, "Codex auth must be a JSON object")
    config_text = sc.get("config", "")
    if not isinstance(config_text, str):
        raise HTTPException(400, "Codex config must be a TOML string")
    if config_text.strip():
        try:
            parse_toml(config_text)
        except ValueError as e:
            raise HTTPException(400, f"Invalid TOML in Codex config: {e}")


def write_live_atomic(auth: dict, config_text: str) -> None:
    """Write auth.json then config.toml; roll auth.json back if the second fails."""
    _validate_settings({"auth": auth, "config": config_text})
    auth_path, cfg_path = _auth_path(), _config_path()
    previous = auth_path.read_bytes() if auth_path.exists() else None
    atomic_write(auth_path, json.dumps(auth, indent=2, ensure_ascii=False).encode("utf-8"))
    try:
        atomic_write(cfg_path, config_text.encode("utf-8"))
    except BaseException:
        # restore auth.json to its pre-write state
        if previous is not None:
            atomic_write(auth_path, previous)
        elif auth_path.exists():
            auth_path.unlink()
        raise


def switch(db, provider: dict) -> list[str]:
    sc = provider["settings_config"]
    _validate_settings(sc)

    # backfill: current provider record takes over the live config
    live = read_live_settings()
    current = db.get_current_provider("codex")
    if current and live is not None:
        db.update_provider_config(current["id"], "codex", live)
    db.set_current_provider(provider["id"], "codex")

    if is_official(provider):
        # Official: write config.toml only — never clobber the ChatGPT OAuth auth.
        atomic_write(_config_path(), sc.get("config", "").encode("utf-8"))
    else:
        write_live_atomic(sc.get("auth") or {}, sc.get("config", ""))
    return []


def import_live(db) -> dict:
    live = read_live_settings()
    if live is None:
        raise HTTPException(404, "No Codex config found (~/.codex/auth.json or config.toml)")
    provider_id = f"imported-{int(time.time())}"
    db.save_provider(provider_id, "codex", "Imported Config", live, category="custom")
    return {"id": provider_id, "name": "Imported Config"}


def load_presets() -> list:
    from presets.codex_presets import CODEX_PRESETS
    return CODEX_PRESETS


def apply_api_key(settings_config: dict, api_key: str) -> dict:
    settings_config.setdefault("auth", {})["OPENAI_API_KEY"] = api_key
    return settings_config


CODEX_SPEC = AgentSpec(
    id="codex",
    name="Codex",
    icon="📖",
    mode="exclusive",
    switch=switch,
    import_live=import_live,
    load_presets=load_presets,
    apply_api_key=apply_api_key,
)
