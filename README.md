# cc-switch-web

> **当前版本：v2.0.0**（2026-08-21）— 存储独立 + 9 智能体全量支持 + 明暗主题。详见文末[版本历史](#版本历史)。

## 痛点：

现有的cc-switch只能用于图形界面，cc-switch-cli只能用于命令行模式。

有时候为了保障服务器性能，大部分的服务器基本上都没有安装图形界面；

对于不喜欢命令行模式的朋友来说，

配置 AI 编码智能体的模型供应商就比较麻烦，不同模型之间切换更麻烦。

这个Web 端 AI Agent 模型切换管理工具，借鉴 [cc-switch](https://github.com/farion1231/cc-switch) 的核心思路，

同时支持无图形界面的服务器和有图形界面的桌面环境。

当前支持全部 9 个智能体的模型/供应商配置：**Claude Code、Claude Desktop、Codex、Gemini CLI、
Grok Build、OpenCode、OpenClaw、Hermes、Pi**。

## 功能

- **Web 管理**：浏览器操作，无需 GUI
- **9 个智能体**：供应商增删改查、预设应用、一键切换、从 live 配置导入
- **预设导入**：claude 19 / openclaw 14 / codex 19 / gemini 23 / grokbuild 18 / opencode 21 / hermes 18 / pi 17 / claude-desktop 14
- **明暗主题**：顶栏 ☀️/🌙 按钮切换浅色/深色，选择持久化（localStorage），默认深色
- **热切换**：OpenClaw/OpenCode/Pi 等切换后无需重启；Claude Code 这点不稳定，保险起见手动重启一下
- **回填保护**：exclusive 型智能体切换前自动把当前 live 配置回填到旧 provider 记录，手动改动不丢失
- **登录认证**：用户名 + 密码 + 验证码，防止公网服务器未授权访问泄露 api
- **独立存储**：数据在 `~/.cc-switch-web/`

## 快速开始

### 前置要求

- Python 3.11+（依赖 stdlib `tomllib`）

### 安装

```bash
cd cc-switch-web
pip install -r requirements.txt
```

> **Ubuntu 23.04+ / Debian 12+ 注意**：系统 pip 受 PEP 668 保护，直接安装会报
> `externally-managed-environment`。改用 venv（Linux 上也可以直接用 `./start.sh start`，
> 脚本会自动建 venv 并装依赖）：
>
> ```bash
> python3 -m venv .venv
> .venv/bin/pip install -r requirements.txt
> ```
>
> PyPI 直连超时/断流的机器，换国内镜像安装（`start.sh` 同理，见下方方式二）：
>
> ```bash
> .venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

### 启动

```bash
python server.py
```

首次启动会自动生成默认密码并打印到控制台：

```
  CC Switch Web
  Default login: admin / xxxxxxxx
  Change password in ~/.cc-switch-web/web-auth.json
  Database: ~/.cc-switch-web/cc-switch.db
  Local:   http://127.0.0.1:8787
  Network: http://192.168.x.x:8787
```

打开浏览器访问 `http://<ip>:8787`，使用打印的账号密码登录。

**首次启动导入**：如果存在旧目录 `~/.cc-switch/`（与桌面版共用时期的数据），
会自动把 `cc-switch.db` 和 `web-auth.json` **复制**到 `~/.cc-switch-web/`（原件不动，
桌面版不受影响）。此后两边数据完全独立、互不影响。

### 自定义参数

```bash
python server.py --host=0.0.0.0 --port=9000
```

## 部署

### Windows 10

**方式一：直接运行**

```cmd
cd cc-switch-web
pip install -r requirements.txt
python server.py
```

方式二：一键运行

run.bat

**方式三：开机自启（Task Scheduler）**

1. 打开 Task Scheduler → Create Basic Task
2. 触发器：计算机启动时
3. 操作：启动程序
   - 程序：`python.exe` 完整路径（如 `C:\Python312\python.exe`）
   - 参数：`server.py`
   - 起始目录：`cc-switch-web` 完整路径
4. 勾选"不管用户是否登录都要运行"

### Ubuntu（无图形界面）

**方式一：直接运行**

```bash
cd cc-switch-web
pip3 install -r requirements.txt
python3 server.py
```

**方式二：后台管理脚本 run.sh（简单方式）**

```bash
# 注：若 ./run.sh 提示"权限不够"，说明解压工具没有保留 zip 内的可执行位
#     （python3 -m zipfile -e、部分图形归档器会这样；unzip 则会保留），先补一句：
chmod +x run.sh watchdog.sh
./run.sh start     # 首次自动建 venv + 装依赖，然后后台启动
./run.sh status    # 查看状态
./run.sh log 100   # 查看最近 100 行日志（首次启动的默认密码也在日志里）
CCSW_PORT=9000 ./run.sh restart   # 换端口重启
```

**方式三：systemd 服务（推荐，自带崩溃自动重启守护）**

1. 先准备 venv（systemd 不走 start.sh，需要先装好依赖）：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

2. 创建服务文件（把 `<你的用户名>` 和路径换成实际值）：

```bash
sudo tee /etc/systemd/system/cc-switch-web.service << 'EOF'
[Unit]
Description=CC Switch Web
After=network.target
# 关闭重启频率限制：无论崩溃多少次都立即重启
StartLimitIntervalSec=0

[Service]
Type=simple
User=<你的用户名>
WorkingDirectory=/path/to/cc-switch-web
ExecStart=/path/to/cc-switch-web/.venv/bin/python /path/to/cc-switch-web/server.py
# 挂掉立即重启（Restart=always：无论异常退出/被杀/正常退出都拉起）
Restart=always
RestartSec=2
# 可选：指定端口
# Environment=CCSW_PORT=9000

[Install]
WantedBy=multi-user.target
EOF
```

3. 启用并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cc-switch-web
```

4. 查看状态和日志：

```bash
sudo systemctl status cc-switch-web
sudo journalctl -u cc-switch-web -f
```

首次启动时查看默认密码：

```bash
sudo journalctl -u cc-switch-web | grep "Default login"
```

> systemd 守护说明：`Restart=always` 让 systemd 在进程退出后 2 秒内重新拉起
> （`on-failure` 只覆盖异常退出，`always` 连被 `kill` 的场景也覆盖）。
> systemd 只能感知**进程退出**，感知不了进程假死（活着但不响应）；
> 如需假死保护，可再加方式四的看门狗，两者不冲突。

**方式四：看门狗 watchdog.sh（无 systemd 环境，或需要假死保护时）**

```bash
# 每 10 秒探测一次：进程不在或 /api/health 无响应（假死）都立即拉起
nohup ./watchdog.sh >> watchdog.log 2>&1 &

# 停止看门狗
pkill -f watchdog.sh
```

## 修改密码

编辑 `~/.cc-switch-web/web-auth.json`，密码为 SHA256 哈希值。

生成新密码哈希：

```python
import hashlib
print(hashlib.sha256("your-new-password".encode()).hexdigest())
```

将生成的哈希值替换到配置文件中对应用户的值即可。

首次运行会在命令行窗口显示生成的随机密码，记得保存，进入系统后可以更改密码。

## 数据与配置文件路径

| 文件 | 路径 | 说明 |
|------|------|------|
| 本应用数据库 | `~/.cc-switch-web/cc-switch.db` | 首次启动从 `~/.cc-switch/` 一次性复制，此后独立 |
| Web 认证 | `~/.cc-switch-web/web-auth.json` | 用户密码存储 |
| Claude Code | `~/.claude/settings.json` | 非原子写入（文件 watcher 需要） |
| Claude Desktop | `%LOCALAPPDATA%\{Claude,Claude-3p}\`（macOS：`~/Library/Application Support/`） | deploymentMode + configLibrary profile |
| Codex | `~/.codex/{auth.json, config.toml}` | 官方条目切换不写 auth.json（保住 ChatGPT OAuth） |
| Gemini CLI | `~/.gemini/{.env, settings.json}` | settings.json 仅浅合并，mcpServers 等保留 |
| Grok Build | `~/.grok/config.toml` | 原生 Grok TOML（`[models].default` + `[model."..."]`） |
| OpenCode | `~/.config/opencode/opencode.json` | 所有平台 XDG 一致；JSON5 读 / 标准 JSON 写 |
| OpenClaw | `~/.openclaw/openclaw.json` | JSON5 读 / 标准 JSON 写 |
| Hermes | `%LOCALAPPDATA%\hermes\config.yaml`（其他：`~/.hermes`；`HERMES_HOME` 可覆盖） | 文本级段落替换，注释与 mcp_servers 保留 |
| Pi | `~/.pi/agent/models.json`（`PI_CODING_AGENT_DIR` 可覆盖） | `settings.json` 属 Pi 原生，本应用不写 |

## 智能体两种工作模式

- **exclusive（互斥）**：claude / claude-desktop / codex / gemini / grokbuild。
  同一时刻只有一个 provider 生效；切换时先把当前 live 配置回填到旧 provider 记录，
  再写入新 provider 的 live 配置。
- **additive（累加）**：opencode / openclaw / hermes / pi。
  所有 provider 共存于原生配置文件；增删改即时同步对应条目，"切换"只负责更新默认模型指向。

## 架构

```
cc-switch-web/
  server.py             # FastAPI 服务（启动入口、路由、认证中间件）
  storage.py            # 独立存储目录 ~/.cc-switch-web/ 与一次性迁移
  db.py                 # SQLite 数据层（兼容 cc-switch schema v10）
  config_ops.py         # 公共配置读写（home 解析、原子写入、claude/openclaw 帮助函数）
  models.py             # Pydantic 数据模型
  agents/
    __init__.py         # AGENT_REGISTRY（9 个 AgentSpec，侧栏顺序）
    base.py             # AgentSpec 数据类
    claude.py / claude_desktop.py / codex.py / gemini.py / grokbuild.py
    opencode.py / openclaw.py / hermes.py / pi.py
    toml_ops.py         # 手写 TOML 渲染 + tomllib 解析
  presets/
    *_presets.py        # 9 组预设数据
  static/
    index.html          # Web 前端（单文件，内联 CSS + JS，FORM_BUILDERS/CARD_META 注册表）
  tests/
    smoke.py            # 端到端冒烟（沙箱 home，9 智能体全量）
    frontend_logic_test.js  # 前端表单收集逻辑测试（node）
  requirements.txt
  start.sh             # Linux 后台管理（自动建 venv + 后台启动/停止/重启/看日志）
  watchdog.sh          # 看门狗（进程死亡/假死时自动拉起，可配合 systemd 用）
```

### 新增 Agent

在 `agents/` 写一个模块导出 `AgentSpec`（实现 switch / import_live / load_presets /
apply_api_key，additive 型再加 sync_to_live / remove_from_live），注册到
`agents/__init__.py` 的 `AGENT_REGISTRY`，前端在 `FORM_BUILDERS` / `CARD_META` /
`MODEL_SPEC_BY_APP` 补一个条目即可，`server.py` 路由零改动。

### 测试

```bash
python tests/smoke.py            # 后端全量冒烟（自动沙箱，不碰真实配置）
node tests/frontend_logic_test.js  # 前端表单逻辑
```

## 已知限制

- 不含 MCP / Prompts / Skills / 本地代理 / 故障转移管理（对齐 cc-switch 的供应商配置子集）
- Codex 官方 OAuth 登录流程由 Codex CLI 自己管理，本应用只保证切换官方条目时不覆盖 auth.json
- Hermes v12+ 的 `providers:` dict 是 Hermes Web UI 的只读覆盖层，本应用只管理 `custom_providers:` 列表
- Claude Desktop 仅支持 Windows / macOS，且需较新版本桌面端（deploymentMode / inference gateway 支持）；
  直连模式模型名须为 `claude-<sonnet|opus|haiku|fable>-*` 形态（桌面端白名单校验）
- json5 → 标准 JSON 写回会丢注释（桌面版同此行为）

## 安全说明

- 默认绑定 `0.0.0.0:8787`，局域网可访问
- 登录需要用户名 + 密码 + 算术验证码
- Session 有效期 7 天，存储在 HttpOnly Cookie 中
- API Key 明文存储在 SQLite（与 cc-switch 一致），建议设置数据库文件权限为 `0600`
- 如需 HTTPS，建议使用 nginx/caddy 反向代理

## 版本历史

### v2.0.0（2026-08-21）

本版本为一次大版本升级，三项核心变更：

**1. 存储独立**
- 数据目录从 `~/.cc-switch/`（与桌面版 cc-switch 共用）迁移至独立的 **`~/.cc-switch-web/`**
- 首次启动自动把 `cc-switch.db` 和 `web-auth.json` **一次性复制**过去（原件不动，桌面版不受影响），此后两边数据完全独立
- 迁移三级降级（sqlite3 backup API → 文件复制 → 空库警告启动），绝不阻断启动、绝不写回旧目录
- 新增 `CC_SWITCH_TEST_HOME` 环境变量作为全路径测试沙箱

**2. 9 个智能体全量支持**
- 新增 7 个智能体的供应商/模型配置：**Claude Desktop、Codex、Gemini CLI、Grok Build、OpenCode、Hermes、Pi**（此前仅 Claude Code / OpenClaw）
- 每个智能体均支持：供应商增删改查、预设应用（API Key 注入）、切换生效（带回填保护或条目同步）、从 live 配置导入、专属前端表单
- 新增预设共 **163 条**（claude 19 / openclaw 14 / codex 19 / gemini 23 / grokbuild 18 / opencode 21 / hermes 18 / pi 17 / claude-desktop 14）
- 后端重构为 `agents/` 包 + `AGENT_REGISTRY` 注册表（exclusive / additive 两种模式），`server.py` 路由零分支委托；前端 `FORM_BUILDERS` / `CARD_META` / 模型字段注册表
- TOML 读校验（stdlib tomllib）+ 手写渲染器 `agents/toml_ops.py`；Hermes YAML 文本级段落替换（注释与 mcp_servers 完整保留）；新增依赖 PyYAML

**3. 明暗主题**
- 新增浅色主题，顶栏 ☀️/🌙 按钮切换，localStorage 持久化，默认深色，含防 FOUC 内联脚本

**测试**：新增 `tests/smoke.py`（9 智能体端到端冒烟，沙箱隔离不碰真实配置）与 `tests/frontend_logic_test.js`（前端表单逻辑 29 项），并在真实机器上完成迁移与启动验证。

### v1.x（2026-08 之前）

- 初始版本：Web 登录认证（用户名 + 密码 + 验证码）、Claude Code 与 OpenClaw 两个智能体的供应商管理
- 数据存储在 `~/.cc-switch/`，与桌面版 cc-switch 共用

## 致谢

核心数据模型和配置逻辑来自 [cc-switch](https://github.com/farion1231/cc-switch)（MIT License, Jason Young）

## License

MIT
