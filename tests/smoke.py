"""End-to-end smoke test against a sandboxed server.

Usage: python tests/smoke.py [agent ...]   (default: all registered agents)

Boots server.py with CC_SWITCH_TEST_HOME pointing at a throwaway sandbox,
logs in via the captcha flow, then exercises provider CRUD / switch / import
for each requested agent and asserts on the files written inside the sandbox.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8799
BASE = f"http://127.0.0.1:{PORT}"
SMOKE_PASS = "smoke-test-pw"

_server: subprocess.Popen | None = None
_sb: Path | None = None
_cookie = ""


def http(method: str, path: str, body: dict | None = None) -> tuple[int, dict | list | str]:
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if _cookie:
        req.add_header("Cookie", _cookie)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def login():
    global _cookie
    st, d = http("GET", "/api/captcha")
    assert st == 200, (st, d)
    m = re.match(r"(\d+) \+ (\d+) = \?", d["question"])
    answer = str(int(m.group(1)) + int(m.group(2)))
    st, d = http("POST", "/api/login",
                 {"username": "admin", "password": SMOKE_PASS,
                  "captcha_id": d["captcha_id"], "captcha_answer": answer})
    assert st == 200, (st, d)
    _cookie = f"cc_switch_session={d['token']}"


def rj(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def start_server(fixture: "callable"):
    global _server, _sb
    _sb = Path(tempfile.mkdtemp(prefix="ccsw-smoke-"))
    fixture(_sb)
    env = dict(os.environ)
    env["CC_SWITCH_TEST_HOME"] = str(_sb)
    # auth file must pre-exist with our password so login is deterministic
    import hashlib
    auth_dir = _sb / ".cc-switch-web"
    auth_dir.mkdir(parents=True, exist_ok=True)
    (auth_dir / "web-auth.json").write_text(json.dumps(
        {"users": {"admin": hashlib.sha256(b"smoke-test-pw").hexdigest()}}))
    # server log goes to a file: a PIPE we never drain would fill its buffer
    # and block uvicorn mid-run
    log = open(_sb / "server.log", "w", encoding="utf-8", errors="replace")
    _server = subprocess.Popen(
        [sys.executable, str(ROOT / "server.py"), f"--port={PORT}"],
        cwd=ROOT, env=env,
        stdout=log, stderr=subprocess.STDOUT,
    )
    for _ in range(50):
        if _server.poll() is not None:
            log.close()
            out = (_sb / "server.log").read_text(encoding="utf-8", errors="replace")
            stop_server()
            raise RuntimeError(f"server exited early:\n{out[-2000:]}")
        try:
            st, _ = http("GET", "/api/health")
            if st == 200:
                break
        except Exception:
            time.sleep(0.2)
    else:
        log.close()
        stop_server()
        raise RuntimeError("server did not start")
    login()


def stop_server():
    global _server, _sb
    if _server:
        _server.terminate()
        try:
            _server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _server.kill()
        _server = None
    if _sb:
        shutil.rmtree(_sb, ignore_errors=True)
        _sb = None


# ---------------- fixtures ----------------

def fixture_default(sb: Path):
    """Live configs for every agent + a legacy DB with one claude provider."""
    (sb / ".claude").mkdir(parents=True)
    (sb / ".claude" / "settings.json").write_text(json.dumps({
        "env": {"ANTHROPIC_BASE_URL": "https://old.example.com",
                "ANTHROPIC_AUTH_TOKEN": "sk-old"},
        "permissions": {"allow": ["Bash"]},
    }))
    (sb / ".openclaw").mkdir(parents=True)
    (sb / ".openclaw" / "openclaw.json").write_text(json.dumps({
        "models": {"mode": "merge", "providers": {
            "live-oc": {"baseUrl": "https://live.example.com/v1", "apiKey": "k1",
                        "api": "openai-completions",
                        "models": [{"id": "m1", "name": "M1"}]}}},
        "agents": {"defaults": {}},
    }))
    # codex
    (sb / ".codex").mkdir(parents=True)
    (sb / ".codex" / "auth.json").write_text(json.dumps({"OPENAI_API_KEY": "sk-codex-old"}))
    (sb / ".codex" / "config.toml").write_text(
        'model_provider = "custom"\nmodel = "old-model"\n\n'
        '[model_providers.custom]\nname = "Old"\n'
        'base_url = "https://old-codex.example.com/v1"\n'
        'wire_api = "responses"\nrequires_openai_auth = true\n')
    # gemini
    (sb / ".gemini").mkdir(parents=True)
    (sb / ".gemini" / ".env").write_text(
        "GEMINI_API_KEY=old-key\nGOOGLE_GEMINI_BASE_URL=https://old.example.com\n")
    (sb / ".gemini" / "settings.json").write_text(json.dumps({
        "mcpServers": {"foo": {"command": "bar"}},
        "security": {"auth": {"selectedType": "oauth-personal"}},
    }))
    # hermes (comments + unrelated sections must survive writes)
    (sb / ".hermes").mkdir(parents=True)
    (sb / ".hermes" / "config.yaml").write_text(
        "# user comment header\n"
        "model:\n  default: old-model\n  provider: hermes-old\n"
        "mcp_servers:\n  weather:\n    command: echo\n"
        "custom_providers:\n"
        "  - name: hermes-old\n"
        "    base_url: https://old.example.com/v1\n"
        "    api_key: old-k\n"
        "    api_mode: chat_completions\n"
        "    model: old-model\n"
        "    models:\n"
        "      old-model:\n        context_length: 128000\n")
    # pi (settings.json belongs to Pi — must stay untouched)
    (sb / ".pi" / "agent").mkdir(parents=True)
    (sb / ".pi" / "agent" / "models.json").write_text(json.dumps({"providers": {
        "pi-live": {"name": "Pi Live", "baseUrl": "https://pi.example.com/v1",
                    "api": "openai-completions", "apiKey": "k1",
                    "models": [{"id": "m1"}]}}}))
    (sb / ".pi" / "agent" / "settings.json").write_text(json.dumps({"theme": "dark"}))
    # claude-desktop
    appdata = sb / "AppData" / "Local"
    for d in ("Claude", "Claude-3p"):
        (appdata / d).mkdir(parents=True)
        (appdata / d / "claude_desktop_config.json").write_text(
            json.dumps({"deploymentMode": "1p", "other": 1}))
    import sqlite3
    legacy = sb / ".cc-switch"
    legacy.mkdir(parents=True)
    conn = sqlite3.connect(legacy / "cc-switch.db")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA user_version = 10")
    conn.execute(
        "CREATE TABLE providers (id TEXT NOT NULL, app_type TEXT NOT NULL, name TEXT NOT NULL,"
        " settings_config TEXT NOT NULL, website_url TEXT, category TEXT, created_at INTEGER,"
        " sort_index INTEGER, notes TEXT, icon TEXT, icon_color TEXT,"
        " meta TEXT NOT NULL DEFAULT '{}', is_current BOOLEAN NOT NULL DEFAULT 0,"
        " in_failover_queue BOOLEAN NOT NULL DEFAULT 0, PRIMARY KEY (id, app_type))")
    conn.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute(
        "INSERT INTO providers (id, app_type, name, settings_config, category, is_current)"
        " VALUES ('mig-claude','claude','Migrated Claude',?,'custom',1)",
        (json.dumps({"env": {"ANTHROPIC_BASE_URL": "https://old.example.com",
                             "ANTHROPIC_AUTH_TOKEN": "sk-old"}}),))
    conn.commit()
    conn.close()


# ---------------- per-agent checks ----------------

def check_common():
    st, d = http("GET", "/api/agents")
    assert st == 200, (st, d)
    ids = [a["id"] for a in d]
    expected = ["claude", "claude-desktop", "codex", "gemini", "grokbuild",
                "opencode", "openclaw", "hermes", "pi"]
    assert ids == expected, ids
    assert all(a["configurable"] for a in d), d
    st, d = http("GET", "/api/health")
    assert st == 200 and Path(d["db_path"]) == _sb / ".cc-switch-web" / "cc-switch.db", d
    # migration happened: legacy provider visible
    st, d = http("GET", "/api/providers?app=claude")
    assert st == 200 and any(p["id"] == "mig-claude" for p in d), d
    print("  common OK: agents list, health db_path, legacy migration")


def check_claude():
    st, d = http("POST", "/api/providers?app=claude", {
        "id": "new-claude", "name": "New Claude",
        "settings_config": {"env": {"ANTHROPIC_BASE_URL": "https://new.example.com",
                                    "ANTHROPIC_AUTH_TOKEN": "sk-new",
                                    "ANTHROPIC_MODEL": "model-x"}}})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=claude&id=new-claude")
    assert st == 200, (st, d)
    live = rj(_sb / ".claude" / "settings.json")
    assert live["env"]["ANTHROPIC_BASE_URL"] == "https://new.example.com", live
    assert live["env"]["ANTHROPIC_MODEL"] == "model-x", live
    assert live["permissions"]["allow"] == ["Bash"], live  # non-env preserved
    # backfill: old current provider now carries the OLD live config
    st, d = http("GET", "/api/providers?app=claude")
    mig = next(p for p in d if p["id"] == "mig-claude")
    assert mig["settings_config"]["env"]["ANTHROPIC_BASE_URL"] == "https://old.example.com", mig
    assert mig["settings_config"]["permissions"]["allow"] == ["Bash"], mig
    st, d = http("GET", "/api/current?app=claude")
    assert d["current"]["id"] == "new-claude", d
    print("  claude OK: switch wrote env, preserved non-env, backfilled old provider")


def check_openclaw():
    st, d = http("POST", "/api/import-live?app=openclaw")
    assert st == 201 and d["imported"] >= 1, (st, d)
    st, d = http("POST", "/api/providers?app=openclaw", {
        "id": "oc-new", "name": "OC New",
        "settings_config": {"baseUrl": "https://ocnew.example.com/v1", "apiKey": "kk",
                            "api": "openai-completions",
                            "models": [{"id": "m1"}, {"id": "m2"}]}})
    assert st == 201, (st, d)
    cfg = rj(_sb / ".openclaw" / "openclaw.json")
    assert cfg["models"]["providers"]["oc-new"]["baseUrl"] == "https://ocnew.example.com/v1", cfg
    st, d = http("POST", "/api/switch?app=openclaw&id=oc-new")
    assert st == 200, (st, d)
    cfg = rj(_sb / ".openclaw" / "openclaw.json")
    assert cfg["agents"]["defaults"]["model"]["primary"] == "oc-new/m1", cfg
    assert cfg["agents"]["defaults"]["model"]["fallbacks"] == ["oc-new/m2"], cfg
    st, d = http("POST", "/api/switch?app=openclaw&id=live-oc")
    assert st == 200, (st, d)
    st, d = http("DELETE", "/api/providers/oc-new?app=openclaw")
    assert st == 200, (st, d)
    cfg = rj(_sb / ".openclaw" / "openclaw.json")
    assert "oc-new" not in cfg["models"]["providers"], cfg
    assert "live-oc" in cfg["models"]["providers"], cfg
    print("  openclaw OK: import, sync-to-live, switch defaults, delete removal")


def check_codex():
    codex_new_toml = (
        'model_provider = "custom"\nmodel = "gpt-5.2"\n'
        'model_reasoning_effort = "high"\ndisable_response_storage = true\n\n'
        '[model_providers.custom]\nname = "X"\nbase_url = "https://x.example.com/v1"\n'
        'wire_api = "responses"\nrequires_openai_auth = true\n')
    st, d = http("POST", "/api/providers?app=codex", {
        "id": "cd-old", "name": "Codex Old",
        "settings_config": {"auth": {"OPENAI_API_KEY": "sk-old2"},
                            "config": codex_new_toml.replace("x.example.com", "old2.example.com")}})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=codex&id=cd-old")
    assert st == 200, (st, d)
    st, d = http("POST", "/api/providers?app=codex", {
        "id": "cd-new", "name": "Codex New",
        "settings_config": {"auth": {"OPENAI_API_KEY": "sk-new"}, "config": codex_new_toml}})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=codex&id=cd-new")
    assert st == 200, (st, d)
    auth = rj(_sb / ".codex" / "auth.json")
    assert auth == {"OPENAI_API_KEY": "sk-new"}, auth
    toml = (_sb / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert 'base_url = "https://x.example.com/v1"' in toml, toml
    # backfill: old current provider carries the live config it owned
    st, d = http("GET", "/api/providers?app=codex")
    old = next(p for p in d if p["id"] == "cd-old")
    assert old["settings_config"]["auth"]["OPENAI_API_KEY"] == "sk-old2", old
    assert "old2.example.com" in old["settings_config"]["config"], old
    # bad TOML -> 400 on switch
    st, d = http("POST", "/api/providers?app=codex", {
        "id": "cd-bad", "name": "Bad",
        "settings_config": {"auth": {}, "config": "not [valid toml"}})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=codex&id=cd-bad")
    assert st == 400 and "TOML" in str(d), (st, d)
    # official switch: config.toml emptied, auth.json untouched
    st, d = http("POST", "/api/providers?app=codex", {
        "id": "codex-official", "name": "OpenAI Official",
        "settings_config": {"auth": {}, "config": ""}, "category": "official"})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=codex&id=codex-official")
    assert st == 200, (st, d)
    assert (_sb / ".codex" / "auth.json").read_text(encoding="utf-8").strip() != ""
    assert (_sb / ".codex" / "config.toml").read_text(encoding="utf-8") == ""
    print("  codex OK: dual-file write, backfill, bad TOML 400, official protects auth.json")


def check_gemini():
    st, d = http("POST", "/api/providers?app=gemini", {
        "id": "gm-old", "name": "GM Old",
        "settings_config": {"env": {"GOOGLE_GEMINI_BASE_URL": "https://gmold.example.com",
                                    "GEMINI_API_KEY": "old-key2"}}})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=gemini&id=gm-old")
    assert st == 200, (st, d)
    st, d = http("POST", "/api/providers?app=gemini", {
        "id": "gm-new", "name": "GM New",
        "settings_config": {"env": {"GOOGLE_GEMINI_BASE_URL": "https://new.example.com",
                                    "GEMINI_API_KEY": "k-new", "GEMINI_MODEL": "gemini-3.6-flash"}}})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=gemini&id=gm-new")
    assert st == 200, (st, d)
    env_text = (_sb / ".gemini" / ".env").read_text(encoding="utf-8")
    assert "GEMINI_API_KEY=k-new" in env_text and "GEMINI_MODEL=gemini-3.6-flash" in env_text, env_text
    settings = rj(_sb / ".gemini" / "settings.json")
    assert settings["mcpServers"] == {"foo": {"command": "bar"}}, settings  # preserved
    assert settings["security"]["auth"]["selectedType"] == "gemini-api-key", settings
    # backfill
    st, d = http("GET", "/api/providers?app=gemini")
    old = next(p for p in d if p["id"] == "gm-old")
    assert old["settings_config"]["env"]["GEMINI_API_KEY"] == "old-key2", old
    # missing key -> 400
    st, d = http("POST", "/api/providers?app=gemini", {
        "id": "gm-bad", "name": "Bad",
        "settings_config": {"env": {"GOOGLE_GEMINI_BASE_URL": "https://x.example.com"}}})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=gemini&id=gm-bad")
    assert st == 400 and "GEMINI_API_KEY" in str(d), (st, d)
    # official -> oauth-personal, empty env
    st, d = http("POST", "/api/providers?app=gemini", {
        "id": "gemini-official", "name": "Google Official",
        "settings_config": {"env": {}}, "category": "official"})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=gemini&id=gemini-official")
    assert st == 200, (st, d)
    assert (_sb / ".gemini" / ".env").read_text(encoding="utf-8").strip() == ""
    settings = rj(_sb / ".gemini" / "settings.json")
    assert settings["security"]["auth"]["selectedType"] == "oauth-personal", settings
    assert settings["mcpServers"], settings
    print("  gemini OK: .env write, settings merge+selectedType, backfill, official oauth")


def check_grokbuild():
    good = ('[models]\ndefault = "grok-4.5"\n\n[model."grok-4.5"]\nmodel = "grok-4.5"\n'
            'base_url = "https://gr.example.com/v1"\nname = "GR"\napi_key = "k"\n'
            'api_backend = "responses"\ncontext_window = 500000')
    st, d = http("POST", "/api/providers?app=grokbuild", {
        "id": "gr-new", "name": "Grok New", "settings_config": {"config": good}})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=grokbuild&id=gr-new")
    assert st == 200, (st, d)
    text = (_sb / ".grok" / "config.toml").read_text(encoding="utf-8")
    assert text == good, text
    # missing context_window -> 400 listing the field
    bad = good.replace("context_window = 500000\n", "").replace("\napi_backend", "\napi_backend")
    bad = '[models]\ndefault = "grok-4.5"\n\n[model."grok-4.5"]\nmodel = "grok-4.5"\n' \
          'base_url = "https://gr.example.com/v1"\nname = "GR"\napi_key = "k"\n' \
          'api_backend = "responses"\n'
    st, d = http("POST", "/api/providers?app=grokbuild", {
        "id": "gr-bad", "name": "Bad", "settings_config": {"config": bad}})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=grokbuild&id=gr-bad")
    assert st == 400 and "context_window" in str(d), (st, d)
    # official -> empty file (xAI OAuth fallback)
    st, d = http("POST", "/api/providers?app=grokbuild", {
        "id": "grokbuild-official", "name": "xAI Official",
        "settings_config": {"config": ""}, "category": "official"})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=grokbuild&id=grokbuild-official")
    assert st == 200, (st, d)
    assert (_sb / ".grok" / "config.toml").read_text(encoding="utf-8") == ""
    print("  grokbuild OK: native TOML write, validation 400, official empty write")


def check_opencode():
    st, d = http("POST", "/api/providers?app=opencode", {
        "id": "ocd-new", "name": "OCD New",
        "settings_config": {"npm": "@ai-sdk/openai-compatible", "name": "OCD",
                            "options": {"baseURL": "https://ocd.example.com/v1", "apiKey": "k"},
                            "models": {"m1": {"name": "M1"}}}})
    assert st == 201, (st, d)
    live = rj(_sb / ".config" / "opencode" / "opencode.json")
    assert live["$schema"], live
    assert live["provider"]["ocd-new"]["options"]["baseURL"] == "https://ocd.example.com/v1", live
    st, d = http("POST", "/api/switch?app=opencode&id=ocd-new")
    assert st == 200, (st, d)
    st, d = http("GET", "/api/current?app=opencode")
    assert d["current"]["id"] == "ocd-new", d
    # switch away before deleting (current provider is protected)
    st, d = http("POST", "/api/providers?app=opencode", {
        "id": "ocd-alt", "name": "OCD Alt",
        "settings_config": {"npm": "@ai-sdk/openai-compatible", "name": "Alt",
                            "options": {"baseURL": "https://alt.example.com/v1", "apiKey": "k"},
                            "models": {"a1": {"name": "A1"}}}})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=opencode&id=ocd-alt")
    assert st == 200, (st, d)
    st, d = http("DELETE", "/api/providers/ocd-new?app=opencode")
    assert st == 200, (st, d)
    live = rj(_sb / ".config" / "opencode" / "opencode.json")
    assert "ocd-new" not in live["provider"] and "ocd-alt" in live["provider"], live
    # import is idempotent: live providers already in the DB are skipped
    st, d = http("POST", "/api/import-live?app=opencode")
    assert st == 201 and d["imported"] == 0, (st, d)
    print("  opencode OK: $schema skeleton, upsert/switch, delete removal, empty import 404")


def check_hermes():
    st, d = http("POST", "/api/providers?app=hermes", {
        "id": "hm-new", "name": "Hermes New",
        "settings_config": {"baseUrl": "https://hm.example.com/v1", "apiKey": "k",
                            "api_mode": "chat_completions",
                            "models": [{"id": "m1", "name": "M1", "context_length": 200000}]}})
    assert st == 201, (st, d)
    text = (_sb / ".hermes" / "config.yaml").read_text(encoding="utf-8")
    assert "# user comment header" in text, text  # comments preserved
    assert "weather" in text, text  # mcp_servers preserved
    import yaml
    cfg = yaml.safe_load(text)
    entry = next(e for e in cfg["custom_providers"] if e["name"] == "hm-new")
    assert entry["base_url"] == "https://hm.example.com/v1", entry  # camelCase healed
    assert entry["model"] == "m1" and entry["models"] == {"m1": {"name": "M1", "context_length": 200000}}, entry
    st, d = http("POST", "/api/switch?app=hermes&id=hm-new")
    assert st == 200, (st, d)
    cfg = yaml.safe_load((_sb / ".hermes" / "config.yaml").read_text(encoding="utf-8"))
    assert cfg["model"] == {"default": "m1", "provider": "hm-new"}, cfg["model"]
    assert cfg["mcp_servers"], cfg  # still preserved after second write
    # import: fixture entry lands in DB
    st, d = http("POST", "/api/import-live?app=hermes")
    assert st == 201 and d["imported"] == 1, (st, d)
    st, d = http("GET", "/api/providers?app=hermes")
    imported = next(p for p in d if p["id"] == "hermes-old")
    assert imported["settings_config"]["models"][0]["id"] == "old-model", imported
    # remove keeps other entries + comments
    st, d = http("POST", "/api/switch?app=hermes&id=hermes-old")
    assert st == 200, (st, d)
    st, d = http("DELETE", "/api/providers/hm-new?app=hermes")
    assert st == 200, (st, d)
    text = (_sb / ".hermes" / "config.yaml").read_text(encoding="utf-8")
    assert "hm-new" not in text and "# user comment header" in text and "weather" in text, text
    print("  hermes OK: comment/mcp preservation, camelCase healing, model defaults, import, removal")


def check_pi():
    pi_settings = _sb / ".pi" / "agent" / "settings.json"
    st, d = http("POST", "/api/providers?app=pi", {
        "id": "pi-new", "name": "Pi New",
        "settings_config": {"name": "Pi New", "baseUrl": "https://pinew.example.com/v1",
                            "api": "openai-completions", "apiKey": "kk",
                            "models": [{"id": "m1"}]}})
    assert st == 201, (st, d)
    live = rj(_sb / ".pi" / "agent" / "models.json")
    assert live["providers"]["pi-new"]["baseUrl"] == "https://pinew.example.com/v1", live
    assert "pi-live" in live["providers"], live
    assert rj(pi_settings) == {"theme": "dark"}  # Pi-owned file untouched
    st, d = http("POST", "/api/switch?app=pi&id=pi-new")
    assert st == 200, (st, d)
    st, d = http("POST", "/api/import-live?app=pi")
    assert st == 201 and d["imported"] >= 1, (st, d)
    st, d = http("POST", "/api/switch?app=pi&id=pi-live")
    assert st == 200, (st, d)
    st, d = http("DELETE", "/api/providers/pi-new?app=pi")
    assert st == 200, (st, d)
    live = rj(_sb / ".pi" / "agent" / "models.json")
    assert "pi-new" not in live["providers"] and "pi-live" in live["providers"], live
    assert rj(pi_settings) == {"theme": "dark"}
    print("  pi OK: upsert/switch/import/remove, settings.json never touched")


def check_claude_desktop():
    base = _sb / "AppData" / "Local"
    profile_id = "00000000-0000-4000-8000-000000157210"
    profile = base / "Claude-3p" / "configLibrary" / f"{profile_id}.json"
    meta = base / "Claude-3p" / "configLibrary" / "_meta.json"
    st, d = http("POST", "/api/providers?app=claude-desktop", {
        "id": "cdsk-new", "name": "CD New",
        "settings_config": {"env": {"ANTHROPIC_BASE_URL": "https://cdsk.example.com",
                                    "ANTHROPIC_AUTH_TOKEN": "tok"},
                            "inferenceModels": ["claude-sonnet-5", "claude-opus-5"]}})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=claude-desktop&id=cdsk-new")
    assert st == 200, (st, d)
    for d_name in ("Claude", "Claude-3p"):
        cfg = rj(base / d_name / "claude_desktop_config.json")
        assert cfg["deploymentMode"] == "3p" and cfg["other"] == 1, cfg
    prof = rj(profile)
    assert prof["inferenceGatewayBaseUrl"] == "https://cdsk.example.com", prof
    assert prof["inferenceGatewayAuthScheme"] == "bearer" and prof["inferenceProvider"] == "gateway", prof
    assert prof["inferenceModels"] == ["claude-sonnet-5", "claude-opus-5"], prof
    assert rj(meta)["appliedId"] == profile_id, rj(meta)
    # unsafe model id -> 400
    st, d = http("POST", "/api/providers?app=claude-desktop", {
        "id": "cdsk-bad", "name": "Bad",
        "settings_config": {"env": {"ANTHROPIC_BASE_URL": "https://x.example.com",
                                    "ANTHROPIC_AUTH_TOKEN": "t"},
                            "inferenceModels": ["gpt-4o"]}})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=claude-desktop&id=cdsk-bad")
    assert st == 400 and "gpt-4o" in str(d), (st, d)
    # import from profile
    st, d = http("POST", "/api/import-live?app=claude-desktop")
    assert st == 201, (st, d)
    st, d = http("GET", "/api/providers?app=claude-desktop")
    imp = next(p for p in d if p["id"].startswith("imported-"))
    assert imp["settings_config"]["env"]["ANTHROPIC_BASE_URL"] == "https://cdsk.example.com", imp
    # official restore: 1p everywhere, profile removed
    st, d = http("POST", "/api/providers?app=claude-desktop", {
        "id": "claude-desktop-official", "name": "Anthropic Official",
        "settings_config": {"env": {}}, "category": "official"})
    assert st == 201, (st, d)
    st, d = http("POST", "/api/switch?app=claude-desktop&id=claude-desktop-official")
    assert st == 200, (st, d)
    for d_name in ("Claude", "Claude-3p"):
        cfg = rj(base / d_name / "claude_desktop_config.json")
        assert cfg["deploymentMode"] == "1p" and cfg["other"] == 1, cfg
    assert not profile.exists()
    assert not rj(meta).get("entries"), rj(meta)
    print("  claude-desktop OK: 3p gateway profile, unsafe model 400, import, official restore")


def check_presets():
    """One preset apply per new agent: load, api_key injection, additive sync."""
    cases = [
        ("codex", "kimi", lambda sc: sc["auth"]["OPENAI_API_KEY"] == "kk"),
        ("gemini", "packycode", lambda sc: sc["env"]["GEMINI_API_KEY"] == "kk"),
        ("grokbuild", "packycode", lambda sc: 'api_key = "kk"' in sc["config"]),
        ("opencode", "kimi", lambda sc: sc["options"]["apiKey"] == "kk"),
        ("hermes", "kimi", lambda sc: sc["api_key"] == "kk"),
        ("pi", "kimi", lambda sc: sc["apiKey"] == "kk"),
        ("claude-desktop", "kimi-for-coding",
         lambda sc: sc["env"]["ANTHROPIC_AUTH_TOKEN"] == "kk"),
    ]
    for app, pid, verify in cases:
        st, d = http("GET", f"/api/presets?app={app}")
        assert st == 200 and d, (app, st, d)
        st, d = http("POST", f"/api/presets/apply?app={app}&id={pid}&api_key=kk")
        assert st == 201, (app, pid, st, d)
        st, d = http("GET", f"/api/providers/{pid}?app={app}")
        assert st == 200 and verify(d["settings_config"]), (app, pid, d)
    # additive agents also synced the preset provider into their live file
    live = rj(_sb / ".config" / "opencode" / "opencode.json")
    assert live["provider"]["kimi"]["options"]["apiKey"] == "kk", live
    import yaml
    hermes = yaml.safe_load((_sb / ".hermes" / "config.yaml").read_text(encoding="utf-8"))
    assert any(e.get("name") == "kimi" and e.get("api_key") == "kk"
               for e in hermes["custom_providers"]), hermes
    pi_live = rj(_sb / ".pi" / "agent" / "models.json")
    assert pi_live["providers"]["kimi"]["apiKey"] == "kk", pi_live
    print("  presets OK: 7 agents load presets, api_key injected, additive live sync")


CHECKS = {
    "claude": check_claude,
    "openclaw": check_openclaw,
    "codex": check_codex,
    "gemini": check_gemini,
    "grokbuild": check_grokbuild,
    "opencode": check_opencode,
    "hermes": check_hermes,
    "pi": check_pi,
    "claude-desktop": check_claude_desktop,
    "presets": check_presets,
}


def main():
    targets = sys.argv[1:] or list(CHECKS.keys())
    try:
        start_server(fixture_default)
        check_common()
        for t in targets:
            CHECKS[t]()
        print(f"SMOKE PASSED: common + {', '.join(targets)}")
    finally:
        stop_server()


if __name__ == "__main__":
    main()
