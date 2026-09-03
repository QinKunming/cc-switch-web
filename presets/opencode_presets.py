"""OpenCode provider presets (converted from cc-switch TypeScript).

Source of truth: cc-switch/src/config/opencodeProviderPresets.ts.
Model limits are enriched from OPENCODE_PRESET_MODEL_VARIANTS when the
model id matches exactly under the same npm package; missing limits
default to {"context": 0, "output": 0}. At most 4 representative models
are kept per provider. All apiKey values are empty strings.
"""

OPENCODE_PRESETS = [
    {
        "id": "kimi",
        "name": "Kimi",
        "category": "cn_official",
        "website_url": "https://platform.kimi.com?aff=cc-switch",
        "icon": "kimi",
        "icon_color": "#6366F1",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "Kimi",
            "options": {
                "baseURL": "https://api.moonshot.cn/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "kimi-k2.7-code": {
                    "name": "Kimi K2.7 Code",
                    "limit": {"context": 0, "output": 0},
                },
                "kimi-k3": {
                    "name": "Kimi K3",
                    "limit": {"context": 1048576, "output": 131072},
                },
            },
        },
    },
    {
        "id": "kimi-for-coding",
        "name": "Kimi For Coding",
        "category": "cn_official",
        "website_url": "https://www.kimi.com/code/?aff=cc-switch",
        "icon": "kimi",
        "icon_color": "#6366F1",
        "settings_config": {
            "npm": "@ai-sdk/anthropic",
            "name": "Kimi For Coding",
            "options": {
                "baseURL": "https://api.kimi.com/coding/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "kimi-for-coding": {
                    "name": "Kimi For Coding",
                    "limit": {"context": 0, "output": 0},
                },
            },
        },
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "category": "cn_official",
        "website_url": "https://platform.deepseek.com",
        "icon": "deepseek",
        "icon_color": "#1E88E5",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "DeepSeek",
            "options": {
                "baseURL": "https://api.deepseek.com/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "deepseek-v4-pro": {
                    "name": "DeepSeek V4 Pro",
                    "limit": {"context": 0, "output": 0},
                },
                "deepseek-v4-flash": {
                    "name": "DeepSeek V4 Flash",
                    "limit": {"context": 0, "output": 0},
                },
            },
        },
    },
    {
        "id": "zhipu-glm",
        "name": "Zhipu GLM",
        "category": "cn_official",
        "website_url": "https://open.bigmodel.cn",
        "icon": "zhipu",
        "icon_color": "#0F62FE",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "Zhipu GLM",
            "options": {
                "baseURL": "https://open.bigmodel.cn/api/coding/paas/v4",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "glm-5.1": {
                    "name": "GLM-5.1",
                    "limit": {"context": 204800, "output": 131072},
                },
            },
        },
    },
    {
        "id": "zhipu-glm-en",
        "name": "Zhipu GLM en",
        "category": "cn_official",
        "website_url": "https://z.ai",
        "icon": "zhipu",
        "icon_color": "#0F62FE",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "Zhipu GLM en",
            "options": {
                "baseURL": "https://api.z.ai/api/coding/paas/v4",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "glm-5.1": {
                    "name": "GLM-5.1",
                    "limit": {"context": 204800, "output": 131072},
                },
            },
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
            "npm": "@ai-sdk/openai-compatible",
            "name": "Bailian",
            "options": {
                "baseURL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {},
        },
    },
    {
        "id": "minimax",
        "name": "MiniMax",
        "category": "cn_official",
        "website_url": "https://platform.minimaxi.com",
        "icon": "minimax",
        "icon_color": "#FF6B6B",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "MiniMax",
            "options": {
                "baseURL": "https://api.minimaxi.com/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "MiniMax-M2.7": {
                    "name": "MiniMax M2.7",
                    "limit": {"context": 204800, "output": 131072},
                },
            },
        },
    },
    {
        "id": "minimax-en",
        "name": "MiniMax en",
        "category": "cn_official",
        "website_url": "https://platform.minimax.io",
        "icon": "minimax",
        "icon_color": "#FF6B6B",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "MiniMax en",
            "options": {
                "baseURL": "https://api.minimax.io/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "MiniMax-M2.7": {
                    "name": "MiniMax M2.7",
                    "limit": {"context": 204800, "output": 131072},
                },
            },
        },
    },
    {
        "id": "doubao-seed",
        "name": "DouBaoSeed",
        "category": "cn_official",
        "website_url": (
            "https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey"
            "?apikey=%7B%7D&utm_campaign=hw&utm_content=ccswitch&utm_medium="
            "devrel_tool_web&utm_source=OWO&utm_term=ccswitch"
        ),
        "icon": "doubao",
        "icon_color": "#3370FF",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "DouBaoSeed",
            "options": {
                "baseURL": "https://ark.cn-beijing.volces.com/api/v3",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "doubao-seed-2-1-pro-260628": {
                    "name": "Doubao Seed 2.1 Pro",
                    "limit": {"context": 0, "output": 0},
                },
            },
        },
    },
    {
        "id": "volcengine-coding-plan",
        "name": "火山 Coding Plan",
        "category": "cn_official",
        "website_url": (
            "https://www.volcengine.com/activity/codingplan?ac=MMAP8JTTCAQ2&rc="
            "6J6FV5N2&utm_campaign=hw&utm_content=ccswitch&utm_medium="
            "devrel_tool_web&utm_source=OWO&utm_term=ccswitch"
        ),
        "icon": "huoshan",
        "icon_color": "#3370FF",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "火山 Coding Plan",
            "options": {
                "baseURL": "https://ark.cn-beijing.volces.com/api/coding/v3",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "ark-code-latest": {
                    "name": "Ark Code Latest",
                    "limit": {"context": 0, "output": 0},
                },
            },
        },
    },
    {
        "id": "stepfun",
        "name": "StepFun",
        "category": "cn_official",
        "website_url": "https://platform.stepfun.com/step-plan",
        "icon": "stepfun",
        "icon_color": "#16D6D2",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "StepFun",
            "options": {
                "baseURL": "https://api.stepfun.com/step_plan/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "step-3.5-flash-2603": {
                    "name": "Step 3.5 Flash 2603",
                    "limit": {"context": 262144, "output": 0},
                },
                "step-3.5-flash": {
                    "name": "Step 3.5 Flash",
                    "limit": {"context": 262144, "output": 0},
                },
            },
        },
    },
    {
        "id": "baidu-qianfan-token-plan",
        "name": "Baidu Qianfan Token Plan",
        "category": "cn_official",
        "website_url": "https://cloud.baidu.com/product/codingplan.html",
        "icon": "baidu",
        "icon_color": "#2932E1",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "Baidu Qianfan Token Plan",
            "options": {
                "baseURL": "https://qianfan.baidubce.com/v2/tokenplan/personal",
                "apiKey": "",
            },
            "models": {
                "deepseek-v4-pro": {
                    "name": "DeepSeek V4 Pro",
                    "limit": {"context": 0, "output": 0},
                },
                "deepseek-v4-flash": {
                    "name": "DeepSeek V4 Flash",
                    "limit": {"context": 0, "output": 0},
                },
                "glm-5.2": {
                    "name": "GLM-5.2",
                    "limit": {"context": 0, "output": 0},
                },
                "kimi-k2.6": {
                    "name": "Kimi K2.6",
                    "limit": {"context": 262144, "output": 262144},
                },
            },
        },
    },
    {
        "id": "longcat",
        "name": "Longcat",
        "category": "cn_official",
        "website_url": "https://longcat.chat/platform",
        "icon": "longcat",
        "icon_color": "#29E154",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "Longcat",
            "options": {
                "baseURL": "https://api.longcat.chat/openai/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "LongCat-2.0": {
                    "name": "LongCat 2.0",
                    "options": {"thinking": {"type": "disabled"}},
                    "limit": {"context": 0, "output": 0},
                },
            },
        },
    },
    {
        "id": "xiaomi-mimo",
        "name": "Xiaomi MiMo",
        "category": "cn_official",
        "website_url": "https://platform.xiaomimimo.com",
        "icon": "xiaomimimo",
        "icon_color": "#000000",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "Xiaomi MiMo",
            "options": {
                "baseURL": "https://api.xiaomimimo.com/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "mimo-v2.5-pro": {
                    "name": "MiMo V2.5 Pro",
                    "limit": {"context": 1048576, "output": 131072},
                    "modalities": {"input": ["text"], "output": ["text"]},
                },
                "mimo-v2.5": {
                    "name": "MiMo V2.5",
                    "limit": {"context": 1048576, "output": 131072},
                    "modalities": {
                        "input": ["text", "image"],
                        "output": ["text"],
                    },
                },
            },
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
            "npm": "@ai-sdk/anthropic",
            "name": "PackyCode",
            "options": {
                "baseURL": "https://www.packyapi.ai/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "claude-sonnet-5": {
                    "name": "Claude Sonnet 5",
                    "limit": {"context": 0, "output": 0},
                },
                "claude-opus-5": {
                    "name": "Claude Opus 5",
                    "limit": {"context": 1000000, "output": 128000},
                },
            },
        },
    },
    {
        "id": "opencode-go",
        "name": "OpenCode Go",
        "category": "third_party",
        "website_url": "https://opencode.ai/go",
        "icon": "opencode",
        "icon_color": "#211E1E",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "OpenCode Go",
            "options": {
                "baseURL": "https://opencode.ai/zen/go/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "glm-5.2": {
                    "name": "GLM 5.2",
                    "limit": {"context": 0, "output": 0},
                },
                "kimi-k2.7-code": {
                    "name": "Kimi K2.7 Code",
                    "limit": {"context": 0, "output": 0},
                },
                "deepseek-v4-pro": {
                    "name": "DeepSeek V4 Pro",
                    "limit": {"context": 0, "output": 0},
                },
                "deepseek-v4-flash": {
                    "name": "DeepSeek V4 Flash",
                    "limit": {"context": 0, "output": 0},
                },
            },
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
            "npm": "@ai-sdk/anthropic",
            "name": "AiHubMix",
            "options": {
                "baseURL": "https://aihubmix.com/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "claude-sonnet-5": {
                    "name": "Claude Sonnet 5",
                    "limit": {"context": 0, "output": 0},
                },
                "claude-opus-5": {
                    "name": "Claude Opus 5",
                    "limit": {"context": 1000000, "output": 128000},
                },
            },
        },
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "category": "aggregator",
        "website_url": "https://openrouter.ai",
        "icon": "openrouter",
        "icon_color": "#6566F1",
        "settings_config": {
            "npm": "@ai-sdk/anthropic",
            "name": "OpenRouter",
            "options": {
                "baseURL": "https://openrouter.ai/api/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "anthropic/claude-sonnet-5": {
                    "name": "Claude Sonnet 5",
                    "limit": {"context": 0, "output": 0},
                },
                "anthropic/claude-opus-5": {
                    "name": "Claude Opus 5",
                    "limit": {"context": 0, "output": 0},
                },
            },
        },
    },
    {
        "id": "modelscope",
        "name": "ModelScope",
        "category": "aggregator",
        "website_url": "https://modelscope.cn",
        "icon": "modelscope",
        "icon_color": "#624AFF",
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "ModelScope",
            "options": {
                "baseURL": "https://api-inference.modelscope.cn/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "ZhipuAI/GLM-5.2": {
                    "name": "GLM-5.2",
                    "limit": {"context": 0, "output": 0},
                },
            },
        },
    },
    {
        "id": "therouter",
        "name": "TheRouter",
        "category": "aggregator",
        "website_url": "https://therouter.ai",
        "icon": None,
        "icon_color": None,
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "TheRouter",
            "options": {
                "baseURL": "https://api.therouter.ai/v1",
                "apiKey": "",
                "setCacheKey": True,
            },
            "models": {
                "anthropic/claude-sonnet-5": {
                    "name": "Claude Sonnet 5",
                    "limit": {"context": 0, "output": 0},
                },
                "openai/gpt-5.3-codex": {
                    "name": "GPT-5.3 Codex",
                    "limit": {"context": 0, "output": 0},
                },
                "openai/gpt-5.2": {
                    "name": "GPT-5.2",
                    "limit": {"context": 0, "output": 0},
                },
                "qwen/qwen3-coder-480b": {
                    "name": "Qwen3 Coder 480B",
                    "limit": {"context": 0, "output": 0},
                },
            },
        },
    },
    {
        "id": "custom",
        "name": "Custom Provider",
        "category": "custom",
        "website_url": None,
        "icon": None,
        "icon_color": None,
        "settings_config": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "Custom Provider",
            "options": {
                "baseURL": "https://api.example.com/v1",
                "apiKey": "",
            },
            "models": {
                "your-model": {
                    "name": "Your Model",
                    "limit": {"context": 0, "output": 0},
                },
            },
        },
    },
]
