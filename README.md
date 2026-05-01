# CC Switch Web

## 痛点：

现有的cc-switch只能用于图形界面，cc-switch-cli只能用于命令行模式。

有时候为了保障服务器性能，基本上都没有安装图形界面；

对于不喜欢命令行模式的朋友来说，配置claude code或openclaw的模型就比较麻烦，不同模型之间切换更麻烦。

这个Web 端 AI Agent 模型切换管理工具，借鉴 [cc-switch](https://github.com/farion1231/cc-switch) 的核心数据模型，

同时支持无图形界面的服务器和有图形界面的桌面环境。

当前支持 **Claude Code** 和 **OpenClaw**，架构已预留 OpenCode、Codex 等 Agent 扩展。

## 功能

- **Web 管理**：浏览器操作，无需 GUI
- **Provider 管理**：添加、编辑、删除、一键切换
- **预设导入**：19 个 Claude Code 预设 + 14 个 OpenClaw 预设
- **热切换**：Claude Code 切换后无需重启
- **回填保护**：切换前自动保存当前配置，手动改动不丢失
- **登录认证**：用户名 + 密码 + 验证码，防止公网服务器未授权访问泄露api
- **数据库**：`~/.cc-switch/cc-switch.db`

## 快速开始

### 前置要求

- Python 3.11+

### 安装

```bash
cd cc-switch-web
pip install -r requirements.txt
```

### 启动

```bash
python server.py
```

首次启动会自动生成默认密码并打印到控制台：

```
  CC Switch Web
  Default login: admin / xxxxxxxx
  Change password in ~/.cc-switch/web-auth.json
  Local:   http://127.0.0.1:8787
  Network: http://192.168.x.x:8787
```

打开浏览器访问 `http://<ip>:8787`，使用打印的账号密码登录。

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

**方式二：开机自启（Task Scheduler）**

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

**方式二：systemd 服务（推荐）**

1. 创建服务文件：

```bash
sudo tee /etc/systemd/system/cc-switch-web.service << 'EOF'
[Unit]
Description=CC Switch Web
After=network.target

[Service]
Type=simple
User=<你的用户名>
WorkingDirectory=/path/to/cc-switch-web
ExecStart=/usr/bin/python3 /path/to/cc-switch-web/server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

2. 启用并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable cc-switch-web
sudo systemctl start cc-switch-web
```

3. 查看状态和日志：

```bash
sudo systemctl status cc-switch-web
sudo journalctl -u cc-switch-web -f
```

首次启动时查看默认密码：

```bash
sudo journalctl -u cc-switch-web | grep "Default login"
```

**方式三：后台运行（简单方式）**

```bash
nohup python3 server.py > cc-switch.log 2>&1 &
# 查看初始密码
head -5 cc-switch.log
```

## 修改密码

编辑 `~/.cc-switch/web-auth.json`，密码为 SHA256 哈希值。

生成新密码哈希：

```python
import hashlib
print(hashlib.sha256("your-new-password".encode()).hexdigest())
```

将生成的哈希值替换到配置文件中对应用户的值即可。

## 配置文件路径

| 文件 | 路径 | 说明 |
|------|------|------|
| Claude Code | `~/.claude/settings.json` | 自动检测 |
| OpenClaw | `~/.openclaw/openclaw.json` | JSON5 格式，写入标准 JSON |
| cc-switch 数据库 | `~/.cc-switch/cc-switch.db` | 与桌面版共享 |
| Web 认证 | `~/.cc-switch/web-auth.json` | 用户密码存储 |

## 架构

```
cc-switch-web/
  server.py           # FastAPI 服务（启动入口、路由、认证中间件）
  db.py               # SQLite 数据层（兼容 cc-switch schema v10）
  config_ops.py       # 配置文件读写、原子写入、回填
  models.py           # Pydantic 数据模型
  presets/
    claude_presets.py  # Claude Code 预设（19 个）
    openclaw_presets.py # OpenClaw 预设（14 个）
  static/
    index.html         # Web 前端（单文件，内联 CSS + JS）
  requirements.txt
```

### Agent 扩展

在 `server.py` 的 `AGENT_REGISTRY` 中注册新 Agent：

```python
AGENT_REGISTRY = {
    "claude":    {"name": "Claude Code", "icon": "🤖", "configurable": True},
    "openclaw":  {"name": "OpenClaw",    "icon": "🐾", "configurable": True},
    "opencode":  {"name": "OpenCode",    "icon": "🔵", "configurable": False},
    "codex":     {"name": "Codex",       "icon": "⚡", "configurable": False},
}
```

设置 `configurable: True` 后，该 Agent 会出现在侧边栏并支持 provider 管理。需要同时实现对应的切换逻辑和预设数据。

## 安全说明

- 默认绑定 `0.0.0.0:8787`，局域网可访问
- 登录需要用户名 + 密码 + 算术验证码
- Session 有效期 7 天，存储在 HttpOnly Cookie 中
- API Key 明文存储在 SQLite（与 cc-switch 一致），建议设置数据库文件权限为 `0600`
- 如需 HTTPS，建议使用 nginx/caddy 反向代理

## 致谢

核心数据模型和配置逻辑来自 [cc-switch](https://github.com/farion1231/cc-switch)（MIT License, Jason Young）

## License

MIT
