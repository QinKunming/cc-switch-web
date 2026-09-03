#!/usr/bin/env bash
# cc-switch-web 看门狗：进程死掉或 /api/health 无响应时，立即通过 start.sh 拉起服务。
#
# 适用场景：没有 systemd 的环境（WSL1、部分容器），或想在 systemd 之外
# 额外加一层"健康探测"（systemd 只能感知进程退出，感知不到进程假死）。
#
# 启动看门狗（后台常驻）:
#   nohup ./watchdog.sh >> watchdog.log 2>&1 &
#
# 停止看门狗:
#   pkill -f watchdog.sh
#
# 可用环境变量:
#   CCSW_PORT            服务端口（默认 8787，须与 start.sh 一致）
#   CCSW_WATCH_INTERVAL  探测间隔秒数（默认 10）
set -u

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTERVAL="${CCSW_WATCH_INTERVAL:-10}"
URL="http://127.0.0.1:${CCSW_PORT:-8787}/api/health"

now() { date '+%F %T'; }

# 用系统 python3 探测（不依赖 curl；/api/health 是免认证端点）
health_ok() {
  python3 -c "
import sys, urllib.request
try:
    with urllib.request.urlopen('$URL', timeout=5) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
" 2>/dev/null
}

echo "$(now) [watchdog] 启动，每 ${INTERVAL}s 探测一次: $URL"

while true; do
  if ! "$APP_DIR/start.sh" status >/dev/null 2>&1; then
    echo "$(now) [watchdog] 进程不在运行 -> start"
    "$APP_DIR/start.sh" start
  elif ! health_ok; then
    echo "$(now) [watchdog] 健康检查失败（进程疑似假死）-> restart"
    "$APP_DIR/start.sh" restart
  fi
  sleep "$INTERVAL"
done
