"""CC Switch Web — FastAPI server for Claude Code and OpenClaw model switching."""
import hashlib
import json
import os
import random
import string
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, HTTPException, Request, Response, Cookie
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from db import Database
from config_ops import (
    get_claude_settings_path,
    get_openclaw_config_path,
    read_claude_settings,
    write_claude_settings,
    read_openclaw_config,
    write_openclaw_config,
    openclaw_get_providers,
    openclaw_set_provider,
    openclaw_remove_provider,
    openclaw_get_default_model,
    openclaw_set_default_model,
    import_claude_live,
    import_openclaw_live,
    sanitize_claude_settings,
)
from models import (
    ProviderCreate,
    ProviderUpdate,
    ProviderResponse,
    SwitchResult,
    PresetResponse,
    LoginRequest,
)

app = FastAPI(title="CC Switch Web")
db = Database()

# --- Auth ---
AUTH_FILE = Path.home() / ".cc-switch" / "web-auth.json"
SESSION_COOKIE = "cc_switch_session"
_sessions: dict[str, float] = {}  # token -> expire_time
SESSION_TTL = 86400 * 7  # 7 days
_captcha_store: dict[str, str] = {}  # session_id -> answer


def _load_auth_config() -> dict:
    if AUTH_FILE.exists():
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_auth_config(cfg: dict) -> None:
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def _init_default_auth() -> None:
    if not AUTH_FILE.exists():
        default_user = "admin"
        default_pass = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        hashed = hashlib.sha256(default_pass.encode()).hexdigest()
        _save_auth_config({"users": {default_user: hashed}})
        print(f"  Default login: admin / {default_pass}")
        print(f"  Change password in {AUTH_FILE}")


def _check_auth(session: Optional[str] = None) -> bool:
    if not session or session not in _sessions:
        return False
    if _sessions[session] < time.time():
        _sessions.pop(session, None)
        return False
    return True


def _hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


# --- Captcha ---
def _generate_captcha() -> tuple[str, str]:
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    captcha_id = uuid.uuid4().hex[:12]
    answer = str(a + b)
    _captcha_store[captcha_id] = answer
    return captcha_id, f"{a} + {b} = ?"


def _verify_captcha(captcha_id: str, answer: str) -> bool:
    expected = _captcha_store.pop(captcha_id, None)
    if expected is None:
        return False
    return expected.strip() == answer.strip()


# --- Presets (lazy loaded) ---
_preset_cache: dict[str, list] = {}

AGENT_REGISTRY = {
    "claude": {"name": "Claude Code", "icon": "🤖", "configurable": True},
    "openclaw": {"name": "OpenClaw", "icon": "🐾", "configurable": True},
    "opencode": {"name": "OpenCode", "icon": "🔵", "configurable": False},
    "codex": {"name": "Codex", "icon": "⚡", "configurable": False},
}

VALID_APPS = set(AGENT_REGISTRY.keys())


def _get_presets(app_type: str) -> list:
    if app_type in _preset_cache:
        return _preset_cache[app_type]
    try:
        if app_type == "claude":
            from presets.claude_presets import CLAUDE_PRESETS
            _preset_cache[app_type] = CLAUDE_PRESETS
        elif app_type == "openclaw":
            from presets.openclaw_presets import OPENCLAW_PRESETS
            _preset_cache[app_type] = OPENCLAW_PRESETS
        else:
            _preset_cache[app_type] = []
    except ImportError:
        _preset_cache[app_type] = []
    return _preset_cache[app_type]


def _validate_app(app: str):
    if app not in VALID_APPS:
        raise HTTPException(400, f"Invalid app type: {app}. Must be one of {VALID_APPS}")


def _provider_to_response(r: dict) -> ProviderResponse:
    return ProviderResponse(
        id=r["id"],
        name=r["name"],
        app_type=r["app_type"],
        settings_config=r["settings_config"],
        website_url=r.get("website_url"),
        category=r.get("category"),
        notes=r.get("notes"),
        icon=r.get("icon"),
        icon_color=r.get("icon_color"),
        is_current=r.get("is_current", False),
    )


# --- Static files ---

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse(STATIC_DIR / "index.html")


