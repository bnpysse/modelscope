#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ModelScope 官方金融与基座大模型极速下载引擎
1. 采用 ModelScope 专线高速内网 CDN 协议下载模型权重
2. 自动保存至持久化存储 /mnt/workspace/models/
3. 支持断点续传与完整性校验
"""

import os
import sys
import time
from pathlib import Path

MODEL_DIR = Path("/mnt/workspace/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

from modelscope import snapshot_download


def download_target_model(model_id: str, local_name: str):
    print("================================================================================")
    print(f"📥 [大模型下载启动] 模型: {model_id} ➔ 目标路径: {MODEL_DIR / local_name}")
    print("================================================================================")
    
    t0 = time.time()
    try:
        path = snapshot_download(
            model_id=model_id,
            cache_dir=str(MODEL_DIR),
            revision="master"
        )
        elapsed = round(time.time() - t0, 1)
        print("================================================================================")
        print(f"🎉 模型 [{model_id}] 下载完成！总耗时: {elapsed} 秒")
        print(f"📁 本地持久化路径: {path}")
        print("================================================================================")
        return path
    except Exception as e:
        print(f"❌ 下载失败 [{model_id}]: {e}")
        return None


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "Qwen/Qwen2.5-7B-Instruct"
    name = sys.argv[2] if len(sys.argv) > 2 else "Qwen2.5-7B-Instruct"
    download_target_model(target, name)
