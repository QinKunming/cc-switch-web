"""Claude Desktop agent: exclusive mode, direct-gateway only (Win/macOS).

Paths: %LOCALAPPDATA%\\{Claude,Claude-3p}\\claude_desktop_config.json (macOS:
~/Library/Application Support/...). Switching writes deploymentMode ("1p"
official / "3p" third-party) into both configs, a gateway profile into
Claude-3p/configLibrary/<PROFILE_ID>.json, and updates the library _meta.json.
All four writes run under a byte-snapshot rollback.

settings_config shape (direct mode): {"env": {ANTHROPIC_BASE_URL,
ANTHROPIC_AUTH_TOKEN}, "inferenceModels": ["claude-sonnet-5", ...]?}.
Model ids must look like claude-<sonnet|opus|haiku|fable>-<suffix>
(Claude Desktop's fail-all validator rejects anything else). The local
proxy / modelRoutes mode is out of scope for the web version.

Credentials: ANTHROPIC_AUTH_TOKEN preferred, ANTHROPIC_API_KEY accepted as
fallback (bearer semantics are identical for Anthropic-protocol relays).
"""
import json
import os
import platform
import time
from pathlib import Path

from fastapi import HTTPException

from config_ops import atomic_write, get_home_dir, read_json, write_json

from agents.base import AgentSpec

PROFILE_ID = "00000000-0000-4000-8000-000000157210"
PROFILE_NAME = "CC Switch"
CONFIG_FILE = "claude_desktop_config.json"
CONFIG_LIBRARY_DIR = "configLibrary"
ONE_M_MARKER = "[1m]"
ANTHROPIC_CLAUDE_ROUTE_PREFIX = "anthropic/claude-"
CLAUDE_ROUTE_PREFIX = "claude-"
ROLE_PREFIXES = ("sonnet-", "opus-", "haiku-", "fable-")
ENTERPRISE_GATEWAY_KEYS = (
    "disableDeploymentModeChooser",
    "inferenceGatewayApiKey",
    "inferenceGatewayAuthScheme",
    "inferenceGatewayBaseUrl",
    "inferenceProvider",
)


# --- path detection ---

def _app_support_base() -> Path:
    test = os.environ.get("CC_SWITCH_TEST_HOME", "").strip()
    if test:
        return Path(test) / "AppData" / "Local"
    system = platform.system()
    if system == "Windows":
        local = os.environ.get("LOCALAPPDATA", "").strip()
        return Path(local) if local else get_home_dir() / "AppData" / "Local"
    if system == "Darwin":
        return get_home_dir() / "Library" / "Application Support"
    raise HTTPException(
        400, "Claude Desktop configuration is only supported on Windows and macOS")


def _pick_windows_claude_dir(base: Path, threep: bool) -> Path:
    exact = base / ("Claude-3p" if threep else "Claude")
    if exact.exists():
        return exact
    candidates = []
    if base.is_dir():
        for entry in base.iterdir():
            name = entry.name
            if entry.is_dir() and name.startswith("Claude") and (("-3p" in name) == threep):
                candidates.append(entry)
        candidates.sort()
    return candidates[0] if candidates else exact


def _config_paths() -> dict:
    base = _app_support_base()
    if platform.system() == "Darwin":
        normal, threep = base / "Claude", base / "Claude-3p"
    else:
        normal = _pick_windows_claude_dir(base, False)
        threep = _pick_windows_claude_dir(base, True)
    library = threep / CONFIG_LIBRARY_DIR
    return {
        "normal_config": normal / CONFIG_FILE,
        "threep_config": threep / CONFIG_FILE,
        "profile": library / f"{PROFILE_ID}.json",
        "meta": library / "_meta.json",
    }


# --- validation ---

