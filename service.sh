#!/usr/bin/env bash
# service.sh — 原神语音 TTS WebUI (PyTorch / GPU) 启停管理
# 用法：./service.sh {start|stop|restart|status|logs}

set -euo pipefail

SERVICE_NAME="genshin-tts-pytorch"
PORT=7861
PROJECT_DIR="/root/python/genshin-sparktts"
PYTHON_BIN="/root/miniconda3/bin/python3.13"

LOG_DIR="/root/logs/genshin-tts"
mkdir -p "${LOG_DIR}"
PID_FILE="${LOG_DIR}/service.pid"
LOG_FILE="${LOG_DIR}/service.log"

is_running() {
  [ -f "${PID_FILE}" ] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null
}

start() {
  if is_running; then
    echo "✓ ${SERVICE_NAME} 已在运行中 (PID=$(cat "${PID_FILE}"))"
    return 0
  fi
  echo "正在启动 ${SERVICE_NAME} (PyTorch / 端口: ${PORT})..."
  cd "${PROJECT_DIR}"
  nohup "${PYTHON_BIN}" webui.py > "${LOG_FILE}" 2>&1 &
  echo $! > "${PID_FILE}"
  sleep 3
  if is_running; then
    echo "✓ 启动成功  PID=$(cat "${PID_FILE}")  端口=${PORT}"
    echo "  访问地址: http://171.80.15.136:${PORT}/"
  else
    echo "✗ 启动失败，请检查日志: tail -n 50 ${LOG_FILE}"
    exit 1
  fi
}

stop() {
  if ! is_running; then
    echo "- ${SERVICE_NAME} 未在运行"
    rm -f "${PID_FILE}"
    return 0
  fi
  local pid
  pid=$(cat "${PID_FILE}")
  echo "正在停止 ${SERVICE_NAME} (PID=${pid})..."
  kill "${pid}" 2>/dev/null || true
  for _ in {1..15}; do
    if ! kill -0 "${pid}" 2>/dev/null; then
      break
    fi
    sleep 1
  done
  if kill -0 "${pid}" 2>/dev/null; then
    kill -9 "${pid}" 2>/dev/null || true
  fi
  rm -f "${PID_FILE}"
  echo "✓ 已停止"
}

status() {
  if is_running; then
    echo "✓ ${SERVICE_NAME} 运行中 (PID=$(cat "${PID_FILE}"))  端口=${PORT}"
  else
    echo "✗ ${SERVICE_NAME} 未运行"
  fi
}

logs() {
  tail -f -n "${1:-50}" "${LOG_FILE}"
}

case "${1:-}" in
  start)        start ;;
  stop)         stop ;;
  restart)      stop; sleep 1; start ;;
  status)       status ;;
  logs)         logs "${2:-50}" ;;
  *)
    echo "用法: $0 {start|stop|restart|status|logs}"
    exit 1
    ;;
esac
