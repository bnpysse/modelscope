#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维量化大模型 (Omni-Tactical FinLLM) · 第三阶段 (Stage 3) 战术动能强化与实战博弈特训
专为 AMD Instinct (192GB 显存) ROCm 极速架构设计:
1. 继承 Stage 2 的 checkpoint-4100 基石权重
2. 聚焦四大实战极限博弈场景:
   - ⚡ 超导死锁与物理真空跃迁 (CPR >= 20, BRI >= 30, eta_V >= 0.02)
   - 🛑 假突破对倒出货一票否决预警 (SMPI <= -0.2, 高换手, Scissor死叉)
   - 💎 战略黄金坑逆向超卖反转 (CYS34 < -15%, CYF拐点)
   - 🌊 跨周期斐波那契动能压阵 (CYF66_Raw / VMA55 动能差扩张)
3. bfloat16 原生显卡并发 + 动态题解流 + 独立显存通道
"""

import os
import sys
import json
import time
import argparse
import shutil
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, LoraConfig, get_peft_model, TaskType

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, default="qwen7b")
parser.add_argument("--batch_size", type=int, default=8, help="Stage 3 高并发 Batch Size (192G 显存推荐 8~16)")
parser.add_argument("--grad_accum", type=int, default=2, help="梯度累积步数")
parser.add_argument("--lr", type=float, default=5e-5, help="Stage 3 强化微调学习率")
parser.add_argument("--base_checkpoint", type=str, default="checkpoint-4100", help="Stage 2 继承权重")
args = parser.parse_args()

WORKSPACE = Path("/mnt/workspace") if Path("/mnt/workspace").exists() else Path(__file__).resolve().parent.parent
ROOT_OUT = Path("/root/train_output/omni-tactical-qwen7b-stage3")
ROOT_LOGS = Path("/root/quant_data")
ROOT_OUT.mkdir(parents=True, exist_ok=True)
ROOT_LOGS.mkdir(parents=True, exist_ok=True)

MODEL_BASE_DIR = str(WORKSPACE / "models" / "models" / "Qwen--Qwen2.5-7B-Instruct" / "snapshots" / "master")
STAGE2_CKPT_DIR = WORKSPACE / "models" / "omni-tactical-qwen7b-lora" / args.base_checkpoint
LOG_FILE = ROOT_LOGS / "stage3_training_progress.log"
DATA_FILE = WORKSPACE / "quant_data" / "omni_finllm_sft_v2.jsonl"
if not DATA_FILE.exists():
    DATA_FILE = WORKSPACE / "quant_data" / "omni_finllm_sft_train.jsonl"

def log_print(msg):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
    except Exception as e:
        print(f"Log write error: {e}", flush=True)

# 1. 检查 GPU 硬件状态
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3) if torch.cuda.is_available() else 0
gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"

log_print("================================================================================")
log_print("⚔️ [天衍五维量化超脑] 第三阶段 (Stage 3) 战术动能与实战博弈特训正式开跑")
log_print(f"🔥 GPU 硬件就绪: {gpu_name} (显存总容量 {vram_gb:.2f} GB, bfloat16 极速模式)")
log_print(f"🎯 基座模型: {MODEL_BASE_DIR}")
log_print(f"📦 承接 Stage 2 权重: {STAGE2_CKPT_DIR}")
log_print(f"📊 特训数据集: {DATA_FILE}")
log_print(f"💾 Stage 3 输出目录: {ROOT_OUT}")
log_print("================================================================================")

# 2. 载入 Tokenizer
log_print("⏳ 正在载入 Tokenizer 与词表...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_BASE_DIR, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 3. 载入基座模型与 Stage 2 Checkpoint 融合
log_print("⏳ 正在加载 Qwen2.5-7B 基座模型 (bfloat16)...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_BASE_DIR,
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",
    trust_remote_code=True
)

if STAGE2_CKPT_DIR.exists():
    log_print(f"🔄 成功加载 Stage 2 基石权重: {STAGE2_CKPT_DIR.name}，开启 Stage 3 战术动能特训！")
    model = PeftModel.from_pretrained(model, str(STAGE2_CKPT_DIR), is_trainable=True)
else:
    log_print("⚠️ 未找到指定 Stage 2 Checkpoint，创建新 LoRA 适配层...")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=64,
        lora_alpha=128,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )
    model = get_peft_model(model, lora_config)

if hasattr(model, "enable_input_require_grads"):
    model.enable_input_require_grads()
model.gradient_checkpointing_enable()
model.print_trainable_parameters()

# 4. 数据集解析与动态批次
class Stage3Dataset(Dataset):
    def __init__(self, data_path, max_len=1024):
        self.samples = []
        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.samples.append(json.loads(line))
        self.max_len = max_len
        log_print(f"✅ Stage 3 成功载入 {len(self.samples)} 条实战博弈思维链训练样本！")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        sys_p = item.get("system", "")
        messages = item.get("messages", [])
        
        full_text = ""
        if sys_p:
            full_text += f"<|im_start|>system\n{sys_p}<|im_end|>\n"
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            full_text += f"<|im_start|>{role}\n{content}<|im_end|>\n"
        
        enc = tokenizer(full_text, truncation=True, max_length=self.max_len, padding=False, return_tensors="pt")
        input_ids = enc["input_ids"].squeeze(0)
        labels = input_ids.clone()
        return {"input_ids": input_ids, "labels": labels}

def pad_collate_fn(batch):
    input_ids = [item["input_ids"] for item in batch]
    labels = [item["labels"] for item in batch]
    
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
    input_ids_padded = torch.nn.utils.rnn.pad_sequence(input_ids, batch_first=True, padding_value=pad_id)
    labels_padded = torch.nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=-100)
    attention_mask = (input_ids_padded != pad_id).long()
    
    return {
        "input_ids": input_ids_padded,
        "attention_mask": attention_mask,
        "labels": labels_padded
    }

dataset = Stage3Dataset(DATA_FILE, max_len=1024)
batch_size = args.batch_size
grad_accum_steps = args.grad_accum
dataloader = DataLoader(
    dataset, 
    batch_size=batch_size, 
    shuffle=True, 
    collate_fn=pad_collate_fn,
    pin_memory=True,
    num_workers=4
)

optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
total_steps = len(dataloader) // grad_accum_steps * 3

log_print(f"⚔️ Stage 3 训练开跑！Batch Size: {batch_size}, 梯度累积: {grad_accum_steps}, 目标总 Step: {total_steps}")

step = 0
accum_loss = 0.0
start_time = time.time()
step_start_time = time.time()

model.train()
torch.cuda.empty_cache()

for epoch in range(3):
    log_print(f"📢 === 开始 Stage 3 Epoch {epoch+1}/3 ===")
    for batch_idx, batch in enumerate(dataloader):
        input_ids = batch["input_ids"].to(device, non_blocking=True)
        attention_mask = batch["attention_mask"].to(device, non_blocking=True)
        labels = batch["labels"].to(device, non_blocking=True)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        loss = outputs.loss / grad_accum_steps
        loss.backward()
        accum_loss += loss.item() * grad_accum_steps

        if (batch_idx + 1) % grad_accum_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            optimizer.zero_grad()
            step += 1

            step_duration = time.time() - step_start_time
            step_start_time = time.time()

            vram_used = torch.cuda.memory_allocated(0) / (1024**3) if torch.cuda.is_available() else 0
            vram_total = torch.cuda.get_device_properties(0).total_memory / (1024**3) if torch.cuda.is_available() else 0

            if step % 1 == 0:
                elapsed = time.time() - start_time
                avg_step_time = elapsed / step if step > 0 else step_duration
                remaining_steps = total_steps - step
                est_remaining_min = (remaining_steps * avg_step_time) / 60.0

                log_print(
                    f"⚔️ [Stage 3 | Step {step}/{total_steps}] "
                    f"Loss: {accum_loss/grad_accum_steps:.4f} | "
                    f"单步: {step_duration:.2f}s | "
                    f"显存: {vram_used:.1f}GB / {vram_total:.0f}GB | "
                    f"题解: {step * batch_size * grad_accum_steps} | "
                    f"预计剩余: {est_remaining_min:.1f}分钟"
                )
            accum_loss = 0.0

            # 每 50 步保存 Checkpoint 并同步持久化
            if step % 50 == 0:
                ckpt_dir = ROOT_OUT / f"checkpoint-{step}"
                model.save_pretrained(str(ckpt_dir))
                tokenizer.save_pretrained(str(ckpt_dir))
                log_print(f"💾 [Stage 3 权重落盘] 成功保存 {ckpt_dir.name} 至本地 NVMe！")

                perm_out_dir = WORKSPACE / "models" / "omni-tactical-qwen7b-stage3" / f"checkpoint-{step}"
                perm_out_dir.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copytree(ckpt_dir, perm_out_dir, dirs_exist_ok=True)
                    log_print(f"☁️ [持久化同步] 成功同步 {ckpt_dir.name} 至共享云盘！")
                except Exception as e:
                    log_print(f"⚠️ 持久化同步警告: {e}")

log_print("🎉 [Stage 3 达成] 战术动能与实战博弈特训圆满完成！")
