#!/usr/bin/env bash
# ==============================================================================
# ModelScope PAI-DSW 云端一键部署与高吞吐数学计算主脚本
# ==============================================================================
set -e

echo "================================================================================"
echo "🛰️ [天眼全息智导 V7.0] ModelScope 云端高吞吐数学计算引擎初始化..."
echo "================================================================================"

# 1. 检查并安装核心计算依赖
echo "📦 [1/3] 检查 Python 数学与量化依赖 (Polars, NumPy, DuckDB, AkShare)..."
pip install --quiet polars numpy duckdb akshare streamlit requests pydantic

# 2. 自动恢复 SSH 证书公钥并强制禁用密码登录 (实现金融级 4096-bit 证书免密登录，杜绝暴力破解)
echo "🔑 [2/4] 配置 SSH 证书公钥免密登录并强制禁用密码登录..."
mkdir -p ~/.ssh /mnt/workspace/.ssh /mnt/workspace/quant_data/daily_parquet /mnt/workspace/quant_data/factors
if [ -f /mnt/workspace/.ssh/authorized_keys ]; then
    cp /mnt/workspace/.ssh/authorized_keys ~/.ssh/authorized_keys
    chmod 700 ~/.ssh
    chmod 600 ~/.ssh/authorized_keys
fi
sed -i -E "s/^#?PasswordAuthentication .*/PasswordAuthentication no/" /etc/ssh/sshd_config 2>/dev/null || true
sed -i -E "s/^#?ChallengeResponseAuthentication .*/ChallengeResponseAuthentication no/" /etc/ssh/sshd_config 2>/dev/null || true
service ssh restart 2>/dev/null || true

# 3. 运行全量筹码物理场微积分递推与因子库生成
echo "⚡ [3/4] 启动高精 MCD 移动成本分布积分递推与全标的物理真值求解..."
python run_cloud_compute.py

echo "================================================================================"
echo "🎉 [部署成功] 一手五维因子已全部落盘至 /mnt/workspace/quant_data/ !"
echo "================================================================================"
