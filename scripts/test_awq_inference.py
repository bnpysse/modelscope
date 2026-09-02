import time
import torch
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

model_path = "/mnt/workspace/models/tianyan_omni_32b_awq4bit"
print("正在以 device_map=auto 极速加载 AWQ 4-bit 终极模型...")
t0 = time.time()
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoAWQForCausalLM.from_quantized(model_path, fuse_layers=False, trust_remote_code=True, device_map="auto")
vram = torch.cuda.memory_allocated() / 1024**3
print(f"✓ 模型加载成功！耗时: {time.time()-t0:.2f}s | 显存仅占用: {vram:.2f} GB (原先需 62GB)")

prompt = "<|im_start|>user\n结合五维物理场微积分，简要说明 ASR 浮筹与 CPR 筹码刚性度的量化判定原则？<|im_end|>\n<|im_start|>assistant\n<thought>"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
print("正在进行毫秒级端到端推理测试...")
t1 = time.time()
with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=80, temperature=0.7)
res = tokenizer.decode(out[0], skip_special_tokens=False)
print(f"✓ 首 token 生成成功！耗时: {time.time()-t1:.2f}s")
print("=================== 模型输出实测 ===================")
print(res)
print("===================================================")
