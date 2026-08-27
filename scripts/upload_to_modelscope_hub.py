#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维量化 · ModelScope 私有资产一键同步枢纽
1. 将 /mnt/workspace/quant_data/ 全量五维因子库同步至 ModelScope 私有数据集 【bnpysse/Tianyan-Data】
2. 将量化核心代码与微调权重同步至 ModelScope 私有模型 【bnpysse/Tianyan】
3. 支持云端 PAI-DSW 与本地 Mac 双向极速同步
"""

import os
import sys
from pathlib import Path

# 适配云端或本地环境
if os.path.exists("/mnt/workspace"):
    WORKSPACE_DIR = Path("/mnt/workspace")
else:
    WORKSPACE_DIR = Path(__file__).resolve().parent.parent

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

api_token = os.getenv("MODELSCOPE_API_KEY", "")
DATASET_ID = os.getenv("MODELSCOPE_DATASET_ID", "bnpysse/Tianyan-Data")
MODEL_ID = os.getenv("MODELSCOPE_MODEL_ID", "bnpysse/Tianyan")


def get_hub_api():
    try:
        from modelscope.hub.api import HubApi
        api = HubApi()
        if api_token:
            api.login(api_token)
        return api
    except ImportError:
        print("❌ 未检测到 modelscope SDK，请运行: pip install modelscope")
        sys.exit(1)


def sync_private_dataset(dataset_name: str = DATASET_ID):
    """创建并推送全市场五维因子私有数据集 (bnpysse/Tianyan-Data)"""
    print(f"📦 [私有数据集同步] 目标仓库: {dataset_name} (Private)...")
    api = get_hub_api()
    data_dir = WORKSPACE_DIR / "quant_data"

    if not data_dir.exists():
        print(f"⚠️ 数据目录 {data_dir} 不存在，跳过上传。")
        return

    print(f"🚀 正在上传量化因子库与行情快照至数据集...")
    
    # 优先上传汇总表与重要快照
    priority_files = [
        "latest_factor_snapshot.parquet",
        "latest_factor_snapshot.json",
        "full_market_snapshot.parquet",
        "omni_finllm_sft_train.jsonl"
    ]
    
    for filename in priority_files:
        f_path = data_dir / filename
        if f_path.exists():
            size_mb = round(f_path.stat().st_size / 1024 / 1024, 2)
            print(f"   ⬆️ [快照] 上传: {filename} ({size_mb} MB)")
            try:
                api.upload_file(
                    path_or_fileobj=str(f_path),
                    path_in_repo=filename,
                    repo_id=dataset_name,
                    repo_type="dataset",
                    commit_message=f"Update snapshot {filename}"
                )
                print(f"      ✅ {filename} 上传成功")
            except Exception as ex:
                print(f"      ⚠️ 上传提示: {ex}")

    # 上传 factors/ 子目录下的各股票高精因子
    factors_dir = data_dir / "factors"
    if factors_dir.exists():
        factor_files = list(factors_dir.glob("*.parquet"))
        print(f"   📊 发现 {len(factor_files)} 个单标的高精因子文件，正在同步...")
        for f in factor_files:
            try:
                api.upload_file(
                    path_or_fileobj=str(f),
                    path_in_repo=f"factors/{f.name}",
                    repo_id=dataset_name,
                    repo_type="dataset",
                    commit_message=f"Sync factor {f.name}"
                )
            except Exception as ex:
                print(f"      ⚠️ {f.name} 上传提示: {ex}")

    print(f"\n🎉 数据集 [{dataset_name}] 同步完毕！")


def sync_private_model(model_name: str = MODEL_ID):
    """推送量化模型/代码与微调权重至私有模型仓库 (bnpysse/Tianyan)"""
    print(f"\n🧠 [私有模型同步] 目标仓库: {model_name} (Private)...")
    api = get_hub_api()

    # 1. 同步 README 与核心架构配置
    readme_path = ROOT_DIR / "README.md"
    if readme_path.exists():
        try:
            print(f"   ⬆️ 同步模型卡片 README.md...")
            api.upload_file(
                path_or_fileobj=str(readme_path),
                path_in_repo="README.md",
                repo_id=model_name,
                repo_type="model",
                commit_message="Update ModelCard with Tianyan V7 architecture"
            )
            print("      ✅ README.md 上传成功")
        except Exception as ex:
            print(f"      ⚠️ README 上传提示: {ex}")

    # 2. 如果存在微调 LoRA 权重，则上传 LoRA 目录
    model_dir = WORKSPACE_DIR / "models" / "omni-tactical-finllm-13b-lora"
    if model_dir.exists():
        print(f"🚀 正在上传 LoRA 适配器权重...")
        try:
            api.upload_folder(
                repo_id=model_name,
                folder_path=str(model_dir),
                repo_type="model",
                commit_message="Upload LoRA finetuned weights"
            )
            print("🎉 LoRA 权重同步完毕！")
        except Exception as ex:
            print(f"      ⚠️ 上传提示: {ex}")


def download_private_dataset(dataset_name: str = DATASET_ID, target_dir: Path = WORKSPACE_DIR / "quant_data"):

    """从 ModelScope 私有数据集仓库拉取最新因子数据与快照到本地/云端"""
    print(f"\n📥 [私有数据集拉取] 正在从 {dataset_name} 下载最新数据...")
    from modelscope.hub.snapshot_download import dataset_snapshot_download
    get_hub_api()
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        download_path = dataset_snapshot_download(
            dataset_id=dataset_name,
            local_dir=str(target_dir),
            revision="master"
        )
        print(f"🎉 数据集拉取成功！已保存至: {download_path}")
    except Exception as e:
        print(f"⚠️ 数据集拉取失败: {e}")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "all"
    if action in ["all", "dataset", "upload_dataset"]:
        sync_private_dataset()
    if action in ["all", "model", "upload_model"]:
        sync_private_model()
    if action in ["pull", "download", "download_dataset"]:
        download_private_dataset()

