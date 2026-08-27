#!/usr/bin/env python3
"""
天衍五维量化大模型 (Omni-Tactical FinLLM) · CPU 高性能高可见度 LoRA 强化训练引擎
专为 32GB CPU 实例优化: float16 显存映射 + 每步实时心跳 + 早期快速存盘 (Step 10, 25, 50)
"""
import os
import sys
import json
import time
import torch
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType

WORKSPACE = Path("/mnt/workspace")
MODEL_DIR = str(WORKSPACE / "models" / "models" / "Qwen--Qwen2.5-7B-Instruct" / "snapshots" / "master")
DATA_FILE = WORKSPACE / "quant_data" / "omni_finllm_sft_train.jsonl"
OUTPUT_DIR = WORKSPACE / "models" / "omni-tactical-qwen7b-lora"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = WORKSPACE / "quant_data" / "live_training_progress.log"

def log_print(msg):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()

log_print("================================================================================")
log_print("🚀 [天衍五维量化超脑] 启动 CPU 极速 LoRA 强化训练 (每步实时汇报版)")
log_print("================================================================================")
log_print(f"🎯 基座模型: {MODEL_DIR}")
log_print(f"📊 训练样本: {DATA_FILE}")
log_print(f"💾 输出目录: {OUTPUT_DIR}")

# 1. 载入 Tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 2. 载入模型 (float16 + 低内存映射)
log_print("⏳ 正在载入 7B 模型权重 (float16 / low_cpu_mem_usage)...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR,
    torch_dtype=torch.float16,
    device_map="cpu",
    low_cpu_mem_usage=True,
    trust_remote_code=True
)

# 3. 注入 LoRA 适配器
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=32,
    lora_alpha=64,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# 4. 数据集解析与 Tokenize (动态长度截断加速)
class FinDataset(Dataset):
    def __init__(self, data_path, max_len=768):
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

dataset = FinDataset(DATA_FILE, max_len=768)
dataloader = DataLoader(dataset, batch_size=2, shuffle=True)

# 5. 优化器与训练循环
optimizer = torch.optim.AdamW(model.parameters(), lr=1.5e-4, weight_decay=0.01)
grad_accum_steps = 4  # 降低累积步数，加速单 step 更新频率
save_milestones = {10, 25, 50, 100, 200, 500}
total_steps = len(dataloader) // grad_accum_steps * 3

log_print(f"🔥 训练正式开始！总 Batch 数: {len(dataloader)}, 梯度累积: {grad_accum_steps}, 首批检查点: {sorted(save_milestones)}")

step = 0
accum_loss = 0.0
start_time = time.time()
step_start_time = time.time()

model.train()
for epoch in range(3):
    log_print(f"📢 === 开始 Epoch {epoch+1}/3 ===")
    for batch_idx, batch in enumerate(dataloader):
        input_ids = batch["input_ids"]
        attention_mask = batch["attention_mask"]
        labels = batch["labels"]

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

            # 每 1 步实时汇报
            current_loss = accum_loss / grad_accum_steps
            samples_seen = step * 2 * grad_accum_steps
            total_elapsed = time.time() - start_time
            avg_step_time = total_elapsed / max(step, 1)
            eta_hours = (total_steps - step) * avg_step_time / 3600
            
            log_print(f"⚡ [Epoch {epoch+1} | Step {step}/{total_steps}] Loss: {current_loss:.4f} | 单步耗时: {step_time:.1f}s | 已消费题解: {samples_seen} | 预计剩余: {eta_hours:.1f}h")
            accum_loss = 0.0

            # 到达里程碑自动落盘
            if step in save_milestones or step % 50 == 0:
                ckpt_dir = OUTPUT_DIR / f"checkpoint-{step}"
                log_print(f"💾 [阶段成果落盘] 正在将 LoRA 增量权重保存至: {ckpt_dir} ...")
                model.save_pretrained(ckpt_dir)
                tokenizer.save_pretrained(ckpt_dir)
                log_print(f"🎉 ✅ Checkpoint-{step} 权重文件已成功生成落盘！")

log_print("🎉 [训练圆满完成] 最终 LoRA 适配器权重已全部就绪！")
model.save_pretrained(OUTPUT_DIR / "final_adapter")
tokenizer.save_pretrained(OUTPUT_DIR / "final_adapter")