# --- Auth API ---

@app.get("/api/captcha")
async def get_captcha():
    captcha_id, question = _generate_captcha()
    return {"captcha_id": captcha_id, "question": question}


@app.post("/api/login")
async def login(body: LoginRequest, response: Response):
    if not _verify_captcha(body.captcha_id, body.captcha_answer):
        raise HTTPException(401, "Captcha verification failed")

    auth_cfg = _load_auth_config()
    users = auth_cfg.get("users", {})
    hashed = _hash_password(body.password)
    if body.username not in users or users[body.username] != hashed:
        raise HTTPException(401, "Invalid username or password")

    token = uuid.uuid4().hex
    _sessions[token] = time.time() + SESSION_TTL
    response = JSONResponse({"success": True, "token": token})
    response.set_cookie(
        key=SESSION_COOKIE, value=token, max_age=SESSION_TTL,
        httponly=True, samesite="lax",
    )
    return response


@app.post("/api/logout")
async def logout(session: Optional[str] = Cookie(None, alias=SESSION_COOKIE)):
    if session:
        _sessions.pop(session, None)
    response = JSONResponse({"success": True})
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/api/check-auth")
async def check_auth(session: Optional[str] = Cookie(None, alias=SESSION_COOKIE)):
    return {"authenticated": _check_auth(session)}


# --- Middleware for auth ---

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    # Public paths
    public = {"/", "/api/captcha", "/api/login", "/api/check-auth", "/api/health"}
    if path in public:
        return await call_next(request)
    if path.startswith("/api/"):
        session = request.cookies.get(SESSION_COOKIE)
        if not _check_auth(session):
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return await call_next(request)


# --- API: Agents ---

@app.get("/api/agents")
async def list_agents():
    return [{"id": k, **v} for k, v in AGENT_REGISTRY.items()]


# --- API: Providers ---

@app.get("/api/providers")
async def list_providers(app_type: str = Query(..., alias="app")):
    _validate_app(app_type)
    providers = db.get_providers(app_type)
    return [_provider_to_response(p) for p in providers]


@app.get("/api/providers/{provider_id}")
async def get_provider(provider_id: str, app_type: str = Query(..., alias="app")):
    _validate_app(app_type)
    p = db.get_provider(provider_id, app_type)
    if p is None:
        raise HTTPException(404, "Provider not found")
    return _provider_to_response(p)


@app.post("/api/providers", status_code=201)
async def create_provider(body: ProviderCreate, app_type: str = Query(..., alias="app")):
    _validate_app(app_type)
    existing = db.get_provider(body.id, app_type)
    if existing:
        raise HTTPException(409, f"Provider '{body.id}' already exists")
    db.save_provider(
        body.id, app_type, body.name, body.settings_config,
        website_url=body.website_url, category=body.category,
        notes=body.notes, icon=body.icon, icon_color=body.icon_color,
    )

    if app_type == "openclaw":
        _sync_openclaw_provider_to_live(body.id, body.settings_config)

    return {"id": body.id, "name": body.name}


@app.put("/api/providers/{provider_id}")
async def update_provider(provider_id: str, body: ProviderUpdate,
                          app_type: str = Query(..., alias="app")):
    _validate_app(app_type)
    existing = db.get_provider(provider_id, app_type)
    if existing is None:
        raise HTTPException(404, "Provider not found")

    updates = body.model_dump(exclude_none=True)
    name = updates.pop("name", existing["name"])
    settings_config = updates.pop("settings_config", existing["settings_config"])

    db.save_provider(provider_id, app_type, name, settings_config, **updates)

    if app_type == "openclaw":
        _sync_openclaw_provider_to_live(provider_id, settings_config)

    return {"id": provider_id, "name": name}


@app.delete("/api/providers/{provider_id}")
async def delete_provider(provider_id: str, app_type: str = Query(..., alias="app")):
    _validate_app(app_type)
    try:
        deleted = db.delete_provider(provider_id, app_type)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not deleted:
        raise HTTPException(404, "Provider not found")

    if app_type == "openclaw":
        config = read_openclaw_config()
        if config:
            openclaw_remove_provider(config, provider_id)
            write_openclaw_config(config)

    return {"deleted": True}


