"""OpenCode agent: additive mode, live at ~/.config/opencode/opencode.json.

All platforms use the XDG-style path (matches cc-switch). The file is read
as JSON5 and written as standard JSON; a `$schema` key present on disk (or
in the default skeleton) is preserved. settings_config is the provider
fragment stored under `provider.<id>`.
"""
import json
import os
from pathlib import Path

import json5
from fastapi import HTTPException

from config_ops import atomic_write

from agents.base import AgentSpec


def _opencode_dir() -> Path:
    test = os.environ.get("CC_SWITCH_TEST_HOME", "").strip()
    if test:
        return Path(test) / ".config" / "opencode"
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "opencode"


def _config_path() -> Path:
    return _opencode_dir() / "opencode.json"


def read_live_config():
    path = _config_path()
    if not path.exists():
        return None
    try:
        config = json5.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        raise HTTPException(400, f"Invalid opencode.json: {e}")
    if not isinstance(config, dict):
        raise HTTPException(400, "opencode.json root is not an object")
    return config


def write_live_config(config: dict) -> None:
    atomic_write(_config_path(),
                 json.dumps(config, indent=2, ensure_ascii=False).encode("utf-8"))


def _providers(config: dict) -> dict:
    providers = config.get("provider")
    if not isinstance(providers, dict):
        providers = {}
        config["provider"] = providers
    return providers


def sync_to_live(provider_id: str, settings_config: dict) -> None:
    config = read_live_config()
    if config is None:
        config = {"$schema": "https://opencode.ai/config.json"}
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
    db.set_current_provider(provider["id"], "opencode")
    return []


def import_live(db) -> dict:
    config = read_live_config()
    if config is None:
        raise HTTPException(404, "No OpenCode config found (~/.config/opencode/opencode.json)")
    providers = config.get("provider")
    if not isinstance(providers, dict) or not providers:
        raise HTTPException(404, "No providers found in opencode.json")
    count = 0
    for pid, pdata in providers.items():
        if db.get_provider(pid, "opencode"):
            continue
        data = json.loads(json.dumps(pdata))
        db.save_provider(pid, "opencode", data.get("name", pid), data, category="custom")
        count += 1
    return {"imported": count}


def load_presets() -> list:
    from presets.opencode_presets import OPENCODE_PRESETS
    return OPENCODE_PRESETS


def apply_api_key(settings_config: dict, api_key: str) -> dict:
    settings_config.setdefault("options", {})["apiKey"] = api_key
    return settings_config


OPENCODE_SPEC = AgentSpec(
    id="opencode",
    name="OpenCode",
    icon="💻",
    mode="additive",
    switch=switch,
    sync_to_live=sync_to_live,
    remove_from_live=remove_from_live,
    import_live=import_live,
    load_presets=load_presets,
    apply_api_key=apply_api_key,
)
