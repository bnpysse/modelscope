#!/bin/bash
# ==============================================================================
# 🛰️ 天衍量化系统 · 超算 1 号机智能体参谋部一键启动脚本
# ==============================================================================

export PYTHONPATH=/public/home/ac17750bxe/.local/lib/python3.12/site-packages:/public/home/ac17750bxe/tianyan_hud:$PYTHONPATH
export PATH=/public/home/ac17750bxe/.local/bin:/usr/local/python3.12/bin:$PATH

cd /public/home/ac17750bxe
python3 cli_chat.py
