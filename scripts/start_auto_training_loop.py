#!/usr/bin/env python3
"""
天衍五维量化大模型 · 自动持续强化训练调度器
自动识别就绪的金融底座 (Qwen2.5-7B / FinGLM / XuanYuan-13B)，启动脱机后台 LoRA 微调，
并持续输出训练 loss 与阶段检查点！
"""
import os
import sys
import time
import subprocess
from pathlib import Path

WORKSPACE = Path("/mnt/workspace")
MODELS_DIR = WORKSPACE / "models"
DATA_FILE = WORKSPACE / "quant_data" / "omni_finllm_sft_train.jsonl"
LOG_FILE = WORKSPACE / "quant_data" / "live_training_progress.log"

print("================================================================================")
print("🚀 [天衍大模型自动化训练中心] 正在初始化训练任务...")
print("================================================================================")

# 寻找已就绪的模型路径
target_model_path = None
model_type = "qwen2_5-7b-instruct"

# 优先级 1: Qwen2.5-7B (阿里官方金融量化高适配)
qwen_path = MODELS_DIR / "models" / "Qwen--Qwen2.5-7B-Instruct" / "snapshots" / "master"
if not qwen_path.exists():
    qwen_path = MODELS_DIR / "Qwen" / "Qwen2.5-7B-Instruct"

# 优先级 2: FinGLM (清华金融大模型)
finglm_path = MODELS_DIR / "models" / "finglm--FinGLM" / "snapshots" / "master"
if not finglm_path.exists():
    finglm_path = MODELS_DIR / "finglm" / "FinGLM"

if qwen_path.exists():
    target_model_path = str(qwen_path)
    model_type = "qwen2_5-7b-instruct"
    out_dir = "/mnt/workspace/models/omni-tactical-qwen7b-lora"
elif finglm_path.exists():
    target_model_path = str(finglm_path)
    model_type = "chatglm3-6b"
    out_dir = "/mnt/workspace/models/omni-tactical-finglm-lora"
else:
    target_model_path = "Qwen/Qwen2.5-7B-Instruct"
    model_type = "qwen2_5-7b-instruct"
    out_dir = "/mnt/workspace/models/omni-tactical-qwen7b-lora"

print(f"🎯 选定训练基座模型: {target_model_path}")
print(f"📊 训练样本总集: {DATA_FILE} (102,280 条全市场物理题解)")
print(f"💾 输出检查点目录: {out_dir}")

cmd = [
    "/usr/local/bin/swift", "sft",
    "--model_type", model_type,
    "--model_id_or_path", target_model_path,
    "--sft_type", "lora",
    "--dataset", str(DATA_FILE),
    "--output_dir", out_dir,
    "--num_train_epochs", "3",
    "--max_length", "1024",
    "--batch_size", "2",
    "--gradient_accumulation_steps", "8",
    "--learning_rate", "1e-4",
    "--lora_rank", "64",
    "--lora_alpha", "128",
    "--gradient_checkpointing", "true",
    "--save_steps", "50",
    "--save_total_limit", "3",
    "--logging_steps", "2"
]

log_f = open(LOG_FILE, "a")
print(f"🔥 启动脱机后台微调守护进程，日志输出至: {LOG_FILE} ...")
proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT, start_new_session=True)
print(f"✅ 训练守护进程已成功拉起！PID: {proc.pid}")
