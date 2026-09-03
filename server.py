"""CC Switch Web — FastAPI server for AI agent model/provider switching."""
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

from storage import get_auth_path, get_db_path, migrate_legacy_storage
from db import Database
from config_ops import (
    get_claude_settings_path,
    get_openclaw_config_path,
)
from agents import AGENT_REGISTRY, VALID_APPS, get_agent, registry_payload
from models import (
    ProviderCreate,
    ProviderUpdate,
    ProviderResponse,
    SwitchResult,
    PresetResponse,
    LoginRequest,
)

app = FastAPI(title="CC Switch Web")
# Migrate legacy shared storage (~/.cc-switch) into the independent app dir
# (~/.cc-switch-web) before opening the database. One-time copy, originals kept.
migrate_legacy_storage()
db = Database(get_db_path())

# --- Auth ---
AUTH_FILE = get_auth_path()
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


def _get_presets(app_type: str) -> list:
    if app_type in _preset_cache:
        return _preset_cache[app_type]
    spec = get_agent(app_type)
    try:
        _preset_cache[app_type] = spec.load_presets() if spec.load_presets else []
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
    return registry_payload()


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

    spec = get_agent(app_type)
    if spec.sync_to_live:
        spec.sync_to_live(body.id, body.settings_config)

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

    spec = get_agent(app_type)
    if spec.sync_to_live:
        spec.sync_to_live(provider_id, settings_config)

    return {"id": provider_id, "name": name}


@app.delete("/api/providers/{provider_id}")
async def delete_provider(provider_id: str, app_type: str = Query(..., alias="app")):
    _validate_app(app_type)
    existing = db.get_provider(provider_id, app_type)
    if existing is None:
        raise HTTPException(404, "Provider not found")
    try:
        deleted = db.delete_provider(provider_id, app_type)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not deleted:
        raise HTTPException(404, "Provider not found")

    spec = get_agent(app_type)
    if spec.remove_from_live:
        spec.remove_from_live(provider_id, existing)

    return {"deleted": True}


# --- API: Switch ---

@app.post("/api/switch")
async def switch_provider(app_type: str = Query(..., alias="app"),
                          provider_id: str = Query(..., alias="id")):
    _validate_app(app_type)
    target = db.get_provider(provider_id, app_type)
    if target is None:
        raise HTTPException(404, "Provider not found")

    spec = get_agent(app_type)
    if spec.switch is None:
        raise HTTPException(400, f"Switch not implemented for {app_type}")
    warnings = spec.switch(db, target)

    return SwitchResult(success=True, message=f"Switched to {target['name']}", warnings=warnings)


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

    spec = get_agent(app_type)
    if api_key and spec.apply_api_key:
        settings_config = spec.apply_api_key(settings_config, api_key)

    db.save_provider(
        preset_id, app_type, preset["name"], settings_config,
        website_url=preset.get("website_url"), category=preset.get("category"),
        icon=preset.get("icon"), icon_color=preset.get("icon_color"),
    )

    if spec.sync_to_live:
        spec.sync_to_live(preset_id, settings_config)

    return {"id": preset_id, "name": preset["name"]}


# --- API: Import live config ---

@app.post("/api/import-live", status_code=201)
async def import_live(app_type: str = Query(..., alias="app")):
    _validate_app(app_type)
    spec = get_agent(app_type)
    if spec.import_live is None:
        raise HTTPException(400, f"Import not implemented for {app_type}")
    return spec.import_live(db)


# --- API: Fetch models from provider ---

_COMPAT_SUFFIXES = [
    "/api/claudecode", "/api/anthropic", "/apps/anthropic", "/api/coding",
    "/claudecode", "/anthropic", "/step_plan", "/coding", "/claude",
]


def _build_models_url_candidates(base_url: str) -> list[str]:
    base_url = base_url.rstrip("/")
    # 用户填写的地址永远第一个原样尝试（base/models），绝不主动补 /v1 改写地址；
    # 其余候选仅在前面全部 404/405 时作为回退探测，不影响保存的配置。
    candidates = [base_url + "/models"]
    if not base_url.endswith("/v1"):
        candidates.append(base_url + "/v1/models")

    for suffix in _COMPAT_SUFFIXES:
        if base_url.endswith(suffix):
            root = base_url[:-len(suffix)]
            candidates.append(root + "/v1/models")
            candidates.append(root + "/models")
            break

    deduped: list[str] = []
    for c in candidates:
        if c not in deduped:
            deduped.append(c)
    return deduped


