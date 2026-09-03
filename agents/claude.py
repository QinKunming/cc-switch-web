"""Claude Code agent: exclusive mode, live at ~/.claude/settings.json."""
import time

from fastapi import HTTPException

from config_ops import import_claude_live, read_claude_settings, write_claude_settings

from agents.base import AgentSpec


def switch(db, provider: dict) -> list[str]:
    live = read_claude_settings()
    current = db.get_current_provider("claude")
    if current and live:
        db.update_provider_config(current["id"], "claude", live)
    db.set_current_provider(provider["id"], "claude")
    # Preserve non-env fields (e.g. skipDangerousModePermissionPrompt) from live settings
    merged = dict(live) if live else {}
    merged["env"] = provider["settings_config"].get("env", {})
    write_claude_settings(merged)
    return []


def import_live(db) -> dict:
    config = import_claude_live()
    if config is None:
        raise HTTPException(404, "No Claude Code settings.json found")
    provider_id = f"imported-{int(time.time())}"
    db.save_provider(provider_id, "claude", "Imported Config", config, category="custom")
    return {"id": provider_id, "name": "Imported Config"}


def load_presets() -> list:
    from presets.claude_presets import CLAUDE_PRESETS
    return CLAUDE_PRESETS


def apply_api_key(settings_config: dict, api_key: str) -> dict:
    env = settings_config.setdefault("env", {})
    key_field = "ANTHROPIC_AUTH_TOKEN"
    for k in env:
        if "API_KEY" in k or "AUTH_TOKEN" in k:
            key_field = k
            break
    env[key_field] = api_key
    return settings_config


CLAUDE_SPEC = AgentSpec(
    id="claude",
    name="Claude Code",
    icon="🤖",
    mode="exclusive",
    switch=switch,
    import_live=import_live,
    load_presets=load_presets,
    apply_api_key=apply_api_key,
)