# --- API: Switch ---

@app.post("/api/switch")
async def switch_provider(app_type: str = Query(..., alias="app"),
                          provider_id: str = Query(..., alias="id")):
    _validate_app(app_type)
    target = db.get_provider(provider_id, app_type)
    if target is None:
        raise HTTPException(404, "Provider not found")

    warnings = []

    if app_type == "claude":
        _switch_claude(target, warnings)
    elif app_type == "openclaw":
        _switch_openclaw(target, warnings)
    else:
        raise HTTPException(400, f"Switch not implemented for {app_type}")

    return SwitchResult(success=True, message=f"Switched to {target['name']}", warnings=warnings)


def _switch_claude(target: dict, warnings: list[str]):
    live = read_claude_settings()
    current = db.get_current_provider("claude")
    if current and live:
        db.update_provider_config(current["id"], "claude", live)
    db.set_current_provider(target["id"], "claude")
    # Preserve non-env fields (e.g. skipDangerousModePermissionPrompt) from live settings
    merged = dict(live) if live else {}
    merged["env"] = target["settings_config"].get("env", {})
    write_claude_settings(merged)


def _switch_openclaw(target: dict, warnings: list[str]):
    config = read_openclaw_config()
    if config is None:
        config = {"models": {"mode": "merge", "providers": {}}, "agents": {"defaults": {}}}
    clean_config = _sanitize_oc_models(target["settings_config"])
    _sync_openclaw_provider_to_live(target["id"], clean_config, config)
    models = clean_config.get("models", [])
    if models:
        primary = f"{target['id']}/{models[0]['id']}"
        fallbacks = [f"{target['id']}/{m['id']}" for m in models[1:4]] if len(models) > 1 else None
        openclaw_set_default_model(config, primary, fallbacks)
    write_openclaw_config(config)
    db.set_current_provider(target["id"], "openclaw")


def _sanitize_oc_models(settings_config: dict) -> dict:
    """Deep-copy settings_config and strip fields OpenClaw doesn't recognize from model entries."""
    clean = json.loads(json.dumps(settings_config))
    for m in clean.get("models", []):
        m.pop("alias", None)
    return clean


def _sync_openclaw_provider_to_live(provider_id: str, settings_config: dict,
                                    config: Optional[dict] = None):
    if config is None:
        config = read_openclaw_config()
    if config is None:
        config = {"models": {"mode": "merge", "providers": {}}, "agents": {"defaults": {}}}
    openclaw_set_provider(config, provider_id, _sanitize_oc_models(settings_config))
    write_openclaw_config(config)


# --- API: Current ---

@app.get("/api/current")
async def get_current(app_type: str = Query(..., alias="app")):
    _validate_app(app_type)
    p = db.get_current_provider(app_type)
    if p is None:
        return {"current": None}
    return {"current": _provider_to_response(p)}


# --- API: Presets ---

@app.get("/api/presets")
async def list_presets(app_type: str = Query(..., alias="app")):
    _validate_app(app_type)
    return _get_presets(app_type)


@app.post("/api/presets/apply", status_code=201)
async def apply_preset(preset_id: str = Query(..., alias="id"),
                       app_type: str = Query(..., alias="app"),
                       api_key: Optional[str] = None):
    _validate_app(app_type)
    presets = _get_presets(app_type)
    preset = next((p for p in presets if p["id"] == preset_id), None)
    if preset is None:
        raise HTTPException(404, f"Preset '{preset_id}' not found")

    existing = db.get_provider(preset_id, app_type)
    if existing:
        raise HTTPException(409, f"Provider '{preset_id}' already exists")

    settings_config = json.loads(json.dumps(preset["settings_config"]))

    if api_key:
        if app_type == "claude":
            env = settings_config.get("env", {})
            key_field = "ANTHROPIC_AUTH_TOKEN"
            for k in env:
                if "API_KEY" in k or "AUTH_TOKEN" in k:
                    key_field = k
                    break
            env[key_field] = api_key
        elif app_type == "openclaw":
            settings_config["apiKey"] = api_key

    db.save_provider(
        preset_id, app_type, preset["name"], settings_config,
        website_url=preset.get("website_url"), category=preset.get("category"),
        icon=preset.get("icon"), icon_color=preset.get("icon_color"),
    )

    if app_type == "openclaw":
        _sync_openclaw_provider_to_live(preset_id, settings_config)

    return {"id": preset_id, "name": preset["name"]}