# 火山方舟套餐网关（Agent Plan / Coding Plan）不提供 OpenAI 风格的 /models 接口，
# 任何候选地址探测都必然 404。这不是配置错误，提前识别并给出可操作的提示。
_ARK_PLAN_GATEWAYS = (
    "ark.cn-beijing.volces.com/api/plan",
    "ark.cn-beijing.volces.com/api/coding",
)


def _plan_gateway_hint(base_url: str) -> Optional[str]:
    u = base_url.lower()
    if not any(g in u for g in _ARK_PLAN_GATEWAYS):
        return None
    return (
        "火山方舟套餐网关（Agent Plan / Coding Plan）不提供模型列表接口，/models 返回 404 属官方行为；"
        "官方查询接口 ListArkCodingPlanModel 需火山云 AccessKey 签名，套餐 API Key 无法调用。"
        "请手动填写模型 ID：推荐官方别名 ark-code-latest（自动指向当前最新编码模型），"
        "完整清单见火山方舟控制台或文档 82379/2546386。"
    )


def _log_fetch(msg: str) -> None:
    """fetch-models 诊断日志：stdout + 应用数据目录 fetch-models.log 双写。

    用于排查“点了获取没结果”这类问题——无论服务由谁在哪个终端启动，
    日志都能事后从文件里读到。
    """
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [fetch-models] {msg}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        # Windows 控制台可能是 GBK，响应体里的特殊字符打不出来不能影响请求本身
        print(line.encode("ascii", "replace").decode("ascii"), flush=True)
    try:
        with open(AUTH_FILE.parent / "fetch-models.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


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
    # 只记 key 长度和末 4 位，避免完整密钥落盘
    _log_fetch(f"start base_url={base_url} key_len={len(api_key)} key_tail={api_key[-4:]}")

    for i, url in enumerate(candidates, 1):
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
                _log_fetch(f"[{i}/{len(candidates)}] {url} -> HTTP {resp.status}")
                try:
                    data = json.loads(raw)
                except Exception:
                    head = raw[:200].decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)[:200]
                    _log_fetch(f"[{i}/{len(candidates)}] non-JSON body head: {head}")
                    last_err = f"{url}: non-JSON response"
                    continue
                entries = data.get("data", []) if isinstance(data, dict) else []
                models = [m["id"] for m in entries if isinstance(m, dict) and m.get("id")]
                models.sort(key=str.lower)
                if not models:
                    _log_fetch(f"[{i}/{len(candidates)}] HTTP 200 but 0 models parsed; body head: {str(data)[:300]}")
                else:
                    _log_fetch(f"[{i}/{len(candidates)}] ok {len(models)} models: {', '.join(models[:8])}{' ...' if len(models) > 8 else ''}")
                return {"models": models}
        except ue.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", "replace")
            except Exception:
                pass
            body_head = err_body[:300]
            if e.code in (404, 405):
                _log_fetch(f"[{i}/{len(candidates)}] {url} -> HTTP {e.code}, trying next. body: {body_head}")
                last_err = f"HTTP {e.code} from {url}"
                continue
            detail = f"HTTP {e.code} from {url}"
            try:
                err = json.loads(err_body)
                detail = err.get("error", {}).get("message", detail) if isinstance(err, dict) else detail
            except Exception:
                pass
            _log_fetch(f"[{i}/{len(candidates)}] {url} -> HTTP {e.code} detail={detail} body: {body_head}")
            raise HTTPException(502, detail)
        except Exception as e:
            _log_fetch(f"[{i}/{len(candidates)}] {url} -> error {type(e).__name__}: {e}")
            last_err = f"{url}: {e}"
            continue

    _log_fetch(f"all {len(candidates)} candidates failed. Last: {last_err}")
    hint = _plan_gateway_hint(base_url)
    if hint:
        raise HTTPException(502, hint)
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
        "db_path": str(get_db_path()),
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
    print(f"  Database: {get_db_path()}")
    print(f"  Claude Code config: {get_claude_settings_path()}")
    print(f"  OpenClaw config: {get_openclaw_config_path()}")
    print()
    uvicorn.run(app, host=host, port=port)
