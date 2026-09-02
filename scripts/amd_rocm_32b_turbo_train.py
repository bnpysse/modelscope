# -*- coding: utf-8 -*-
"""
天衍五维量化大模型 - ModelScope AMD GPU (192GB 超大显存 / ROCm)
🔥 Qwen2.5-32B-Instruct 全息物理微积分终极对齐训练引擎 🔥
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

LOCAL_CANDIDATES = [
    "/mnt/workspace/models/models/Qwen--Qwen2.5-32B-Instruct/snapshots/master",
    "/mnt/workspace/models/models/Qwen--Qwen2.5-32B-Instruct",
    "/mnt/workspace/models/Qwen--Qwen2.5-32B-Instruct",
    "Qwen/Qwen2.5-32B-Instruct"
]
MODEL_NAME_OR_PATH = next((p for p in LOCAL_CANDIDATES if os.path.exists(p)), "Qwen/Qwen2.5-32B-Instruct")
DATA_FILE = "/mnt/workspace/quant_data/omni_finllm_sft_v2.jsonl"
OUTPUT_DIR = "/mnt/workspace/models/omni-qwen2.5-32b-rocm-lora"
LOG_FILE = "/mnt/workspace/training_32b_rocm.log"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_print(msg):
    t = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{t} {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()

log_print("========================================================================================")
log_print("🔥【ModelScope AMD GPU 192GB 巨无霸显存】Qwen2.5-32B 终极对齐训练引擎点火！")
log_print(f"• 模型加载源: {MODEL_NAME_OR_PATH}")
log_print("========================================================================================")

# 1. 加载分词器
log_print(f"正在从本地装载分词器: {MODEL_NAME_OR_PATH} ...")
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME_OR_PATH, 
    trust_remote_code=True,
    local_files_only=os.path.exists(MODEL_NAME_OR_PATH)
)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 2. 统计样本数
def count_lines(fname):
    with open(fname, "r", encoding="utf-8") as f:
        for i, _ in enumerate(f):
            pass
    return i + 1

total_samples = count_lines(DATA_FILE)
log_print(f"✓ 数据集索引就绪！总样本数: {total_samples} 局")

# 3. 极速内存流式数据集
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
            messages = data.get("messages", [])
            if not messages:
                return [tokenizer.eos_token_id]
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            enc = tokenizer(text, max_length=2048, truncation=True, padding=False)
            return enc["input_ids"]
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
        "input_ids": torch.tensor(input_ids_batch, dtype=torch.long),
        "labels": torch.tensor(labels_batch, dtype=torch.long),
        "attention_mask": torch.tensor(attention_mask_batch, dtype=torch.long)
    }

train_dataset = LazyJSONLDataset(DATA_FILE, total_samples)
train_loader = DataLoader(
    train_dataset,
    batch_size=12, # 192GB 满血显存调度，单卡开到 Batch Size 12 (显存约 165GB / 82% 饱和)!
    shuffle=True,
    collate_fn=collate_fn,
    num_workers=0, # 单进程免 IPC 极速内存读取
    pin_memory=True
)

# 4. 加载 32B 模型 (利用 192GB 显存，直接单卡装入 BF16/FP16，无需任何切片与 CPU 卸载！)
log_print(f"正在将 Qwen2.5-32B-Instruct 完整模型装入 192GB 显存 (源: {MODEL_NAME_OR_PATH})...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME_OR_PATH,
    torch_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
    device_map="cuda:0",
    trust_remote_code=True,
    local_files_only=os.path.exists(MODEL_NAME_OR_PATH)
)

model.gradient_checkpointing_enable()
model.enable_input_require_grads()

# 检查是否有历史 checkpoint
existing_ckpts = glob.glob(os.path.join(OUTPUT_DIR, "checkpoint-*"))
latest_step = 0
latest_ckpt_path = None
for p in existing_ckpts:
    try:
        s = int(os.path.basename(p).split("-")[1])
        if s > latest_step:
            latest_step = s
            latest_ckpt_path = p
    except:
        pass

if latest_ckpt_path and os.path.exists(latest_ckpt_path):
    log_print(f"💎 挂载历史 Checkpoint [{os.path.basename(latest_ckpt_path)}]，从 Step {latest_step} 续训！")
    model = PeftModel.from_pretrained(model, latest_ckpt_path, is_trainable=True)
    initial_step = latest_step
else:
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=32, # 192G 显存直接开 r=32 强化秩容量！
        lora_alpha=64,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )
    model = get_peft_model(model, peft_config)
    initial_step = 0

trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
log_print(f"✓ LoRA 挂载就绪！可训练参数: {trainable_params / 1e6:.2f} M")

optimizer = torch.optim.AdamW(
    [p for p in model.parameters() if p.requires_grad],
    lr=1e-4,
    weight_decay=0.01
)

vram = torch.cuda.memory_allocated(0) / (1024**3)
log_print(f"✓ 192GB 显存装载完成: 显存占用 {vram:.1f}GB / 192GB (余量极其充沛！)")
log_print(f"🚀 【192GB 满血开训】Qwen2.5-32B 终极炼丹正式起飞！")

model.train()
step = initial_step
accum_steps = 4 # 8 * 4 = 32 等效批次
optimizer.zero_grad()
t_step_start = time.time()

for epoch in range(5):
    for batch_idx, batch in enumerate(train_loader):
        batch = {k: v.to("cuda:0", non_blocking=True) for k, v in batch.items()}
        outputs = model(**batch)
        loss = outputs.loss / accum_steps
        loss.backward()

        if (batch_idx + 1) % accum_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            optimizer.zero_grad()
            step += 1

            if step % 5 == 0:
                dt = (time.time() - t_step_start) / 5
                vram = torch.cuda.memory_allocated(0) / (1024**3)
                log_print(f"👑 [ModelScope 32B ROCm | Step {step}] Loss: {outputs.loss.item():.4f} | 单步: {dt:.2f}s | 显存: {vram:.1f}G/192G | 已吞噬: {step*32} 局")
                t_step_start = time.time()

            if step % 50 == 0:
                save_path = os.path.join(OUTPUT_DIR, f"checkpoint-{step}")
                log_print(f"💾 保存 Checkpoint-{step} 到 {save_path} ...")
                model.save_pretrained(save_path)
                tokenizer.save_pretrained(save_path)
