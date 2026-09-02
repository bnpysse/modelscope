import torch
import gc
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

cases = [
    {
        "name": "Case 1: 真龙真空超导主升突破态 (香农芯创 300475)",
        "prompt": """【当前研判标的实时物理真值情报】
- 标的: 香农芯创 (300475)
- 收盘价: 162.16 元, 换手率: 8.5%
- LFS=88.5, HCCYF13=92.1, ASR=35.6%
- Z获利比例=96.0%, X70=5.98%, X90=8.12%, Y重合度=61.29%
- CYF66_Raw / VMA(T+55): 89.20 / 72.40 (ΔCYF=+16.80 极速扩张)
- 主力净流入 Main%=+0.810%, 游资 Dare%=+0.12%, 活筹位置 D_pos=34.42
- 均线偏离 BIAS_5_20=2.85%, CYS34=12.40%

请总参谋部穿透当前物理场，给出严密微积分推导与最终军令。"""
    },
    {
        "name": "Case 2: 假突破对倒诱多出货一票否决态 (典型高风险盘口)",
        "prompt": """【当前研判标的实时物理真值情报】
- 标的: 某高位妖股 (000XXX)
- 收盘价: 35.20 元, 换手率: 18.5% (高换手放量)
- LFS=42.0, HCCYF13=40.5, ASR=58.2% (上方套牢盘严重积压)
- Z获利比例=35.0%, X70=22.5%, X90=28.5%, Y重合度=32.1%
- CYF66_Raw / VMA(T+55): 42.0 / 58.0 (ΔCYF=-16.0 深度死叉发散)
- 主力净流入 Main%=-2.85% (机构大幅净流出), 游资 Dare%=+3.20% (游资虚假拉升), 活筹位置 D_pos=82.0 (高位派发)
- 均线偏离 BIAS_5_20=8.50%, CYS34=-6.80%

请总参谋部穿透当前物理场，给出严密微积分推导与最终军令。"""
    }
]

def eval_qwen7b():
    print("====================================================================")
    print("🎯 正在评测 Qwen2.5-7B (Checkpoint-6000, 9.6万题毕业权重)")
    print("====================================================================")
    base_dir = "/mnt/workspace/models/models/Qwen--Qwen2.5-7B-Instruct/snapshots/master"
    lora_dir = "/mnt/workspace/models/omni-tactical-qwen7b-lora/checkpoint-6000"
    
    tokenizer = AutoTokenizer.from_pretrained(base_dir, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_dir,
        torch_dtype=torch.bfloat16,
        device_map="cuda:0",
        trust_remote_code=True
    )
    model = PeftModel.from_pretrained(base_model, lora_dir)
    model.eval()

    for c in cases:
        print(f"\n🔥 【Qwen-7B 评测输出】 {c['name']}:")
        messages = [
            {"role": "system", "content": "你是天衍五维量化总参谋部专属大模型，精通五维时空微积分场论与三唯一终极军令。请结合物理真值给出推导与最终军令。"},
            {"role": "user", "content": c["prompt"]}
        ]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer([text], return_tensors="pt").to("cuda:0")
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=400,
                temperature=0.1,
                repetition_penalty=1.15,
                top_p=0.9
            )
        ans = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
        print(ans.strip())
    
    del model, base_model, tokenizer
    torch.cuda.empty_cache()
    gc.collect()

def eval_xuanyuan13b():
    print("\n====================================================================")
    print("🎯 正在评测 度小满 XuanYuan-13B (Checkpoint-2050, 3.2万题毕业权重)")
    print("====================================================================")
    base_dir = "/mnt/workspace/models/models/Duxiaoman-DI--XuanYuan-13B-Chat/snapshots/master"
    lora_dir = "/mnt/workspace/models/omni-tactical-xuanyuan13b-lora/checkpoint-2050"
    
    tokenizer = AutoTokenizer.from_pretrained(base_dir, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_dir,
        torch_dtype=torch.bfloat16,
        device_map="cuda:0",
        trust_remote_code=True
    )
    model = PeftModel.from_pretrained(base_model, lora_dir)
    model.eval()

    for c in cases:
        print(f"\n💼 【度小满-13B 评测输出】 {c['name']}:")
        messages = [
            {"role": "system", "content": "你是天衍五维量化总参谋部专属大模型，精通A股金融逻辑、五维时空微积分场论与三唯一终极军令。请给出深度推导与最终军令。"},
            {"role": "user", "content": c["prompt"]}
        ]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer([text], return_tensors="pt").to("cuda:0")
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=400,
                temperature=0.1,
                repetition_penalty=1.15,
                top_p=0.9
            )
        ans = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
        print(ans.strip())

    del model, base_model, tokenizer
    torch.cuda.empty_cache()
    gc.collect()

if __name__ == "__main__":
    eval_qwen7b()
    eval_xuanyuan13b()
