#!/bin/bash
# ==============================================================================
# 🛰️ 超算 1 号机 Streamlit 作战大盘本地高速直连穿梭隧道
# ==============================================================================

pkill -f "8501:127.0.0.1:8501" 2>/dev/null || true
sleep 1

ssh -i /Users/woodman/.ssh/scnet_node1_id_rsa \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=5 \
    -p 65032 \
    -N -L 8501:127.0.0.1:8501 \
    ac17750bxe@zzeshell.scnet.cn >/dev/null 2>&1 &

echo "🟢 超算 1 号机前端已映射至本地！"
echo "👉 请在浏览器直接打开: http://localhost:8501"
