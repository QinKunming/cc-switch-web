"""Codex provider presets (converted from cc-switch TypeScript)."""

CODEX_PRESETS = [
    {
        "id": "codex-official",
        "name": "OpenAI Official",
        "category": "official",
        "website_url": "https://chatgpt.com/codex",
        "icon": "openai",
        "icon_color": "#00A67E",
        "settings_config": {"auth": {}, "config": ""},
    },
    {
        "id": "kimi",
        "name": "Kimi",
        "category": "cn_official",
        "website_url": "https://platform.kimi.com",
        "icon": "kimi",
        "icon_color": "#6366F1",
        "settings_config": {
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "kimi-k2.7-code"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "Kimi"
base_url = "https://api.moonshot.cn/v1"
wire_api = "responses"
requires_openai_auth = true
''',
        },
    },
    {
        "id": "kimi-for-coding",
        "name": "Kimi For Coding",
        "category": "cn_official",
        "website_url": "https://www.kimi.com/code",
        "icon": "kimi",
        "icon_color": "#6366F1",
        "settings_config": {
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "kimi-for-coding"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "Kimi For Coding"
base_url = "https://api.kimi.com/coding/v1"
wire_api = "responses"
requires_openai_auth = true
''',
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
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "deepseek-v4-flash"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "DeepSeek"
base_url = "https://api.deepseek.com/v1"
wire_api = "responses"
requires_openai_auth = true
''',
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
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "glm-5.2"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "Zhipu GLM"
base_url = "https://open.bigmodel.cn/api/coding/paas/v4"
wire_api = "responses"
requires_openai_auth = true
''',
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
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "qwen3-coder-plus"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "Bailian"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
wire_api = "responses"
requires_openai_auth = true
''',
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
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "MiniMax-M3"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "MiniMax"
base_url = "https://api.minimaxi.com/v1"
wire_api = "responses"
requires_openai_auth = true
''',
        },
    },
    {
        "id": "volcengine-agent-plan",
        "name": "火山 Agent Plan",
        "category": "cn_official",
        "website_url": "https://www.volcengine.com/activity/agentplan",
        "icon": "huoshan",
        "icon_color": "#3370FF",
        "settings_config": {
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "ark-code-latest"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "火山 Agent Plan"
base_url = "https://ark.cn-beijing.volces.com/api/plan/v3"
wire_api = "responses"
requires_openai_auth = true
''',
        },
    },
    {
        "id": "volcengine-coding-plan",
        "name": "火山 Coding Plan",
        "category": "cn_official",
        "website_url": "https://www.volcengine.com/activity/codingplan",
        "icon": "huoshan",
        "icon_color": "#3370FF",
        "settings_config": {
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "ark-code-latest"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "火山 Coding Plan"
base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
wire_api = "responses"
requires_openai_auth = true
''',
        },
    },
    {
        "id": "doubao-seed",
        "name": "DouBaoSeed",
        "category": "cn_official",
        "website_url": "https://console.volcengine.com/ark",
        "icon": "doubao",
        "icon_color": "#3370FF",
        "settings_config": {
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "doubao-seed-2-1-pro-260628"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "DouBaoSeed"
base_url = "https://ark.cn-beijing.volces.com/api/v3"
wire_api = "responses"
requires_openai_auth = true
''',
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
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "step-3.7-flash"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "StepFun"
base_url = "https://api.stepfun.com/step_plan/v1"
wire_api = "responses"
requires_openai_auth = true
''',
        },
    },
    {
        "id": "tencent-hunyuan",
        "name": "Tencent Hunyuan",
        "category": "cn_official",
        "website_url": "https://cloud.tencent.com/product/tokenhub",
        "icon": "hunyuan",
        "icon_color": "#0055E9",
        "settings_config": {
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "hy3"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "Tencent Hunyuan"
base_url = "https://tokenhub.tencentmaas.com/v1"
wire_api = "responses"
requires_openai_auth = true
''',
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
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "ZhipuAI/GLM-5.2"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "ModelScope"
base_url = "https://api-inference.modelscope.cn/v1"
wire_api = "responses"
requires_openai_auth = true
''',
        },
    },
    {
        "id": "siliconflow",
        "name": "SiliconFlow",
        "category": "aggregator",
        "website_url": "https://siliconflow.cn",
        "icon": "siliconflow",
        "icon_color": "#6E29F6",
        "settings_config": {
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "Pro/MiniMaxAI/MiniMax-M2.5"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "SiliconFlow"
base_url = "https://api.siliconflow.cn/v1"
wire_api = "responses"
requires_openai_auth = true
''',
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
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "gpt-5.6-sol"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "OpenRouter"
base_url = "https://openrouter.ai/api/v1"
wire_api = "responses"
requires_openai_auth = true
''',
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
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "gpt-5.6-sol"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "AiHubMix"
base_url = "https://aihubmix.com/v1"
wire_api = "responses"
requires_openai_auth = true
''',
        },
    },
    {
        "id": "nvidia",
        "name": "Nvidia",
        "category": "aggregator",
        "website_url": "https://build.nvidia.com",
        "icon": "nvidia",
        "icon_color": "#000000",
        "settings_config": {
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "moonshotai/kimi-k2.5"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "Nvidia"
base_url = "https://integrate.api.nvidia.com/v1"
wire_api = "responses"
requires_openai_auth = true
''',
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
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "gpt-5.6-sol"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "PackyCode"
base_url = "https://www.packyapi.ai/v1"
wire_api = "responses"
requires_openai_auth = true
''',
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
            "auth": {"OPENAI_API_KEY": ""},
            "config": '''model_provider = "custom"
model = "your-model"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "Custom Provider"
base_url = "https://api.example.com/v1"
wire_api = "responses"
requires_openai_auth = true
''',
        },
    },
]
