#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维量化 · 专属金融大模型集群全自动下载与管理引擎
专门下载 A 股量化与金融垂直领域的代表性大模型权重：
1. 【度小满/清华】XuanYuan-13B-Chat (轩辕中文金融千亿级开源大模型 13B版)
2. 【度小满】XuanYuan-FinX1-Preview (轩辕金融深度推理与归因模型)
3. 【阿里/通义】Qwen2.5-14B-Instruct (通义量化与金融结构化因子抽取基座)
4. 【清华】FinGLM (中文金融推理与财务穿透大模型)
"""

import os
import sys
import time
from pathlib import Path

# 自动适配云端 /mnt/workspace 或本地目录
if os.path.exists("/mnt/workspace"):
    WORKSPACE_DIR = Path("/mnt/workspace")
else:
    WORKSPACE_DIR = Path(__file__).resolve().parent.parent

MODELS_DIR = WORKSPACE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

from modelscope import snapshot_download


FIN_MODEL_REGISTRY = [
    {
        "id": "Duxiaoman-DI/XuanYuan-13B-Chat",
        "name": "轩辕-13B金融大模型 (度小满/清华联合开发)",
        "desc": "中文金融量化旗舰，专攻宏观政策、行业周期、主力偏好与战术决策",
        "size": "~26 GB",
    },
    {
        "id": "Duxiaoman-DI/XuanYuan-FinX1-Preview",
        "name": "轩辕-FinX1金融深度推理模型",
        "desc": "强化研报逻辑链穿透与金融微积分归因",
        "size": "~14 GB",
    },
    {
        "id": "Qwen/Qwen2.5-14B-Instruct",
        "name": "通义千问-14B金融基座与量化因子抽取模型",
        "desc": "阿里开源旗舰，融合金融语言基准，微调 Fin-Qwen 核心基座",
        "size": "~28 GB",
    },
    {
        "id": "finglm/FinGLM",
        "name": "清华 FinGLM 财务逻辑分析模型",
        "desc": "专攻财报财务指标、审计穿透与资产负债表异常分析",
        "size": "~12 GB",
    }
]


def download_all_financial_models():
    print("================================================================================")
    print("🏛️ [天衍金融大模型集群] ModelScope 专线高速下载引擎启动")
    print(f"📁 目标存储路径: {MODELS_DIR} (持久化 NAS，机器休眠无损)")
    print(f"📦 计划下载金融大模型: {len(FIN_MODEL_REGISTRY)} 款")
    print("================================================================================")

    for idx, item in enumerate(FIN_MODEL_REGISTRY, start=1):
        m_id = item["id"]
        m_name = item["name"]
        print(f"\n📥 [{idx}/{len(FIN_MODEL_REGISTRY)}] 正在高速拉取: {m_name}")
        print(f"   模型 ID: {m_id} | 预估体积: {item['size']} | 特色: {item['desc']}")
        
        t0 = time.time()
        try:
            local_path = snapshot_download(
                model_id=m_id,
                cache_dir=str(MODELS_DIR),
                revision="master"
            )
            elapsed = round(time.time() - t0, 1)
            print(f"   🎉 【下载成功】{m_id} 落盘完成！耗时: {elapsed}s")
            print(f"   📁 存储绝对路径: {local_path}")
        except Exception as e:
            print(f"   ⚠️ 【下载异常】{m_id} 错误: {e}")

    print("\n================================================================================")
    print("✅ 全部金融大模型下载流程执行完毕！")
    print("================================================================================")


if __name__ == "__main__":
    download_all_financial_models()
