"""Hermes agent: additive mode, live at <hermes_home>/config.yaml (YAML).

Directory resolution matches Hermes' own get_hermes_home(): HERMES_HOME env
-> Windows %LOCALAPPDATA%\\hermes (fallback ~/AppData/Local/hermes)
-> ~/.hermes. The CC_SWITCH_TEST_HOME sandbox always wins for testing.

Writes are text-level YAML section replacements (never a full round-trip)
so user comments and unrelated sections like mcp_servers survive. Reads
heal duplicate top-level keys first (keep-last), matching Hermes/PyYAML
last-wins semantics. The v12+ `providers:` dict overlay is left alone:
only `custom_providers:` entries are managed here.

settings_config shape (snake_case): {"name", "base_url", "api_key",
"api_mode", "models": [{"id", "name", "context_length"}, ...]}.
"""
import os
import platform
from pathlib import Path

import yaml
from fastapi import HTTPException

from config_ops import atomic_write, get_home_dir

from agents.base import AgentSpec

# camelCase keys from legacy DeepLink imports -> Hermes snake_case schema
_KEY_ALIASES = [
    ("baseUrl", "base_url"),
    ("apiKey", "api_key"),
    ("apiMode", "api_mode"),
    ("maxTokens", "max_tokens"),
    ("contextLength", "context_length"),
]
# UI-only markers and unmappable legacy fields that must never reach YAML
_LEGACY_DROP = ["api", "_cc_source", "provider_key"]


def _hermes_dir() -> Path:
    test = os.environ.get("CC_SWITCH_TEST_HOME", "").strip()
    if test:
        return Path(test) / ".hermes"
    override = os.environ.get("HERMES_HOME", "").strip()
    if override:
        return Path(override)
    if platform.system() == "Windows":
        local = os.environ.get("LOCALAPPDATA", "").strip()
        base = Path(local) if local else get_home_dir() / "AppData" / "Local"
        return base / "hermes"
    return get_home_dir() / ".hermes"


def _config_path() -> Path:
    return _hermes_dir() / "config.yaml"


# --- top-level key line scanning (CRLF tolerant, column-0 keys only) ---

def _is_top_level_key_line(line: str) -> bool:
    if not line:
        return False
    if line[0] in " \t#-":
        return False
    colon = line.find(":")
    if colon == -1:
        return False
    after = line[colon + 1:]
    return after == "" or after[0] in " \t\r"


def _deduplicate_top_level_keys(raw: str) -> str:
    """Drop duplicate top-level sections, keeping the LAST occurrence."""
    sections = []  # (key, byte offset)
    offset = 0
    for line in raw.split("\n"):
        if _is_top_level_key_line(line):
            sections.append((line[:line.find(":")], offset))
        offset += len(line) + 1

    counts: dict[str, int] = {}
    for key, _ in sections:
        counts[key] = counts.get(key, 0) + 1
    if all(c <= 1 for c in counts.values()):
        return raw

    head_end = sections[0][1] if sections else len(raw)
    result = raw[:head_end]
    remaining = dict(counts)
    for i, (key, start) in enumerate(sections):
        end = sections[i + 1][1] if i + 1 < len(sections) else len(raw)
        remaining[key] -= 1
        if remaining[key] > 0:
            continue  # a later occurrence exists — drop this one
        result += raw[start:end]
    return result


def _find_section_range(raw: str, section_key: str):
    """(start, end) byte range of a top-level section, or None."""
    target = f"{section_key}:"
    section_start = None
    offset = 0
    for line in raw.split("\n"):
        if section_start is None and _is_top_level_key_line(line) and line.startswith(target):
            after = line[len(target):]
            if after == "" or after[0] in " \t\r":
                section_start = offset
        elif section_start is not None and _is_top_level_key_line(line):
            return section_start, offset
        offset += len(line) + 1
    return (section_start, len(raw)) if section_start is not None else None


def _remove_all_sections(raw: str, section_key: str) -> str:
    result = ""
    rest = raw
    while True:
        found = _find_section_range(rest, section_key)
        if found is None:
            break
        start, end = found
        result += rest[:start]
        rest = rest[end:]
    return result + rest


def _replace_yaml_section(raw: str, section_key: str, value) -> str:
    serialized = yaml.safe_dump(
        {section_key: value}, default_flow_style=False,
        allow_unicode=True, sort_keys=False,
    )
    found = _find_section_range(raw, section_key)
    if found is None:
        result = raw
        if result and not result.endswith("\n"):
            result += "\n"
        result += serialized
        return result if result.endswith("\n") else result + "\n"

    start, end = found
    result = raw[:start] + serialized
    remainder = _remove_all_sections(raw[end:], section_key)
    if not serialized.endswith("\n") and remainder and not remainder.startswith("\n"):
        result += "\n"
    return result + remainder


def write_yaml_section(section_key: str, value) -> None:
    path = _config_path()
    raw = path.read_text(encoding="utf-8") if path.exists() else ""
    raw = _deduplicate_top_level_keys(raw)
    new_raw = _replace_yaml_section(raw, section_key, value)
    if new_raw != raw:
        atomic_write(path, new_raw.encode("utf-8"))


