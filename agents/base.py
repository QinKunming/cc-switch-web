"""AgentSpec: one place per agent for switch/sync/import/preset behavior.

mode:
  - "exclusive": one active provider at a time (claude, claude-desktop, codex,
    gemini, grokbuild). switch() backfills live -> old provider, sets current,
    then writes the live config.
  - "additive": all providers coexist in the agent's native config file
    (opencode, openclaw, hermes, pi). sync_to_live()/remove_from_live() keep
    individual entries in sync; switch() also marks current for the UI badge.
"""
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class AgentSpec:
    id: str                       # cc-switch AppType string, e.g. "claude-desktop"
    name: str                     # display name
    icon: str                     # emoji
    mode: str                     # "exclusive" | "additive"
    configurable: bool = True
    # (db, provider_dict) -> list of warning strings; raise HTTPException on failure
    switch: Optional[Callable] = None
    # additive: (provider_id, settings_config) — called after create/update
    sync_to_live: Optional[Callable] = None
    # additive: (provider_id, provider_dict) — called after delete
    remove_from_live: Optional[Callable] = None
    # (db) -> {"id": ..., "name": ...} or {"imported": n}; 404 when nothing to import
    import_live: Optional[Callable] = None
    # () -> list of preset dicts (lazy, cached by the caller)
    load_presets: Optional[Callable] = None
    # (settings_config, api_key) -> settings_config with the key injected
    apply_api_key: Optional[Callable] = None
