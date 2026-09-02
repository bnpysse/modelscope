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
from peft import LoraConfig, get_peft_model, PeftModel, TaskType
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, default="qwen7b", choices=["qwen7b", "xuanyuan13b", "finglm"])
parser.add_argument("--resume", action="store_true", help="从最新 Checkpoint 恢复继续训练")
parser.add_argument("--batch_size", type=int, default=1, help="单步 Batch Size (24G 显卡推荐 1, 192G 显卡推荐 4~8)")
parser.add_argument("--grad_accum", type=int, default=16, help="梯度累积步数 (保证有效 batch size 恒定为 16)")
args = parser.parse_args()

WORKSPACE = Path("/mnt/workspace")
ROOT_OUT = Path("/root/train_output")
ROOT_LOGS = Path("/root/quant_data")
ROOT_OUT.mkdir(parents=True, exist_ok=True)
ROOT_LOGS.mkdir(parents=True, exist_ok=True)

if args.model == "xuanyuan13b":
    MODEL_DIR = str(WORKSPACE / "models" / "models" / "Duxiaoman-DI--XuanYuan-13B-Chat" / "snapshots" / "master")
    OUTPUT_DIR = ROOT_OUT / "omni-tactical-xuanyuan13b-lora"
    model_name = "度小满轩辕-13B"
    LOG_FILE = ROOT_LOGS / "xuanyuan13b_gpu_training_progress.log"
elif args.model == "finglm":
    MODEL_DIR = str(WORKSPACE / "models" / "models" / "finglm--FinGLM" / "snapshots" / "master")
    OUTPUT_DIR = ROOT_OUT / "omni-tactical-finglm-lora"
    model_name = "清华 FinGLM-6B"
    LOG_FILE = ROOT_LOGS / "finglm_gpu_training_progress.log"
else:
    MODEL_DIR = str(WORKSPACE / "models" / "models" / "Qwen--Qwen2.5-7B-Instruct" / "snapshots" / "master")
    OUTPUT_DIR = ROOT_OUT / "omni-tactical-qwen7b-lora"
    model_name = "Qwen2.5-7B-Instruct"
    LOG_FILE = ROOT_LOGS / "qwen7b_gpu_training_progress.log"

DATA_FILE = WORKSPACE / "quant_data" / "omni_finllm_sft_train.jsonl"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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

# 1. 检查 GPU 状态与硬件类型
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3) if torch.cuda.is_available() else 0
gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
log_print("================================================================================")
log_print(f"🚀 [天衍五维量化超脑] GPU 算力引擎 · {model_name} 强化微调开跑")
log_print(f"🔥 GPU 硬件就绪: {gpu_name} (显存总容量 {vram_gb:.2f} GB, bfloat16 极速模式)")
log_print("================================================================================")
log_print(f"🎯 基座模型: {MODEL_DIR}")
log_print(f"📊 训练样本: {DATA_FILE}")
log_print(f"💾 高速输出: {OUTPUT_DIR}")

# 2. 载入 Tokenizer
log_print("⏳ 正在载入 Tokenizer 与词表...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 3. 载入模型推入 显存
log_print(f"⏳ 正在将 {model_name} 推入显存 (bfloat16)...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR,
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",
    trust_remote_code=True
)

# 4. 跨实例 Checkpoint 恢复与续训检查
start_step = 0
latest_ckpt = None

# 如果本地 /root 目录为空，尝试从持久化 NAS /mnt/workspace 恢复
perm_model_dir = WORKSPACE / "models" / OUTPUT_DIR.name
if (not list(OUTPUT_DIR.glob("checkpoint-*"))) and perm_model_dir.exists():
    perm_ckpts = sorted(
        [p for p in perm_model_dir.glob("checkpoint-*") if p.is_dir()],
        key=lambda p: int(p.name.split("-")[1]) if p.name.split("-")[1].isdigit() else 0
    )
    if perm_ckpts:
        best_p_ckpt = perm_ckpts[-1]
        local_target = OUTPUT_DIR / best_p_ckpt.name
        log_print(f"📦 [跨实例迁移] 检测到持久化网盘存档: {best_p_ckpt.name}，正在同步至高速 NVMe...")
        shutil.copytree(best_p_ckpt, local_target, dirs_exist_ok=True)

if args.resume or list(OUTPUT_DIR.glob("checkpoint-*")):
    ckpts = sorted(
        [p for p in OUTPUT_DIR.glob("checkpoint-*") if p.is_dir()],
        key=lambda p: int(p.name.split("-")[1]) if p.name.split("-")[1].isdigit() else 0
    )
    if ckpts:
        latest_ckpt = ckpts[-1]
        start_step = int(latest_ckpt.name.split("-")[1])
        log_print(f"🔄 检测到已有成果存档: {latest_ckpt.name}，正在无缝加载继续冲刺 (起始 Step {start_step})！")

if latest_ckpt:
    model = PeftModel.from_pretrained(model, str(latest_ckpt), is_trainable=True)
else:
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=64,
        lora_alpha=128,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )
    model = get_peft_model(model, lora_config)

