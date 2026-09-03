"""Gemini CLI agent: exclusive mode, live at ~/.gemini/{.env, settings.json}.

settings_config shape: {"env": {...}, "config": {...}|None}.
.env is rewritten sorted; settings.json is shallow-merged (keeps mcpServers
and other top-level keys) and security.auth.selectedType is updated only.
"""
import os
import platform
import time

from fastapi import HTTPException

from config_ops import atomic_write, get_home_dir, read_json, write_json

from agents.base import AgentSpec


def _gemini_dir():
    return get_home_dir() / ".gemini"


def _env_path():
    return _gemini_dir() / ".env"


def _settings_path():
    return _gemini_dir() / "settings.json"


def parse_env_file(text: str) -> dict:
    """Loose .env parse: KEY=VALUE lines, blank lines and # comments skipped."""
    env = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            env[key] = value
    return env


def _needs_quoting(value: str) -> bool:
    return any(c in value for c in " \t#'\"\\")


def serialize_env_file(env: dict) -> str:
    lines = []
    for key in sorted(env):
        value = str(env[key])
        if _needs_quoting(value):
            value = '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def write_env_atomic(env: dict) -> None:
    path = _env_path()
    atomic_write(path, serialize_env_file(env).encode("utf-8"))
    if platform.system() != "Windows":
        try:
            os.chmod(_gemini_dir(), 0o700)
            os.chmod(path, 0o600)
        except OSError:
            pass


def _read_settings() -> dict:
    settings = read_json(_settings_path())
    return settings if isinstance(settings, dict) else {}


def _update_selected_type(settings: dict, value: str) -> dict:
    security = settings.get("security")
    if not isinstance(security, dict):
        security = {}
        settings["security"] = security
    auth = security.get("auth")
    if not isinstance(auth, dict):
        auth = {}
        security["auth"] = auth
    auth["selectedType"] = value
    return settings


def is_official(provider: dict) -> bool:
    return provider.get("category") == "official" or provider["id"] == "gemini-official"


def switch(db, provider: dict) -> list[str]:
    sc = provider["settings_config"]
    env = sc.get("env") or {}
    if not isinstance(env, dict):
        raise HTTPException(400, "Gemini env must be an object")

    if not is_official(provider):
        if not (env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY")):
            raise HTTPException(400, "Gemini config is missing GEMINI_API_KEY")

    # backfill: current provider record takes over the live config
    env_file = _env_path()
    live_env = parse_env_file(env_file.read_text(encoding="utf-8")) if env_file.exists() else {}
    live_settings = _read_settings()
    current = db.get_current_provider("gemini")
    if current and (live_env or live_settings):
        db.update_provider_config(current["id"], "gemini", {
            "env": live_env,
            "config": live_settings or None,
        })
    db.set_current_provider(provider["id"], "gemini")

    write_env_atomic(env)
    settings = _read_settings()
    extra = sc.get("config")
    if isinstance(extra, dict):
        settings.update(extra)
    if is_official(provider):
        settings = _update_selected_type(settings, "oauth-personal")
    else:
        settings = _update_selected_type(settings, "gemini-api-key")
    write_json(_settings_path(), settings)
    return []


def import_live(db) -> dict:
    env_file = _env_path()
    settings_file = _settings_path()
    if not env_file.exists() and not settings_file.exists():
        raise HTTPException(404, "No Gemini configuration found (~/.gemini)")
    env = parse_env_file(env_file.read_text(encoding="utf-8")) if env_file.exists() else {}
    sc = {"env": env}
    if settings_file.exists():
        sc["config"] = _read_settings() or None
    provider_id = f"imported-{int(time.time())}"
    db.save_provider(provider_id, "gemini", "Imported Config", sc, category="custom")
    return {"id": provider_id, "name": "Imported Config"}


def load_presets() -> list:
    from presets.gemini_presets import GEMINI_PRESETS
    return GEMINI_PRESETS


def apply_api_key(settings_config: dict, api_key: str) -> dict:
    env = settings_config.setdefault("env", {})
    if "GEMINI_API_KEY" not in env and "GOOGLE_API_KEY" in env:
        env["GOOGLE_API_KEY"] = api_key
    else:
        env["GEMINI_API_KEY"] = api_key
    return settings_config


GEMINI_SPEC = AgentSpec(
    id="gemini",
    name="Gemini CLI",
    icon="✨",
    mode="exclusive",
    switch=switch,
    import_live=import_live,
    load_presets=load_presets,
    apply_api_key=apply_api_key,
)
