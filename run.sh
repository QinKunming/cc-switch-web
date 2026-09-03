#!/usr/bin/env bash
# cc-switch-web 后台服务管理脚本（Ubuntu / Linux / macOS）
#
# 用法:
#   ./run.sh            # 等同于 start
#   ./run.sh start      # 首次自动建 venv + 装依赖，后台启动
#   ./run.sh stop       # 停止
#   ./run.sh restart    # 重启
#   ./run.sh status     # 查看运行状态
#   ./run.sh log [N]    # 查看最近 N 行日志（默认 50）
#
# 可用环境变量覆盖:
#   CCSW_HOST       监听地址，默认 0.0.0.0
#   CCSW_PORT       监听端口，默认 8787
#   CCSW_PIP_INDEX  pip 镜像源（弱网/PyPI 直连超时时用，如清华/阿里云源）
#   例: CCSW_PORT=9000 ./run.sh restart
#       CCSW_PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple ./run.sh start
set -u

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/.venv"
PID_FILE="$APP_DIR/cc-switch-web.pid"
LOG_FILE="$APP_DIR/cc-switch-web.log"
STAMP_FILE="$VENV_DIR/.requirements.stamp"

HOST="${CCSW_HOST:-0.0.0.0}"
PORT="${CCSW_PORT:-8787}"

is_running() {
  [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null
}

# 确保 venv 与依赖就绪（幂等：依赖没变不重复安装）
ensure_env() {
  if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "[ccsw] 创建虚拟环境: $VENV_DIR"
    python3 -m venv "$VENV_DIR" || { echo "[ccsw] 错误: venv 创建失败（需要 python3-venv: sudo apt install python3-venv）"; exit 1; }
  fi
  if [ ! -f "$STAMP_FILE" ] || ! cmp -s "$APP_DIR/requirements.txt" "$STAMP_FILE"; then
    local idx="${CCSW_PIP_INDEX:-${PIP_INDEX_URL:-}}"
    local -a cmd=("$VENV_DIR/bin/pip" install -q --disable-pip-version-check)
    [ -n "$idx" ] && cmd+=(-i "$idx")
    cmd+=(-r "$APP_DIR/requirements.txt")
    local ok=1 attempt
    for attempt in 1 2 3; do
      echo "[ccsw] 安装/更新依赖 ... (第 $attempt/3 次${idx:+，源: $idx})"
      if "${cmd[@]}"; then ok=0; break; fi
      [ "$attempt" -lt 3 ] && { echo "[ccsw] 安装失败，5 秒后重试"; sleep 5; }
    done
    if [ "$ok" -ne 0 ]; then
      echo "[ccsw] 错误: 依赖安装失败（已重试 3 次）"
      echo "[ccsw] 提示: PyPI 直连超时可改用国内镜像，例如:"
      echo "[ccsw]   CCSW_PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple ./run.sh start"
      exit 1
    fi
    cp "$APP_DIR/requirements.txt" "$STAMP_FILE"
  fi
}

do_start() {
  if is_running; then
    echo "[ccsw] 已在运行 (pid $(cat "$PID_FILE"))  http://$HOST:$PORT"
    return 0
  fi
  ensure_env
  echo "[ccsw] 启动中: http://$HOST:$PORT   日志: $LOG_FILE"
  (
    cd "$APP_DIR" || exit 1
    exec nohup "$VENV_DIR/bin/python" server.py --host="$HOST" --port="$PORT" >>"$LOG_FILE" 2>&1
  ) &
  echo $! >"$PID_FILE"
  sleep 2
  if is_running; then
    echo "[ccsw] 已启动 (pid $(cat "$PID_FILE"))"
    # 首次启动的默认密码在日志里，顺手提示一下
    awk '/Default login/ {line=$0} END {if (line != "") print "[ccsw] " line}' "$LOG_FILE"
  else
    echo "[ccsw] 启动失败，最近日志："
    tail -n 20 "$LOG_FILE"
    rm -f "$PID_FILE"
    return 1
  fi
}

do_stop() {
  if ! is_running; then
    echo "[ccsw] 未在运行"
    rm -f "$PID_FILE"
    return 0
  fi
  local pid
  pid="$(cat "$PID_FILE")"
  echo "[ccsw] 停止中 (pid $pid) ..."
  kill "$pid" 2>/dev/null
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    kill -0 "$pid" 2>/dev/null || { rm -f "$PID_FILE"; echo "[ccsw] 已停止"; return 0; }
    sleep 0.5
  done
  echo "[ccsw] 强制结束 (kill -9)"
  kill -9 "$pid" 2>/dev/null
  rm -f "$PID_FILE"
}

do_status() {
  if is_running; then
    echo "[ccsw] running (pid $(cat "$PID_FILE"))  http://$HOST:$PORT"
    return 0
  else
    echo "[ccsw] stopped"
    return 1
  fi
}

case "${1:-start}" in
  start)   do_start ;;
  stop)    do_stop ;;
  restart) do_stop; do_start ;;
  status)  do_status ;;
  log)     [ -f "$LOG_FILE" ] && tail -n "${2:-50}" "$LOG_FILE" || echo "[ccsw] 暂无日志" ;;
  *) echo "用法: $0 {start|stop|restart|status|log [N]}"; exit 1 ;;
esac