# 显存极致优化: 启用梯度检查点 (Gradient Checkpointing)
if hasattr(model, "enable_input_require_grads"):
    model.enable_input_require_grads()
model.gradient_checkpointing_enable()

model.print_trainable_parameters()

# 5. 数据集解析 (动态批次填充 collate_fn 极大节省显存并提升吞吐)
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

dataset = FinDataset(DATA_FILE, max_len=1024)
batch_size = args.batch_size
grad_accum_steps = args.grad_accum
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, collate_fn=pad_collate_fn)

# 6. 优化器与训练循环 (高并发 GPU 吞吐)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
total_steps = len(dataloader) // grad_accum_steps * 3

log_print(f"🔥 GPU 训练开跑！Batch Size: {batch_size}, 梯度累积: {grad_accum_steps}, 动态填充模式, 目标总 Step: {total_steps}")

step = start_step
accum_loss = 0.0
start_time = time.time()
step_start_time = time.time()

model.train()
torch.cuda.empty_cache()

for epoch in range(3):
    log_print(f"📢 === 开始 Epoch {epoch+1}/3 ===")
    
    # 极速断点续训: 仅在 Epoch 0 且存在历史存档时跳过对应样本量，无需逐条消耗 CPU
    if epoch == 0 and start_step > 0:
        start_sample_idx = min(start_step * grad_accum_steps * batch_size, len(dataset))
        if start_sample_idx < len(dataset):
            log_print(f"⏩ [秒级断点恢复] 跳过前 {start_sample_idx} 条样本，直接从 Step {start_step} 开始 GPU 计算！")
            epoch_indices = list(range(start_sample_idx, len(dataset)))
            epoch_sampler = torch.utils.data.SubsetRandomSampler(epoch_indices)
            epoch_dataloader = DataLoader(dataset, batch_size=batch_size, sampler=epoch_sampler, collate_fn=pad_collate_fn)
        else:
            epoch_dataloader = dataloader
    else:
        epoch_dataloader = dataloader

    for batch_idx, batch in enumerate(epoch_dataloader):
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
            avg_step_time = total_elapsed / max(step - start_step, 1)
            eta_mins = (total_steps - step) * avg_step_time / 60
            vram_used = torch.cuda.memory_allocated(0) / (1024**3) if torch.cuda.is_available() else 0
            
            log_print(f"⚡ [Epoch {epoch+1} | Step {step}/{total_steps}] Loss: {current_loss:.4f} | 单步: {step_time:.2f}s | 显存: {vram_used:.1f}GB / {vram_gb:.0f}GB | 题解: {samples_seen} | 预计剩余: {eta_mins:.1f}分钟")
            accum_loss = 0.0

            if step % 50 == 0 or step == total_steps:
                ckpt_dir = OUTPUT_DIR / f"checkpoint-{step}"
                log_print(f"💾 [阶段成果落盘] 正在将 {model_name} LoRA 权重保存至: {ckpt_dir} ...")
                model.save_pretrained(ckpt_dir)
                tokenizer.save_pretrained(ckpt_dir)
                log_print(f"🎉 ✅ Checkpoint-{step} 权重已成功落盘！")
                
                # 自动清理：保留最新 2 个 checkpoint，彻底杜绝磁盘超限
                try:
                    all_ckpts = sorted(
                        [p for p in OUTPUT_DIR.glob("checkpoint-*") if p.is_dir()],
                        key=lambda p: int(p.name.split("-")[1]) if p.name.split("-")[1].isdigit() else 0
                    )
                    if len(all_ckpts) > 2:
                        for old_ckpt in all_ckpts[:-2]:
                            shutil.rmtree(old_ckpt, ignore_errors=True)
                            log_print(f"🧹 [自动瘦身] 已修剪旧存档: {old_ckpt.name}，释放磁盘空间！")
                except Exception as e:
                    pass

                # 自动镜像最新 Checkpoint 至持久化盘 /mnt/workspace/models (防关机双重保险)
                try:
                    perm_parent = WORKSPACE / "models" / OUTPUT_DIR.name
                    perm_parent.mkdir(parents=True, exist_ok=True)
                    perm_ckpt = perm_parent / f"checkpoint-{step}"
                    if not perm_ckpt.exists():
                        shutil.copytree(ckpt_dir, perm_ckpt)
                    perm_ckpts = sorted(
                        [p for p in perm_parent.glob("checkpoint-*") if p.is_dir()],
                        key=lambda p: int(p.name.split("-")[1]) if p.name.split("-")[1].isdigit() else 0
                    )
                    if len(perm_ckpts) > 2:
                        for p_old in perm_ckpts[:-2]:
                            shutil.rmtree(p_old, ignore_errors=True)
                    log_print(f"🛡️ [双保险] Checkpoint-{step} 已实时同步持久化盘，关机零丢失！")
                except Exception as e:
                    pass

log_print(f"🎉 [训练圆满完成] 最终 {model_name} LoRA 适配器权重已全部就绪！")
model.save_pretrained(OUTPUT_DIR / "final_adapter")
tokenizer.save_pretrained(OUTPUT_DIR / "final_adapter")

