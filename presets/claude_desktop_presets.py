"""Claude Desktop provider presets (converted from cc-switch TypeScript).

Source: cc-switch/src/config/claudeDesktopProviderPresets.ts (74 entries).

Unlike Claude Code presets, the TS source keeps baseUrl at the top level and
expresses models as Desktop-visible route ids mapped to upstream models
(modelRoutes). Only passthrough-compatible providers are included here, i.e.
providers whose upstream model ids are identical to the official Claude model
ids (claude-sonnet-5 / claude-opus-5 / claude-haiku-4-5), so Desktop role
routes work without renaming. Entries that map roles to different upstream
model names (brandedRoutes / mappedRoutes) are intentionally skipped.

inferenceModels lists the passthrough Claude role model ids advertised by the
provider (omitted when the source declares no routes).
"""

CLAUDE_DESKTOP_PRESETS = [
    {
        "id": "claude-desktop-official",
        "name": "Claude Official",
        "category": "official",
        "website_url": "https://claude.ai",
        "icon": "anthropic",
        "icon_color": "#D4915D",
        "settings_config": {"env": {}},
    },
    {
        "id": "kimi-for-coding",
        "name": "Kimi For Coding",
        "category": "cn_official",
        "website_url": "https://www.kimi.com/code/",
        "icon": "kimi",
        "icon_color": "#6366F1",
        "settings_config": {
            "env": {
                "ANTHROPIC_BASE_URL": "https://api.kimi.com/coding/",
                "ANTHROPIC_AUTH_TOKEN": "",
            },
            "inferenceModels": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5"],
        },
    },
    {
        "id": "bailian",
        "name": "Bailian",
        "category": "cn_official",
        "website_url": "https://bailian.console.aliyun.com",
        "icon": "bailian",
        "icon_color": "#624AFF",
        "settings_config": {
            "env": {
                "ANTHROPIC_BASE_URL": "https://dashscope.aliyuncs.com/apps/anthropic",
                "ANTHROPIC_AUTH_TOKEN": "",
            },
            "inferenceModels": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5"],
        },
    },
    {
        "id": "bailian-for-coding",
        "name": "Bailian For Coding",
        "category": "cn_official",
        "website_url": "https://bailian.console.aliyun.com",
        "icon": "bailian",
        "icon_color": "#624AFF",
        "settings_config": {
            "env": {
                "ANTHROPIC_BASE_URL": "https://coding.dashscope.aliyuncs.com/apps/anthropic",
                "ANTHROPIC_AUTH_TOKEN": "",
            },
            "inferenceModels": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5"],
        },
    },
    {
        "id": "packycode",
        "name": "PackyCode",
        "category": "third_party",
        "website_url": "https://www.packyapi.ai",
        "icon": "packycode",
        "icon_color": None,
        "settings_config": {
            "env": {
                "ANTHROPIC_BASE_URL": "https://www.packyapi.ai",
                "ANTHROPIC_AUTH_TOKEN": "",
            },
            "inferenceModels": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5"],
        },
    },
    {
        "id": "zetaapi",
        "name": "ZetaAPI",
        "category": "aggregator",
        "website_url": "https://zetaapi.ai",
        "icon": "zetaapi",
        "icon_color": None,
        "settings_config": {
            "env": {
                "ANTHROPIC_BASE_URL": "https://api.zetaapi.ai",
                "ANTHROPIC_AUTH_TOKEN": "",
            },
            "inferenceModels": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5"],
        },
    },
    {
        "id": "apinebula",
        "name": "APINebula",
        "category": "third_party",
        "website_url": "https://apinebula.ai",
        "icon": "apinebula",
        "icon_color": None,
        "settings_config": {
            "env": {
                "ANTHROPIC_BASE_URL": "https://apinebula.ai",
                "ANTHROPIC_AUTH_TOKEN": "",
            },
            "inferenceModels": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5"],
        },
    },
    {
        "id": "aicodemirror",
        "name": "AICodeMirror",
        "category": "third_party",
        "website_url": "https://www.aicodemirror.ai",
        "icon": "aicodemirror",
        "icon_color": "#000000",
        "settings_config": {
            "env": {
                "ANTHROPIC_BASE_URL": "https://api.aicodemirror.ai/api/claudecode",
                "ANTHROPIC_AUTH_TOKEN": "",
            },
            "inferenceModels": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5"],
        },
    },
    {
        "id": "runapi",
        "name": "RunAPI",
        "category": "aggregator",
        "website_url": "https://runapi.host",
        "icon": "runapi",
        "icon_color": None,
        "settings_config": {
            "env": {
                "ANTHROPIC_BASE_URL": "https://runapi.host",
                "ANTHROPIC_AUTH_TOKEN": "",
            },
            "inferenceModels": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5"],
        },
    },
    {
        "id": "qiniu",
        "name": "Qiniu",
        "category": "aggregator",
        "website_url": "https://www.qiniu.com",
        "icon": "qiniu",
        "icon_color": None,
        "settings_config": {
            "env": {
                "ANTHROPIC_BASE_URL": "https://api.qnaigc.com",
                "ANTHROPIC_AUTH_TOKEN": "",
            },
            "inferenceModels": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5"],
        },
    },
    {
        "id": "aihubmix",
        "name": "AiHubMix",
        "category": "aggregator",
        "website_url": "https://aihubmix.com",
        "icon": "aihubmix",
        "icon_color": "#006FFB",
        "settings_config": {
            # Source declares apiKeyField: "ANTHROPIC_API_KEY".
            "env": {
                "ANTHROPIC_BASE_URL": "https://aihubmix.com",
                "ANTHROPIC_API_KEY": "",
            },
            "inferenceModels": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5"],
        },
    },
    {
        "id": "atlascloud",
        "name": "AtlasCloud",
        "category": "aggregator",
        "website_url": "https://www.atlascloud.ai/console/coding-plan",
        "icon": "atlascloud",
        "icon_color": None,
        "settings_config": {
            "env": {
                "ANTHROPIC_BASE_URL": "https://api.atlascloud.ai",
                "ANTHROPIC_AUTH_TOKEN": "",
            },
            "inferenceModels": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5"],
        },
    },
    {
        "id": "ccsub",
        "name": "CCSub",
        "category": "aggregator",
        "website_url": "https://www.ccsub.net",
        "icon": "ccsub",
        "icon_color": None,
        "settings_config": {
            "env": {
                "ANTHROPIC_BASE_URL": "https://www.ccsub.net",
                "ANTHROPIC_AUTH_TOKEN": "",
            },
            "inferenceModels": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5"],
        },
    },
    {
        "id": "custom",
        "name": "Custom Provider",
        "category": "custom",
        "website_url": None,
        "icon": None,
        "icon_color": None,
        "settings_config": {"env": {
            "ANTHROPIC_BASE_URL": "https://api.example.com",
            "ANTHROPIC_AUTH_TOKEN": "",
        }},
    },
]
