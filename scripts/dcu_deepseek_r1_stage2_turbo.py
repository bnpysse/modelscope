# -*- coding: utf-8 -*-
"""
天衍五维量化大模型 - 国家超算 1 号机 DeepSeek-R1-7B 
🔥 Stage 2 巅峰冲刺引擎 (从 Checkpoint-4900 无缝续训，突破 20 万局大圆满) 🔥
"""

import os
import sys
import glob
import json
import time
import argparse
from multiprocessing import Pool
from pathlib import Path
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import Dataset, DataLoader, DistributedSampler
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType, PeftModel

local_rank = int(os.environ.get('LOCAL_RANK', 0))
world_size = int(os.environ.get('WORLD_SIZE', 1))
if world_size > 1:
    dist.init_process_group(backend='nccl')
torch.cuda.set_device(local_rank)
device = torch.device(f'cuda:{local_rank}')

MODEL_DIR = '/root/private_data/SothisAI/model/Aihub/DeepSeek-R1-Distill-Qwen-7B/main/DeepSeek-R1-Distill-Qwen-7B'
DATA_FILE = '/root/private_data/quant_data/omni_finllm_sft_v2.jsonl'
OUTPUT_DIR = '/root/private_data/models/omni-deepseek-r1-7b-lora'
LOG_FILE = '/root/private_data/quant_engine/training_turbo.log'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_print(msg):
    if local_rank == 0:
        t = time.strftime('[%Y-%m-%d %H:%M:%S]')
        line = f'{t} {msg}'
        print(line, flush=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + chr(10))
            f.flush()

log_print('========================================================================================')
log_print(f'🔥【Stage 2 巅峰冲刺】1 号机 DeepSeek-R1-7B 双卡满血点火 | GPU卡数: {world_size} | 本地卡: {local_rank}')
log_print('========================================================================================')

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

def _tokenize_line(line_text):
    try:
        data = json.loads(line_text.strip())
        messages = data.get('messages', [])
        if not messages:
            return None
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        enc = tokenizer(text, max_length=2048, truncation=True, padding=False)
        return enc['input_ids']
    except:
        return None

log_print(f'正在利用 24 核心 CPU 并行极速预分词数据集: {DATA_FILE} ...')
t0 = time.time()
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

with Pool(24) as pool:
    tokenized_samples = pool.map(_tokenize_line, lines, chunksize=2000)

samples = [s for s in tokenized_samples if s is not None]
log_print(f'✓ 数据集预载完成！有效样本: {len(samples)} 局，耗时: {time.time()-t0:.1f} 秒')

class InMemoryDataset(Dataset):
    def __init__(self, data_list):
        self.data = data_list
    def __len__(self):
        return len(self.data)
    def __getitem__(self, idx):
        return self.data[idx]

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
        'input_ids': torch.tensor(input_ids_batch, dtype=torch.long, device=device),
        'labels': torch.tensor(labels_batch, dtype=torch.long, device=device),
        'attention_mask': torch.tensor(attention_mask_batch, dtype=torch.long, device=device)
    }

train_dataset = InMemoryDataset(samples)
sampler = DistributedSampler(train_dataset, shuffle=True) if world_size > 1 else None
dataloader = DataLoader(
    train_dataset,
    batch_size=4, # 每卡 4 条 (显存极度安全)
    sampler=sampler,
    collate_fn=collate_fn,
    num_workers=0
)

log_print(f'正在装载 DeepSeek-R1-7B 基础底座 (开启 Gradient Checkpointing)...')
base_model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR,
    torch_dtype=torch.float16,
    trust_remote_code=True
).to(device)
base_model.gradient_checkpointing_enable()
base_model.enable_input_require_grads()

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
    model = PeftModel.from_pretrained(base_model, latest_ckpt_path, is_trainable=True)
    initial_step = latest_step
else:
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj']
    )
    model = get_peft_model(base_model, peft_config)
    initial_step = 0

trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
log_print(f'✓ LoRA 挂载就绪！可训练参数: {trainable_params / 1e6:.2f} M')

if world_size > 1:
    model = DDP(model, device_ids=[local_rank], output_device=local_rank)

# Stage 2 采用平滑精调学习率 (8e-5) 避免震荡，深度强化思维链反思
optimizer = torch.optim.AdamW(
    [p for p in model.parameters() if p.requires_grad],
    lr=8e-5,
    weight_decay=0.01
)

log_print(f'🚀 【Stage 2 巅峰炼丹】DeepSeek-R1-7B 双卡满血轰鸣！(起点: Step {initial_step})')
model.train()
step = initial_step
accum_steps = 4 # 2卡 * 4 * 4 = 32 等效批次

for epoch in range(5):
    if sampler:
        sampler.set_epoch(epoch)
    for batch_idx, batch in enumerate(dataloader):
        t_step_start = time.time()
        outputs = model(**batch)
        loss = outputs.loss / accum_steps
        loss.backward()

        if (batch_idx + 1) % accum_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            optimizer.zero_grad()
            step += 1

            if step % 5 == 0 and local_rank == 0:
                dt = time.time() - t_step_start
                vram = torch.cuda.memory_allocated(0) / (1024**3)
                log_print(f'👑 [1号机 7B Stage2 | Step {step}] Loss: {loss.item()*accum_steps:.4f} | 单步: {dt:.2f}s | 显存: {vram:.1f}GB / 64GB | 已吞噬: {step*32} 局')

            if step % 100 == 0 and local_rank == 0:
                save_path = os.path.join(OUTPUT_DIR, f'checkpoint-{step}')
                log_print(f'💾 保存 Checkpoint-{step} 到 {save_path} ...')
                if hasattr(model, 'module'):
                    model.module.save_pretrained(save_path)
                else:
                    model.save_pretrained(save_path)
                tokenizer.save_pretrained(save_path)

if dist.is_initialized():
    dist.destroy_process_group()