def _read_config_lenient() -> dict:
    """Parsed config for in-memory merges; {} on missing/malformed file."""
    path = _config_path()
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return {}
    try:
        config = yaml.safe_load(_deduplicate_top_level_keys(raw))
    except yaml.YAMLError:
        return {}
    return config if isinstance(config, dict) else {}


# --- provider entry shaping ---

def _sanitize_provider(entry: dict) -> dict:
    """camelCase -> snake_case healing; drop UI-only/legacy fields."""
    clean = {k: v for k, v in entry.items() if k not in _LEGACY_DROP}
    for frm, to in _KEY_ALIASES:
        if frm in clean:
            clean.setdefault(to, clean.pop(frm))  # snake_case wins on conflict
    return clean


def _models_array_to_dict(models: list) -> dict:
    """[{"id": "foo", ...}] -> {"foo": {...}} (entries without id dropped)."""
    out = {}
    for item in models:
        if not isinstance(item, dict):
            continue
        mid = item.get("id")
        if not isinstance(mid, str) or not mid.strip():
            continue
        out[mid.strip()] = {k: v for k, v in item.items() if k != "id"}
    return out


def _entry_first_model(entry: dict):
    models = entry.get("models")
    if isinstance(models, dict):
        return next(iter(models), None)
    if isinstance(models, list):
        first = next(iter(models), None)
        if isinstance(first, dict) and isinstance(first.get("id"), str):
            return first["id"].strip() or None
    return None


def set_provider(name: str, settings_config: dict) -> None:
    entry = _sanitize_provider(settings_config)
    if isinstance(entry.get("models"), list):
        entry["models"] = _models_array_to_dict(entry["models"])
    entry["name"] = name
    first_model = _entry_first_model(entry)
    if first_model:
        entry["model"] = first_model
    else:
        entry.pop("model", None)

    config = _read_config_lenient()
    providers = config.get("custom_providers")
    providers = [p for p in providers if isinstance(p, dict)] if isinstance(providers, list) else []

    for i, existing in enumerate(providers):
        if existing.get("name") == name:
            merged = dict(entry)
            for k, v in existing.items():  # keep on-disk fields the payload lacked
                merged.setdefault(k, v)
            providers[i] = merged
            break
    else:
        providers.append(entry)

    write_yaml_section("custom_providers", providers)


def remove_from_live(provider_id: str, provider: dict) -> None:
    config = _read_config_lenient()
    providers = config.get("custom_providers")
    if not isinstance(providers, list):
        return
    kept = [p for p in providers
            if not (isinstance(p, dict) and p.get("name") == provider_id)]
    if len(kept) != len(providers):
        write_yaml_section("custom_providers", kept)


def _apply_switch_defaults(provider_id: str, settings_config: dict) -> None:
    """model.provider always follows the switch; model.default only when the
    new provider declares a model (otherwise the previous default survives)."""
    models = settings_config.get("models")
    first_model = None
    if isinstance(models, list) and models:
        first = models[0]
        if isinstance(first, dict) and isinstance(first.get("id"), str):
            first_model = first["id"].strip() or None

    config = _read_config_lenient()
    current = config.get("model")
    current = dict(current) if isinstance(current, dict) else {}
    current["provider"] = provider_id
    if first_model:
        current["default"] = first_model
    write_yaml_section("model", current)


def switch(db, provider: dict) -> list[str]:
    set_provider(provider["id"], provider["settings_config"])
    _apply_switch_defaults(provider["id"], provider["settings_config"])
    db.set_current_provider(provider["id"], "hermes")
    return []


def import_live(db) -> dict:
    config = _read_config_lenient()
    providers = config.get("custom_providers")
    if not isinstance(providers, list) or not providers:
        raise HTTPException(404, "No custom_providers found in Hermes config.yaml")
    count = 0
    for entry in providers:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name or db.get_provider(name, "hermes"):
            continue
        data = _provider_for_db(entry)
        db.save_provider(name, "hermes", name, data, category="custom")
        count += 1
    return {"imported": count}


def _provider_for_db(entry: dict) -> dict:
    """YAML entry -> DB settings_config: models dict -> array, singular model dropped."""
    data = {k: v for k, v in entry.items() if k != "model"}
    models = data.get("models")
    if isinstance(models, dict):
        arr = []
        for mid, mdata in models.items():
            item = dict(mdata) if isinstance(mdata, dict) else {}
            item["id"] = mid
            arr.append(item)
        data["models"] = arr
    return data


def load_presets() -> list:
    from presets.hermes_presets import HERMES_PRESETS
    return HERMES_PRESETS


def apply_api_key(settings_config: dict, api_key: str) -> dict:
    settings_config["api_key"] = api_key
    return settings_config


HERMES_SPEC = AgentSpec(
    id="hermes",
    name="Hermes",
    icon="📡",
    mode="additive",
    switch=switch,
    sync_to_live=lambda provider_id, sc: set_provider(provider_id, sc),
    remove_from_live=remove_from_live,
    import_live=import_live,
    load_presets=load_presets,
    apply_api_key=apply_api_key,
)
