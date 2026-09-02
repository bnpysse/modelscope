# -*- coding: utf-8 -*-
import torch
import os
import time
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE_MODEL = '/root/private_data/SothisAI/model/Aihub/Qwen3-Coder-30B-A3B-Instruct/main/Qwen3-Coder-30B-A3B-Instruct'
CKPT_DIR = '/root/private_data/models/omni-qwen3-coder-30b-lora/checkpoint-375'

print('1. 正在载入 Tokenizer...')
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)

print('2. 正在装载 Qwen3-Coder-30B 基础底座 (双卡流水线)...')
device_map = {
    'model.embed_tokens': 0,
    'model.norm': 1,
    'lm_head': 1,
}
for i in range(48):
    device_map[f'model.layers.{i}'] = 0 if i < 24 else 1

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    device_map=device_map,
    trust_remote_code=True
)

print(f'3. 正在无缝挂载天衍五维训练成果 Checkpoint: {CKPT_DIR} ...')
model = PeftModel.from_pretrained(base_model, CKPT_DIR)
model.eval()

# 实战推理测试 Prompt
test_prompt = """【当前研判标的实时物理真值情报】
- 标的: 香农芯创 (300475)
- 收盘价: 34.50 元, 换手率: 8.2%
- LFS=62.50, HCCYF13=48.20, ASR=12.30%
- Z获利比例=88.50%, X70=8.20%, X90=14.50%, Y重合度=25.00%
- CYF66_Raw / VMA(T+55): 68.50 / 52.10 (ΔCYF=+16.40)
- 主力净流入 Main%=12.50%, 游资 Dare%=1.20%, 活筹位置 D_pos=28.50
- 均线偏离 BIAS_5_20=+4.20%, CYS34=+6.50%

请结合连续微积分时空场与天衍战法，推演当前标的主力控盘意图、一票否决风控判定及 4 级动态仓位指令："""

messages = [
    {'role': 'system', 'content': '你是天眼参谋部首席量化专家与大模型战术推演大脑，基于天衍五维微积分时空场与筹码守恒反解给出确定性研判。'},
    {'role': 'user', 'content': test_prompt}
]

prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(prompt_text, return_tensors='pt').to(0)

print("\n🚀 开始执行 30B 战神大脑跨周期物理真值穿透推理...")
t0 = time.time()
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=400,
        temperature=0.2,
        top_p=0.9,
        do_sample=True
    )

gen_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
dt = time.time() - t0
print(f"✓ 推理完成！耗时: {dt:.2f} 秒\n")
print("="*80)
print(gen_text)
print("="*80)
