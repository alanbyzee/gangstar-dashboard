#!/bin/sh
# Gangstar 粉丝数自动刷新包装脚本（供 LaunchAgent 每6小时调用）
export PATH="/Users/alan/.workbuddy/binaries/node/versions/22.22.2/bin:$PATH"
export NODE_PATH="/Users/alan/.workbuddy/binaries/node/workspace/node_modules"
cd "/Users/alan/WorkBuddy/2026-07-27-22-07-48/gangstar-ops-hub"
echo "[$(date)] refresh start" >> /tmp/gangstar_refresh.log
node refresh_fans.js --write >> /tmp/gangstar_refresh.log 2>&1
echo "[$(date)] refresh done (exit $?)" >> /tmp/gangstar_refresh.log
