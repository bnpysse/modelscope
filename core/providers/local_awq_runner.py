# -*- coding: utf-8 -*-
"""
天衍五维量化大模型 - 本地 / 挂载卷 AWQ 4-bit 终极大模型极速单例推理引擎
"""
import os
import re
import time
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("LocalAWQRunner")

class LocalAWQRunner:
    """本地/挂载目录 AWQ 4-bit 终极模型推理执行器"""

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._loaded_path = None

    def _ensure_loaded(self, model_path: str):
        if self._model is not None and self._loaded_path == model_path:
            return

        import torch
        from transformers import AutoTokenizer
        from awq import AutoAWQForCausalLM

        # 默认寻找路径
        actual_path = model_path
        if not os.path.exists(actual_path):
            candidates = [
                "/mnt/workspace/models/tianyan_omni_32b_awq4bit",
                os.path.expanduser("~/dev/modelscope/models/tianyan_omni_32b_awq4bit"),
                "models/tianyan_omni_32b_awq4bit",
            ]
            for c in candidates:
                if os.path.exists(c):
                    actual_path = c
                    break

        if not os.path.exists(actual_path):
            raise FileNotFoundError(f"未找到 AWQ 模型路径: {model_path} (已检索各可能目录)")

        logger.info(f"正在挂载加载天衍 32B AWQ 4-bit 终极大模型: {actual_path} ...")
        self._tokenizer = AutoTokenizer.from_pretrained(actual_path, trust_remote_code=True)
        self._model = AutoAWQForCausalLM.from_quantized(
            actual_path,
            fuse_layers=False,
            trust_remote_code=True,
            device_map="auto"
        )
        self._loaded_path = model_path
        logger.info("✓ 天衍 32B AWQ 模型加载大圆满！")

    def _extract_thinking_and_content(self, text: str) -> Tuple[str, str]:
        """分离 <thought> 或 <think> 思维链与最终内容"""
        think_match = re.search(r"<(?:thought|think)>(.*?)</(?:thought|think)>", text, re.DOTALL)
        if think_match:
            thinking = think_match.group(1).strip()
            clean_content = re.sub(r"<(?:thought|think)>.*?</(?:thought|think)>", "", text, flags=re.DOTALL).strip()
            return thinking, clean_content
        return "", text.strip()

    def generate(
        self,
        messages: List[Dict[str, str]],
        model_path: str = "/mnt/workspace/models/tianyan_omni_32b_awq4bit",
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        """执行端到端量化推理"""
        import torch

        self._ensure_loaded(model_path)
        t0 = time.time()

        # 构建对话上下文 prompt
        prompt = ""
        for m in messages:
            role = m["role"]
            content = m["content"]
            prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
        prompt += "<|im_start|>assistant\n"

        inputs = self._tokenizer(prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                pad_token_id=self._tokenizer.eos_token_id
            )

        input_len = inputs["input_ids"].shape[1]
        generated_ids = outputs[0][input_len:]
        raw_output = self._tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

        duration = round(time.time() - t0, 2)
        thinking, content = self._extract_thinking_and_content(raw_output)

        return {
            "status": "success",
            "content": content if content else raw_output,
            "thinking": thinking,
            "raw_content": raw_output,
            "model": "👑 天衍 32B 终极工业量化模型 (AWQ 4-bit)",
            "duration_seconds": duration,
            "usage": {
                "prompt_tokens": input_len,
                "completion_tokens": len(generated_ids),
                "total_tokens": input_len + len(generated_ids)
            },
            "quota_status": {
                "date": "本地/独占挂载",
                "used_calls": "本地无限次",
                "limit_calls": 99999,
                "remaining_calls": 99999,
                "remaining_ratio": 1.0,
                "total_tokens": input_len + len(generated_ids),
                "is_safe": True
            }
        }

local_awq_runner = LocalAWQRunner()
