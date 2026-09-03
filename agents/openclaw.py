"""OpenClaw agent: additive mode, live at ~/.openclaw/openclaw.json."""
import json
import time

from fastapi import HTTPException

from config_ops import (
    import_openclaw_live,
    openclaw_get_providers,
    openclaw_remove_provider,
    openclaw_set_default_model,
    openclaw_set_provider,
    read_openclaw_config,
    write_openclaw_config,
)

from agents.base import AgentSpec


def _default_config() -> dict:
    return {"models": {"mode": "merge", "providers": {}}, "agents": {"defaults": {}}}


def _sanitize_models(settings_config: dict) -> dict:
    """Deep-copy settings_config and strip fields OpenClaw doesn't recognize from model entries."""
    clean = json.loads(json.dumps(settings_config))
    for m in clean.get("models", []):
        m.pop("alias", None)
    return clean


def sync_to_live(provider_id: str, settings_config: dict, config: dict = None) -> None:
    if config is None:
        config = read_openclaw_config()
    if config is None:
        config = _default_config()
    openclaw_set_provider(config, provider_id, _sanitize_models(settings_config))
    write_openclaw_config(config)


def remove_from_live(provider_id: str, provider: dict) -> None:
    config = read_openclaw_config()
    if config:
        openclaw_remove_provider(config, provider_id)
        write_openclaw_config(config)


def switch(db, provider: dict) -> list[str]:
    config = read_openclaw_config()
    if config is None:
        config = _default_config()
    clean_config = _sanitize_models(provider["settings_config"])
    sync_to_live(provider["id"], clean_config, config)
    models = clean_config.get("models", [])
    if models:
        primary = f"{provider['id']}/{models[0]['id']}"
        fallbacks = [f"{provider['id']}/{m['id']}" for m in models[1:4]] if len(models) > 1 else None
        openclaw_set_default_model(config, primary, fallbacks)
    write_openclaw_config(config)
    db.set_current_provider(provider["id"], "openclaw")
    return []


def import_live(db) -> dict:
    config = import_openclaw_live()
    if config is None:
        raise HTTPException(404, "No OpenClaw openclaw.json found")
    providers = openclaw_get_providers(config)
    if not providers:
        raise HTTPException(404, "No providers found in OpenClaw config")
    count = 0
    for pid, pdata in providers.items():
        existing = db.get_provider(pid, "openclaw")
        if not existing:
            db.save_provider(pid, "openclaw", pdata.get("name", pid), dict(pdata),
                             category="custom")
            count += 1
    return {"imported": count}


def load_presets() -> list:
    from presets.openclaw_presets import OPENCLAW_PRESETS
    return OPENCLAW_PRESETS


def apply_api_key(settings_config: dict, api_key: str) -> dict:
    settings_config["apiKey"] = api_key
    return settings_config


OPENCLAW_SPEC = AgentSpec(
    id="openclaw",
    name="OpenClaw",
    icon="🐾",
    mode="additive",
    switch=switch,
    sync_to_live=sync_to_live,
    remove_from_live=remove_from_live,
    import_live=import_live,
    load_presets=load_presets,
    apply_api_key=apply_api_key,
)
