#!/bin/bash
# DSW 自动心跳保活脚本 (MacOS / 本地端)
PORT=${1:-14010}
HOST="10.tcp.cpolar.top"

echo "🟢 [DSW 保活心跳] 已启动，正在通过 ${HOST}:${PORT} 定期发送活跃心跳..."

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -p "$PORT" "root@$HOST" "uptime > /dev/null" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "[$TIMESTAMP] 💓 心跳成功触达 DSW (活跃状态维持)"
    else
        echo "[$TIMESTAMP] ⚠️ 探测超时或端口变动，正在重试..."
    fi
    sleep 120
done
