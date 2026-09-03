"""Grok Build (Grok CLI) agent: exclusive mode, live at ~/.grok/config.toml.

settings_config shape: {"config": "<native Grok TOML text>"}:
    [models]
    default = "<profile>"
    [model."<profile>"]
    model / base_url / name / api_key|env_key / api_backend / context_window

Official entries carry an empty config (Grok CLI falls back to xAI OAuth).
"""
import time

from fastapi import HTTPException

from config_ops import atomic_write, get_home_dir

from agents.base import AgentSpec
from agents.toml_ops import dumps_toml, parse_toml


def _config_path():
    return get_home_dir() / ".grok" / "config.toml"


def is_official(provider: dict) -> bool:
    return provider.get("category") == "official" or provider["id"] == "grokbuild-official"


def _validate_syntax(text: str) -> None:
    try:
        parse_toml(text)
    except ValueError as e:
        raise HTTPException(400, f"Invalid TOML in Grok config: {e}")


def validate_config(text: str) -> None:
    """Full validation for non-official configs. 400 with the missing fields."""
    _validate_syntax(text)
    data = parse_toml(text)
    errors = []

    models = data.get("models")
    default = models.get("default") if isinstance(models, dict) else None
    if not isinstance(default, str) or not default:
        errors.append("[models].default (profile name)")
        profile = None
    else:
        model_table = data.get("model")
        profile = model_table.get(default) if isinstance(model_table, dict) else None
        if not isinstance(profile, dict):
            errors.append(f'[model."{default}"] profile table')

    if isinstance(profile, dict):
        if not isinstance(profile.get("model"), str) or not profile.get("model"):
            errors.append("model")
        if not isinstance(profile.get("base_url"), str) or not profile.get("base_url"):
            errors.append("base_url")
        if not isinstance(profile.get("name"), str) or not profile.get("name"):
            errors.append("name")
        if "api_key" not in profile and "env_key" not in profile:
            errors.append("api_key or env_key")
        if not isinstance(profile.get("api_backend"), str) or not profile.get("api_backend"):
            errors.append("api_backend")
        cw = profile.get("context_window")
        if isinstance(cw, bool) or not isinstance(cw, int) or cw <= 0:
            errors.append("context_window (positive integer)")

    if errors:
        raise HTTPException(400, f"Grok config is missing: {', '.join(errors)}")


def switch(db, provider: dict) -> list[str]:
    sc = provider["settings_config"]
    text = sc.get("config", "")
    if not isinstance(text, str):
        raise HTTPException(400, "Grok config must be a TOML string")

    if is_official(provider):
        if text.strip():
            _validate_syntax(text)
    else:
        if not text.strip():
            raise HTTPException(400, "Grok config is empty (missing [models].default and model profile)")
        validate_config(text)

    # backfill: current provider record takes over the live config text
    cfg = _config_path()
    live_text = cfg.read_text(encoding="utf-8") if cfg.exists() else None
    current = db.get_current_provider("grokbuild")
    if current and live_text is not None:
        db.update_provider_config(current["id"], "grokbuild", {"config": live_text})

    db.set_current_provider(provider["id"], "grokbuild")
    atomic_write(cfg, text.encode("utf-8"))
    return []


def import_live(db) -> dict:
    cfg = _config_path()
    if not cfg.exists():
        raise HTTPException(404, "No Grok CLI config found (~/.grok/config.toml)")
    sc = {"config": cfg.read_text(encoding="utf-8")}
    provider_id = f"imported-{int(time.time())}"
    db.save_provider(provider_id, "grokbuild", "Imported Config", sc, category="custom")
    return {"id": provider_id, "name": "Imported Config"}


def load_presets() -> list:
    from presets.grokbuild_presets import GROKBUILD_PRESETS
    return GROKBUILD_PRESETS


def apply_api_key(settings_config: dict, api_key: str) -> dict:
    text = settings_config.get("config", "")
    try:
        data = parse_toml(text)
    except ValueError as e:
        raise HTTPException(400, f"Cannot apply API key: invalid TOML ({e})")
    default = data.get("models", {}).get("default")
    profile = data.get("model", {}).get(default) if default else None
    if not isinstance(profile, dict):
        raise HTTPException(400, "Cannot apply API key: no default model profile in Grok config")
    profile["api_key"] = api_key
    profile.pop("env_key", None)
    settings_config["config"] = dumps_toml(data)
    return settings_config


GROKBUILD_SPEC = AgentSpec(
    id="grokbuild",
    name="Grok Build",
    icon="⚡",
    mode="exclusive",
    switch=switch,
    import_live=import_live,
    load_presets=load_presets,
    apply_api_key=apply_api_key,
)
