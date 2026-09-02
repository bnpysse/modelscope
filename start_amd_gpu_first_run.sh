#!/usr/bin/env bash
# ==============================================================================
# 🚀 ModelScope AMD GPU (192GB / ROCm) 开机首发一键满血点火脚本 (v2.0 8小时冲刺版)
# ==============================================================================

echo "================================================================================"
echo "👑 【天衍量化系统】ModelScope 192GB AMD GPU 终极大合拢训练流水线开机点火"
echo "• 目标模式: 8 小时全速大冲刺 (Batch Size = 12 极限吞吐 / 0 提前关机)"
echo "================================================================================"

# 1. 启动 SSH 守护进程与 cpolar 专线隧道
echo "🛰️ 步骤 1/4: 激活 SSH 守护进程与 cpolar 专线隧道..."
bash /mnt/workspace/start_tunnel.sh

# 2. 探测 AMD ROCm 驱动与 192GB 显存
echo ""
echo "🔍 步骤 2/4: 探测 AMD ROCm GPU 硬件与显存状态..."
if command -v rocm-smi &> /dev/null; then
    rocm-smi --showmeminfo vram || true
else
    echo "ℹ️ ROCm SMI 工具未直接就绪，PyTorch 将通过 ROCm-HIP 驱动直接调度 192GB 显存"
fi

# 3. 补齐 ROCm 专属训练与量化依赖
echo ""
echo "📦 步骤 3/4: 检查并载入 PEFT / Transformers / Accelerate / TRL..."
pip install --quiet --upgrade peft transformers accelerate trl datasets sentencepiece

# 4. 后台点火启动 32B 终极训练 (Batch Size = 12 / 自动续训)
echo ""
echo "🔥 步骤 4/4: 后台点火启动 Qwen2.5-32B (Batch Size=12) 满血对齐流水线..."
cd /mnt/workspace

pkill -9 -f amd_rocm_32b_turbo_train.py 2>/dev/null || true
sleep 1

python3 -c "
import subprocess
with open('/mnt/workspace/training_32b_rocm.log', 'a') as f:
    p = subprocess.Popen(['python3', '/mnt/workspace/scripts/amd_rocm_32b_turbo_train.py'], cwd='/mnt/workspace', stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
print('🚀 32B 训练引擎已成功在后台点火！进程 PID:', p.pid)
"

echo "================================================================================"
echo "✅ 32B 终极训练已满血启动！自动从最新 Checkpoint 恢复续训！"
echo "📄 实时日志追踪: tail -f /mnt/workspace/training_32b_rocm.log"
echo "================================================================================"
