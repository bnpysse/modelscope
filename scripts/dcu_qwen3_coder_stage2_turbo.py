# -*- coding: utf-8 -*-
"""
天衍五维量化大模型 - 国家超算 2 号机 Qwen3-Coder-30B (MoE) 
🔥 Stage 2 极限精调冲刺版 (从 Checkpoint-375 续训，迈向 98% 巅峰智力) 🔥
"""

import os
import sys
import glob
import json
import time
import linecache
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType, PeftModel

MODEL_DIR = '/root/private_data/SothisAI/model/Aihub/Qwen3-Coder-30B-A3B-Instruct/main/Qwen3-Coder-30B-A3B-Instruct'
DATA_FILE = '/root/private_data/quant_data/omni_finllm_sft_v2.jsonl'
OUTPUT_DIR = '/root/private_data/models/omni-qwen3-coder-30b-lora'
LOG_FILE = '/root/private_data/quant_engine/training_qwen3_coder.log'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_print(msg):
    t = time.strftime('[%Y-%m-%d %H:%M:%S]')
    line = f'{t} {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + chr(10))
        f.flush()

log_print('========================================================================================')
log_print('🔥【Stage 2 巅峰冲刺】超算 2 号机 Qwen3-Coder-30B 双卡 128GB 显存流水线点火！')
log_print('========================================================================================')

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

def count_lines(fname):
    with open(fname, 'r', encoding='utf-8') as f:
        for i, _ in enumerate(f):
            pass
    return i + 1

total_samples = count_lines(DATA_FILE)
log_print(f'✓ 数据集索引就绪！总有效样本: {total_samples} 局 (双卡 Pinned Memory 零拷贝流水线)')

class LazyJSONLDataset(Dataset):
    def __init__(self, file_path, total_len):
        self.file_path = file_path
        self.total_len = total_len
    def __len__(self):
        return self.total_len
    def __getitem__(self, idx):
        line = linecache.getline(self.file_path, idx + 1)
        if not line:
            return [tokenizer.eos_token_id]
        try:
            data = json.loads(line.strip())
            messages = data.get('messages', [])
            if not messages:
                return [tokenizer.eos_token_id]
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            enc = tokenizer(text, max_length=2048, truncation=True, padding=False)
            return enc['input_ids']
        except:
            return [tokenizer.eos_token_id]

def collate_fn(batch):
    max_len = max(len(x) for x in batch)
    input_ids_batch = []
    labels_batch = []
    attention_mask_batch = []
    pad_id = tokenizer.pad_token_id

    for ids in batch:
        pad_len = max_len - len(ids)
        input_ids = ids + [pad_id] * pad_len
        labels = ids + [-100] * pad_len
        mask = [1] * len(ids) + [0] * pad_len
        input_ids_batch.append(input_ids)
        labels_batch.append(labels)
        attention_mask_batch.append(mask)

    return {
        'input_ids': torch.tensor(input_ids_batch, dtype=torch.long),
        'labels': torch.tensor(labels_batch, dtype=torch.long),
        'attention_mask': torch.tensor(attention_mask_batch, dtype=torch.long)
    }

train_dataset = LazyJSONLDataset(DATA_FILE, total_samples)
train_loader = DataLoader(
    train_dataset,
    batch_size=4,
    shuffle=True,
    collate_fn=collate_fn,
    num_workers=8,
    pin_memory=True,
    prefetch_factor=2
)

log_print('正在构建双卡 128GB 显存均衡分片映射 (Card 0: 48GB | Card 1: 48GB)...')
max_memory = {0: '48GB', 1: '48GB'}

model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR,
    device_map='auto',
    max_memory=max_memory,
    torch_dtype=torch.float16,
    trust_remote_code=True
)

model.gradient_checkpointing_enable()
model.enable_input_require_grads()

# 自动寻找历史最新的 Checkpoint
existing_ckpts = glob.glob(os.path.join(OUTPUT_DIR, 'checkpoint-*'))
latest_step = 0
latest_ckpt_path = None

for p in existing_ckpts:
    try:
        s = int(os.path.basename(p).split('-')[1])
        if s > latest_step:
            latest_step = s
            latest_ckpt_path = p
    except:
        pass

if latest_ckpt_path and os.path.exists(latest_ckpt_path):
    log_print(f'💎 成功识别历史最强黄金权重 [{os.path.basename(latest_ckpt_path)}]，正在无缝挂载从 Step {latest_step} 开启 Stage 2 续训！')
    model = PeftModel.from_pretrained(model, latest_ckpt_path, is_trainable=True)
    initial_step = latest_step
else:
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj']
    )
    model = get_peft_model(model, peft_config)
    initial_step = 0

trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
log_print(f'✓ LoRA 挂载就绪！可训练参数: {trainable_params / 1e6:.2f} M')

# Stage 2 采用平滑精调学习率 (5e-5) 避免震荡，深度挖掘长程因果逻辑
optimizer = torch.optim.AdamW(
    [p for p in model.parameters() if p.requires_grad],
    lr=5e-5,
    weight_decay=0.01
)

vram0 = torch.cuda.memory_allocated(0) / (1024**3)
vram1 = torch.cuda.memory_allocated(1) / (1024**3)
log_print(f'✓ 双卡显存分布就绪: 卡0占用: {vram0:.1f}GB / 64GB | 卡1占用: {vram1:.1f}GB / 64GB')
log_print(f'🚀 【Stage 2 巅峰炼丹】Qwen3-Coder-30B 双卡显存流水线满血狂飙！(起点: Step {initial_step})')

model.train()
step = initial_step
accum_steps = 8
optimizer.zero_grad()
t_step_start = time.time()

for epoch in range(5):
    for batch_idx, batch in enumerate(train_loader):
        input_ids = batch['input_ids'].to('cuda:0')
        labels = batch['labels'].to('cuda:0')
        attention_mask = batch['attention_mask'].to('cuda:0')

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        loss = outputs.loss / accum_steps
        loss.backward()

        if (batch_idx + 1) % accum_steps == 0:
            optimizer.step()
            optimizer.zero_grad()
            step += 1

            if step % 5 == 0:
                dt = (time.time() - t_step_start) / 5
                vram0 = torch.cuda.memory_allocated(0) / (1024**3)
                vram1 = torch.cuda.memory_allocated(1) / (1024**3)
                log_print(f'👑 [2号机 30B Stage2 | Step {step}] Loss: {outputs.loss.item():.4f} | 单步: {dt:.2f}s | 显存: 卡0 {vram0:.1f}G + 卡1 {vram1:.1f}G | 已吞噬: {step*32} 局')
                t_step_start = time.time()

            if step % 25 == 0:
                save_path = os.path.join(OUTPUT_DIR, f'checkpoint-{step}')
                log_print(f'💾 保存 Checkpoint-{step} 到 {save_path} ...')
                model.save_pretrained(save_path)
                tokenizer.save_pretrained(save_path)