def is_claude_safe_model_id(model_id: str) -> bool:
    normalized = model_id.strip().lower()
    if ONE_M_MARKER in normalized:
        return False
    if normalized.startswith(ANTHROPIC_CLAUDE_ROUTE_PREFIX):
        tail = normalized[len(ANTHROPIC_CLAUDE_ROUTE_PREFIX):]
    elif normalized.startswith(CLAUDE_ROUTE_PREFIX):
        tail = normalized[len(CLAUDE_ROUTE_PREFIX):]
    else:
        return False
    return any(tail.startswith(p) and len(tail) > len(p) for p in ROLE_PREFIXES)


def is_official(provider: dict) -> bool:
    return provider.get("category") == "official" or provider["id"] == "claude-desktop-official"


def _direct_gateway_credentials(provider: dict) -> tuple:
    env = provider["settings_config"].get("env")
    if not isinstance(env, dict):
        raise HTTPException(400, "Claude Desktop direct provider is missing env configuration")
    base_url = str(env.get("ANTHROPIC_BASE_URL") or "").strip()
    if not base_url:
        raise HTTPException(400, "Claude Desktop direct provider is missing ANTHROPIC_BASE_URL")
    api_key = str(env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_KEY") or "").strip()
    if not api_key:
        raise HTTPException(
            400, "Claude Desktop direct provider is missing ANTHROPIC_AUTH_TOKEN (Bearer Token)")
    return base_url, api_key


def _direct_model_specs(provider: dict) -> list:
    models = provider["settings_config"].get("inferenceModels")
    if models is None:
        return []
    if not isinstance(models, list):
        raise HTTPException(400, "Claude Desktop inferenceModels must be a list")
    specs = []
    for m in models:
        mid = m.strip() if isinstance(m, str) else ""
        if not mid:
            continue
        if not is_claude_safe_model_id(mid):
            raise HTTPException(
                400,
                f"Claude Desktop direct model must use a claude-* or anthropic/claude-* "
                f"name: {m}")
        specs.append(mid)
    return specs


def _validate_direct(provider: dict) -> None:
    if not isinstance(provider["settings_config"], dict):
        raise HTTPException(400, "Claude Desktop provider configuration must be a JSON object")
    _direct_model_specs(provider)
    _direct_gateway_credentials(provider)


# --- file helpers ---

def _read_json_or_empty(path: Path) -> dict:
    value = read_json(path)
    return value if isinstance(value, dict) else {}


def _write_deployment_mode(path: Path, mode: str) -> None:
    value = _read_json_or_empty(path)
    value["deploymentMode"] = mode
    write_json(path, value)


def _remove_enterprise_config(path: Path) -> None:
    if not path.exists():
        return
    value = _read_json_or_empty(path)
    enterprise = value.get("enterpriseConfig")
    if isinstance(enterprise, dict):
        for key in ENTERPRISE_GATEWAY_KEYS:
            enterprise.pop(key, None)
        if not enterprise:
            value.pop("enterpriseConfig", None)
        else:
            value["enterpriseConfig"] = enterprise
    write_json(path, value)


def _write_meta(path: Path, applied_profile_id) -> None:
    value = _read_json_or_empty(path)
    entries = [e for e in (value.get("entries") or [])
               if isinstance(e, dict) and e.get("id") != PROFILE_ID]
    if applied_profile_id:
        entries.append({"id": PROFILE_ID, "name": PROFILE_NAME})
        value["appliedId"] = applied_profile_id
    elif value.get("appliedId") == PROFILE_ID:
        next_id = next((e["id"] for e in entries if isinstance(e.get("id"), str)), None)
        if next_id:
            value["appliedId"] = next_id
        else:
            value.pop("appliedId", None)
    value["entries"] = entries
    write_json(path, value)


def _profile_to_settings(profile: dict) -> dict:
    sc = {"env": {
        "ANTHROPIC_BASE_URL": profile.get("inferenceGatewayBaseUrl", ""),
        "ANTHROPIC_AUTH_TOKEN": profile.get("inferenceGatewayApiKey", ""),
    }}
    models = profile.get("inferenceModels")
    if isinstance(models, list) and models:
        names = [m if isinstance(m, str) else m.get("name") for m in models]
        sc["inferenceModels"] = [n for n in names if isinstance(n, str) and n]
    return sc


# --- apply / restore with rollback ---

def _apply_direct_inner(paths: dict, provider: dict) -> None:
    base_url, api_key = _direct_gateway_credentials(provider)
    specs = _direct_model_specs(provider)
    profile = {
        "coworkEgressAllowedHosts": ["*"],
        "disableDeploymentModeChooser": True,
        "inferenceGatewayApiKey": api_key,
        "inferenceGatewayAuthScheme": "bearer",
        "inferenceGatewayBaseUrl": base_url,
        "inferenceProvider": "gateway",
    }
    if specs:
        profile["inferenceModels"] = specs
    _write_deployment_mode(paths["normal_config"], "3p")
    _write_deployment_mode(paths["threep_config"], "3p")
    write_json(paths["profile"], profile)
    _write_meta(paths["meta"], PROFILE_ID)


def _restore_official_inner(paths: dict) -> None:
    _write_deployment_mode(paths["normal_config"], "1p")
    _write_deployment_mode(paths["threep_config"], "1p")
    _remove_enterprise_config(paths["threep_config"])
    if paths["profile"].exists():
        paths["profile"].unlink()
    _write_meta(paths["meta"], None)


def _with_rollback(paths: dict, op) -> None:
    keys = ("normal_config", "threep_config", "profile", "meta")
    snapshots = [(paths[k], paths[k].read_bytes() if paths[k].exists() else None)
                 for k in keys]
    try:
        op()
    except BaseException as err:
        for path, content in snapshots:
            try:
                if content is None:
                    if path.exists():
                        path.unlink()
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    atomic_write(path, content)
            except OSError:
                pass
        raise


# --- AgentSpec surface ---

def switch(db, provider: dict) -> list[str]:
    paths = _config_paths()

    # backfill: current provider record takes over the live profile
    current = db.get_current_provider("claude-desktop")
    if current and paths["profile"].exists():
        profile = read_json(paths["profile"])
        if isinstance(profile, dict):
            db.update_provider_config(current["id"], "claude-desktop",
                                      _profile_to_settings(profile))

    if is_official(provider):
        _with_rollback(paths, lambda: _restore_official_inner(paths))
    else:
        _validate_direct(provider)
        _with_rollback(paths, lambda: _apply_direct_inner(paths, provider))

    db.set_current_provider(provider["id"], "claude-desktop")
    return []


def import_live(db) -> dict:
    paths = _config_paths()
    if not paths["profile"].exists():
        raise HTTPException(
            404, "No Claude Desktop CC Switch profile found (Claude-3p/configLibrary)")
    profile = read_json(paths["profile"])
    if not isinstance(profile, dict):
        raise HTTPException(404, "No Claude Desktop CC Switch profile found (Claude-3p/configLibrary)")
    sc = _profile_to_settings(profile)
    provider_id = f"imported-{int(time.time())}"
    db.save_provider(provider_id, "claude-desktop", "Imported Config", sc, category="custom")
    return {"id": provider_id, "name": "Imported Config"}


def load_presets() -> list:
    from presets.claude_desktop_presets import CLAUDE_DESKTOP_PRESETS
    return CLAUDE_DESKTOP_PRESETS


def apply_api_key(settings_config: dict, api_key: str) -> dict:
    env = settings_config.setdefault("env", {})
    key_field = "ANTHROPIC_AUTH_TOKEN"
    for k in env:
        if "API_KEY" in k or "AUTH_TOKEN" in k:
            key_field = k
            break
    env[key_field] = api_key
    return settings_config


CLAUDE_DESKTOP_SPEC = AgentSpec(
    id="claude-desktop",
    name="Claude Desktop",
    icon="🖥️",
    mode="exclusive",
    switch=switch,
    import_live=import_live,
    load_presets=load_presets,
    apply_api_key=apply_api_key,
)
