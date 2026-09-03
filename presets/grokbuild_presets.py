"""Grok Build (Grok CLI) provider presets (converted from cc-switch TypeScript).

Source: cc-switch/src/config/grokBuildProviderPresets.ts. The TypeScript config
field uses a Codex-style TOML carrier; base_url / model / name are extracted
from it and rebuilt as native Grok CLI config.toml ([models].default plus a
[model."<profile>"] table). Default model is grok-4.5; OpenRouter-style ids
("x-ai/grok-4.5") keep the full id as the upstream model while the profile
takes the last path segment. Per the TS source, no cn_official / open-source
hosting presets are included (no Grok models upstream).
"""

GROKBUILD_PRESETS = [
    # Official entry: empty config = no custom model table, Grok CLI falls
    # back to its built-in xAI subscription (OAuth) login.
    {
        "id": "grokbuild-official",
        "name": "xAI Official",
        "category": "official",
        "website_url": "https://x.ai",
        "icon": "grok",
        "icon_color": None,
        "settings_config": {"config": ""},
    },
    {
        "id": "packycode",
        "name": "PackyCode",
        "category": "third_party",
        "website_url": "https://www.packyapi.ai",
        "icon": "packycode",
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://www.packyapi.ai/v1"\n'
            'name = "PackyCode"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "zetaapi",
        "name": "ZetaAPI",
        "category": "aggregator",
        "website_url": "https://zetaapi.ai",
        "icon": "zetaapi",
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://api.zetaapi.ai/v1"\n'
            'name = "ZetaAPI"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "apinebula",
        "name": "APINebula",
        "category": "third_party",
        "website_url": "https://apinebula.ai",
        "icon": "apinebula",
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://apinebula.ai/v1"\n'
            'name = "APINebula"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "aicodemirror",
        "name": "AICodeMirror",
        "category": "third_party",
        "website_url": "https://www.aicodemirror.ai",
        "icon": "aicodemirror",
        "icon_color": "#000000",
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://api.aicodemirror.ai/api/codex/backend-api/codex"\n'
            'name = "AICodeMirror"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "runapi",
        "name": "RunAPI",
        "category": "aggregator",
        "website_url": "https://runapi.host",
        "icon": "runapi",
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://runapi.host/v1"\n'
            'name = "RunAPI"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "shengsuanyun",
        "name": "Shengsuanyun",
        "category": "aggregator",
        "website_url": "https://www.shengsuanyun.com",
        "icon": "shengsuanyun",
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "x-ai/grok-4.5"\n'
            'base_url = "https://router.shengsuanyun.com/api/v1"\n'
            'name = "Shengsuanyun"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "qiniu",
        "name": "Qiniu",
        "category": "aggregator",
        "website_url": "https://s.qiniu.com/nMvAvy",
        "icon": "qiniu",
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://api.qnaigc.com/bypass/openai/v1"\n'
            'name = "Qiniu"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "subrouter",
        "name": "SubRouter",
        "category": "aggregator",
        "website_url": "https://subrouter.ai",
        "icon": "subrouter",
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://subrouter.ai/v1"\n'
            'name = "SubRouter"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "code0",
        "name": "Code0",
        "category": "aggregator",
        "website_url": "https://code0.ai",
        "icon": "code0",
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://code0.ai/v1"\n'
            'name = "Code0"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "dmxapi",
        "name": "DMXAPI",
        "category": "aggregator",
        "website_url": "https://www.dmxapi.cn",
        "icon": None,
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://www.dmxapi.cn/v1"\n'
            'name = "DMXAPI"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "xai-grok",
        "name": "xAI (Grok)",
        "category": "third_party",
        "website_url": "https://x.ai/api",
        "icon": "xai",
        "icon_color": "#000000",
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://api.x.ai/v1"\n'
            'name = "xAI (Grok)"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "amux",
        "name": "Amux",
        "category": "aggregator",
        "website_url": "https://amux.ai",
        "icon": "amux",
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://api.amux.ai/v1"\n'
            'name = "Amux"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "aihubmix",
        "name": "AiHubMix",
        "category": "aggregator",
        "website_url": "https://aihubmix.com",
        "icon": "aihubmix",
        "icon_color": "#006FFB",
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://aihubmix.com/v1"\n'
            'name = "AiHubMix"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "cherryin",
        "name": "CherryIN",
        "category": "aggregator",
        "website_url": "https://open.cherryin.ai",
        "icon": "cherryin",
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "x-ai/grok-4.5"\n'
            'base_url = "https://open.cherryin.net/v1"\n'
            'name = "CherryIN"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "category": "aggregator",
        "website_url": "https://openrouter.ai",
        "icon": "openrouter",
        "icon_color": "#6566F1",
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "x-ai/grok-4.5"\n'
            'base_url = "https://openrouter.ai/api/v1"\n'
            'name = "OpenRouter"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "therouter",
        "name": "TheRouter",
        "category": "aggregator",
        "website_url": "https://therouter.ai",
        "icon": None,
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "x-ai/grok-4.5"\n'
            'base_url = "https://api.therouter.ai/v1"\n'
            'name = "TheRouter"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
    {
        "id": "custom",
        "name": "Custom Provider",
        "category": "custom",
        "website_url": "https://api.example.com/v1",
        "icon": None,
        "icon_color": None,
        "settings_config": {"config": (
            '[models]\n'
            'default = "grok-4.5"\n'
            '\n'
            '[model."grok-4.5"]\n'
            'model = "grok-4.5"\n'
            'base_url = "https://api.example.com/v1"\n'
            'name = "Custom Provider"\n'
            'api_key = ""\n'
            'api_backend = "responses"\n'
            'context_window = 500000'
        )},
    },
]