# --- API: Import live config ---

@app.post("/api/import-live", status_code=201)
async def import_live(app_type: str = Query(..., alias="app")):
    _validate_app(app_type)

    if app_type == "claude":
        config = import_claude_live()
        if config is None:
            raise HTTPException(404, "No Claude Code settings.json found")
        provider_id = f"imported-{int(time.time())}"
        db.save_provider(provider_id, "claude", "Imported Config", config,
                         category="custom")
    elif app_type == "openclaw":
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
        provider_id = "bulk-import"
        return {"imported": count}
    else:
        raise HTTPException(400, f"Import not implemented for {app_type}")

    return {"id": provider_id, "name": "Imported Config"}


# --- API: Fetch models from provider ---

_COMPAT_SUFFIXES = [
    "/api/claudecode", "/api/anthropic", "/apps/anthropic", "/api/coding",
    "/claudecode", "/anthropic", "/step_plan", "/coding", "/claude",
]


def _build_models_url_candidates(base_url: str) -> list[str]:
    base_url = base_url.rstrip("/")
    candidates = []

    if base_url.endswith("/v1"):
        candidates.append(base_url + "/models")
    else:
        candidates.append(base_url + "/v1/models")

    for suffix in _COMPAT_SUFFIXES:
        if base_url.endswith(suffix):
            root = base_url[:-len(suffix)]
            candidates.append(root + "/v1/models")
            candidates.append(root + "/models")
            break

    return candidates


@app.post("/api/fetch-models")
async def fetch_models(request: Request):
    import urllib.request
    import urllib.error as ue

    body = await request.json()
    base_url = body.get("base_url", "").rstrip("/")
    api_key = body.get("api_key", "")

    if not base_url:
        raise HTTPException(400, "base_url is required")
    if not api_key:
        raise HTTPException(400, "api_key is required")

    candidates = _build_models_url_candidates(base_url)
    last_err = "No candidate URLs"

    for url in candidates:
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                models = [m["id"] for m in data.get("data", []) if m.get("id")]
                models.sort(key=str.lower)
                return {"models": models}
        except ue.HTTPError as e:
            if e.code in (404, 405):
                last_err = f"HTTP {e.code} from {url}"
                continue
            detail = f"HTTP {e.code} from {url}"
            try:
                err = json.loads(e.read())
                detail = err.get("error", {}).get("message", detail) if isinstance(err, dict) else detail
            except Exception:
                pass
            raise HTTPException(502, detail)
        except Exception as e:
            last_err = f"{url}: {e}"
            continue

    raise HTTPException(502, f"All candidates failed. Tried: {', '.join(candidates)}. Last: {last_err}")


# --- API: Health ---

@app.get("/api/health")
async def health():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"
    return {
        "status": "ok",
        "local_ip": local_ip,
        "agents": list(AGENT_REGISTRY.keys()),
        "claude_settings_path": str(get_claude_settings_path()),
        "openclaw_config_path": str(get_openclaw_config_path()),
        "claude_settings_exists": get_claude_settings_path().exists(),
        "openclaw_config_exists": get_openclaw_config_path().exists(),
    }


# --- Entrypoint ---

if __name__ == "__main__":
    import uvicorn
    import socket

    _init_default_auth()

    host = "0.0.0.0"
    port = 8787
    for arg in sys.argv[1:]:
        if arg.startswith("--host="):
            host = arg.split("=", 1)[1]
        elif arg.startswith("--port="):
            port = int(arg.split("=", 1)[1])

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = host

    print(f"\n  CC Switch Web")
    print(f"  Local:   http://{local_ip}:{port}")
    print(f"  Network: http://{local_ip}:{port}")
    print(f"  Claude Code config: {get_claude_settings_path()}")
    print(f"  OpenClaw config: {get_openclaw_config_path()}")
    print()
    uvicorn.run(app, host=host, port=port)
