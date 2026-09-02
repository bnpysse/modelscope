#!/bin/bash
# ==============================================================================
# 🔥 ModelScope AMD GPU (192GB 显存 / ROCm) 一键满载点火脚本 🔥
# ==============================================================================

echo "===================================================================="
echo "🚀 正在检测 AMD ROCm 192GB 显存状态..."
echo "===================================================================="
rocminfo 2>/dev/null || rocm-smi 2>/dev/null || nvidia-smi 2>/dev/null || true

cd /mnt/workspace
pip install -q transformers peft datasets accelerate sentencepiece protobuf

echo "===================================================================="
echo "👑 启动 Qwen2.5-32B 终极全息物理对齐训练 (Batch Size 8 | 192GB 显存)..."
echo "===================================================================="
nohup python3 scripts/amd_rocm_32b_turbo_train.py > /mnt/workspace/training_32b_rocm.log 2>&1 &

sleep 3
ps aux | grep amd_rocm_32b | grep -v grep
echo "🎉 训练进程已在后台全速轰鸣！日志输出: /mnt/workspace/training_32b_rocm.log"
