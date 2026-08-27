#!/usr/bin/env python3
"""
天衍五维量化大模型 (Omni-Tactical FinLLM) · AMD GPU (192GB 显存) ROCm 极速 LoRA 训练引擎
专为 192GB 显存优化: bfloat16 原生显卡并发 + 动态题解流 + 显存监控 + 快速落盘 Checkpoint
"""
import os
import sys
import json
import time
import argparse
import torch
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, default="qwen7b", choices=["qwen7b", "xuanyuan13b", "finglm"])
args = parser.parse_args()

WORKSPACE = Path("/mnt/workspace")
if args.model == "xuanyuan13b":
    MODEL_DIR = str(WORKSPACE / "models" / "models" / "Duxiaoman-DI--XuanYuan-13B-Chat" / "snapshots" / "master")
    OUTPUT_DIR = WORKSPACE / "models" / "omni-tactical-xuanyuan13b-lora"
    model_name = "度小满轩辕-13B"
elif args.model == "finglm":
    MODEL_DIR = str(WORKSPACE / "models" / "models" / "finglm--FinGLM" / "snapshots" / "master")
    OUTPUT_DIR = WORKSPACE / "models" / "omni-tactical-finglm-lora"
    model_name = "清华 FinGLM-6B"
else:
    MODEL_DIR = str(WORKSPACE / "models" / "models" / "Qwen--Qwen2.5-7B-Instruct" / "snapshots" / "master")
    OUTPUT_DIR = WORKSPACE / "models" / "omni-tactical-qwen7b-lora"
    model_name = "Qwen2.5-7B-Instruct"

DATA_FILE = WORKSPACE / "quant_data" / "omni_finllm_sft_train.jsonl"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = WORKSPACE / "quant_data" / "gpu_live_training_progress.log"

def log_print(msg):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()

log_print("================================================================================")
log_print(f"🚀 [天衍五维量化超脑] AMD 192GB 显存 · {model_name} 旗舰 GPU 强化微调开跑")
log_print("================================================================================")
log_print(f"🎯 基座模型: {MODEL_DIR}")
log_print(f"📊 训练样本: {DATA_FILE}")
log_print(f"💾 输出目录: {OUTPUT_DIR}")

# 1. 检查 GPU 状态
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3) if torch.cuda.is_available() else 0
log_print(f"🔥 GPU 硬件就绪: 显存总容量 {vram_gb:.2f} GB (ROCm bfloat16 极速加速模式)")

# 2. 载入 Tokenizer
log_print("⏳ 正在载入 Tokenizer 与词表...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 3. 载入模型推入 192GB 显存
log_print(f"⏳ 正在将 {model_name} 推入 192GB 显存 (bfloat16)...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR,
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",
    trust_remote_code=True
)

# 4. 注入 LoRA 适配器
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=64,
    lora_alpha=128,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# 5. 数据集解析 (动态长度)
class FinDataset(Dataset):
    def __init__(self, data_path, max_len=1024):
        self.samples = []
        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.samples.append(json.loads(line))
        self.max_len = max_len
        log_print(f"✅ 成功载入 {len(self.samples)} 条微观物理场思维链训练样本！")

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
        
        enc = tokenizer(full_text, truncation=True, max_length=self.max_len, padding="max_length", return_tensors="pt")
        input_ids = enc["input_ids"].squeeze(0)
        attention_mask = enc["attention_mask"].squeeze(0)
        labels = input_ids.clone()
        labels[attention_mask == 0] = -100
        return {"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels}

dataset = FinDataset(DATA_FILE, max_len=1024)
batch_size = 4
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# 6. 优化器与训练循环 (高并发 GPU 吞吐)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
grad_accum_steps = 4
save_milestones = {10, 25, 50, 100, 200, 500, 1000}
total_steps = len(dataloader) // grad_accum_steps * 3

log_print(f"🔥 GPU 训练正式开始！Batch Size: {batch_size}, 梯度累积: {grad_accum_steps}, 早期存盘点: {sorted(save_milestones)}")

step = 0
accum_loss = 0.0
start_time = time.time()
step_start_time = time.time()

model.train()
for epoch in range(3):
    log_print(f"📢 === 开始 Epoch {epoch+1}/3 ===")
    for batch_idx, batch in enumerate(dataloader):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss / grad_accum_steps
        loss.backward()
        accum_loss += loss.item() * grad_accum_steps

        if (batch_idx + 1) % grad_accum_steps == 0:
            optimizer.step()
            optimizer.zero_grad()
            step += 1
            step_time = time.time() - step_start_time
            step_start_time = time.time()

            current_loss = accum_loss / grad_accum_steps
            samples_seen = step * batch_size * grad_accum_steps
            total_elapsed = time.time() - start_time
            avg_step_time = total_elapsed / max(step, 1)
            eta_mins = (total_steps - step) * avg_step_time / 60
            vram_used = torch.cuda.memory_allocated(0) / (1024**3) if torch.cuda.is_available() else 0
            
            log_print(f"⚡ [Epoch {epoch+1} | Step {step}/{total_steps}] Loss: {current_loss:.4f} | 单步: {step_time:.2f}s | 显存: {vram_used:.1f}GB / {vram_gb:.0f}GB | 题解: {samples_seen} | 预计剩余: {eta_mins:.1f}分钟")
            accum_loss = 0.0

            if step in save_milestones or step % 50 == 0:
                ckpt_dir = OUTPUT_DIR / f"checkpoint-{step}"
                log_print(f"💾 [阶段成果落盘] 正在将 {model_name} LoRA 权重保存至: {ckpt_dir} ...")
                model.save_pretrained(ckpt_dir)
                tokenizer.save_pretrained(ckpt_dir)
                log_print(f"🎉 ✅ Checkpoint-{step} 权重已成功落盘！")

log_print(f"🎉 [训练圆满完成] 最终 {model_name} LoRA 适配器权重已全部就绪！")
model.save_pretrained(OUTPUT_DIR / "final_adapter")
tokenizer.save_pretrained(OUTPUT_DIR / "final_adapter")
