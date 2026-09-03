"""Pi coding agent: additive mode, live at ~/.pi/agent/models.json.

`PI_CODING_AGENT_DIR` overrides the agent directory in production; when the
CC_SWITCH_TEST_HOME sandbox is active the sandbox path always wins. The
sibling settings.json belongs to Pi itself and is never written by us.
settings_config is the provider fragment stored under `providers.<id>`.
"""
import json
import os
from pathlib import Path

import json5
from fastapi import HTTPException

from config_ops import atomic_write, get_home_dir

from agents.base import AgentSpec


def _pi_dir() -> Path:
    test = os.environ.get("CC_SWITCH_TEST_HOME", "").strip()
    if test:
        return Path(test) / ".pi" / "agent"
    override = os.environ.get("PI_CODING_AGENT_DIR", "").strip()
    if override:
        return Path(override)
    return get_home_dir() / ".pi" / "agent"


def _models_path() -> Path:
    return _pi_dir() / "models.json"


def read_live_config():
    path = _models_path()
    if not path.exists():
        return None
    try:
        config = json5.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        raise HTTPException(400, f"Invalid models.json: {e}")
    if not isinstance(config, dict):
        raise HTTPException(400, "models.json root is not an object")
    return config


def write_live_config(config: dict) -> None:
    atomic_write(_models_path(),
                 json.dumps(config, indent=2, ensure_ascii=False).encode("utf-8"))


def _providers(config: dict) -> dict:
    providers = config.get("providers")
    if not isinstance(providers, dict):
        raise HTTPException(400, "models.json 'providers' section is not an object")
    return providers


def sync_to_live(provider_id: str, settings_config: dict) -> None:
    config = read_live_config() or {}
    _providers(config)[provider_id] = settings_config
    write_live_config(config)


def remove_from_live(provider_id: str, provider: dict) -> None:
    config = read_live_config()
    if config is None:
        return
    _providers(config).pop(provider_id, None)
    write_live_config(config)


def switch(db, provider: dict) -> list[str]:
    sync_to_live(provider["id"], provider["settings_config"])
    db.set_current_provider(provider["id"], "pi")
    return []


def import_live(db) -> dict:
    config = read_live_config()
    if config is None:
        raise HTTPException(404, "No Pi models.json found (~/.pi/agent/models.json)")
    providers = config.get("providers")
    if not isinstance(providers, dict) or not providers:
        raise HTTPException(404, "No providers found in models.json")
    count = 0
    for pid, pdata in providers.items():
        if db.get_provider(pid, "pi"):
            continue
        data = json.loads(json.dumps(pdata))
        db.save_provider(pid, "pi", data.get("name", pid), data, category="custom")
        count += 1
    return {"imported": count}


def load_presets() -> list:
    from presets.pi_presets import PI_PRESETS
    return PI_PRESETS


def apply_api_key(settings_config: dict, api_key: str) -> dict:
    settings_config["apiKey"] = api_key
    return settings_config


PI_SPEC = AgentSpec(
    id="pi",
    name="Pi",
    icon="🥧",
    mode="additive",
    switch=switch,
    sync_to_live=sync_to_live,
    remove_from_live=remove_from_live,
    import_live=import_live,
    load_presets=load_presets,
    apply_api_key=apply_api_key,
)
