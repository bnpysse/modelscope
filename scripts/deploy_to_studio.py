#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维量化战术超脑 · ModelScope 创空间 (Studio) 一键全自动部署枢纽
将本地 Streamlit 全息 HUD、核心算法、五维因子与依赖一键同步至 【bnpysse/Tianyan-HUD】
"""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

api_token = os.getenv("MODELSCOPE_API_KEY", "")
STUDIO_ID = "bnpysse/Tianyan-HUD"


def get_hub_api():
    from modelscope.hub.api import HubApi
    api = HubApi()
    if api_token:
        api.login(api_token)
    return api


def deploy_studio():
    print(f"================================================================================")
    print(f"🚀 [创空间一键部署] 正在将天衍五维 Streamlit 全息大屏部署至: {STUDIO_ID} ...")
    print(f"================================================================================")
    
    api = get_hub_api()
    
    # 1. 核心根目录文件
    root_files = [
        "app.py",
        "requirements.txt",
        "README.md",
        ".env"
    ]
    
    for rf in root_files:
        f_path = ROOT_DIR / rf
        if f_path.exists():
            print(f"⬆️ 上传根目录配置: {rf}")
            try:
                api.upload_file(
                    path_or_fileobj=str(f_path),
                    path_in_repo=rf,
                    repo_id=STUDIO_ID,
                    repo_type="studio",
                    commit_message=f"Deploy {rf} to studio"
                )
                print(f"   ✅ {rf} 同步成功")
            except Exception as e:
                print(f"   ⚠️ {rf} 上传提示: {e}")

    # 2. 递归同步 core 算法目录
    core_dir = ROOT_DIR / "core"
    if core_dir.exists():
        for py_file in core_dir.rglob("*.py"):
            rel_path = py_file.relative_to(ROOT_DIR).as_posix()
            print(f"⬆️ 上传算法模块: {rel_path}")
            try:
                api.upload_file(
                    path_or_fileobj=str(py_file),
                    path_in_repo=rel_path,
                    repo_id=STUDIO_ID,
                    repo_type="studio",
                    commit_message=f"Deploy {rel_path}"
                )
            except Exception as e:
                print(f"   ⚠️ {rel_path} 上传提示: {e}")

    # 3. 递归同步 streamlit_app 组件与样式目录
    st_dir = ROOT_DIR / "streamlit_app"
    if st_dir.exists():
        for st_file in st_dir.rglob("*"):
            if st_file.is_file() and not st_file.name.startswith((".", "__pycache__")):
                rel_path = st_file.relative_to(ROOT_DIR).as_posix()
                print(f"⬆️ 上传前端组件: {rel_path}")
                try:
                    api.upload_file(
                        path_or_fileobj=str(st_file),
                        path_in_repo=rel_path,
                        repo_id=STUDIO_ID,
                        repo_type="studio",
                        commit_message=f"Deploy {rel_path}"
                    )
                except Exception as e:
                    print(f"   ⚠️ {rel_path} 上传提示: {e}")

    # 4. 同步 data 股票底座
    data_dir = ROOT_DIR / "data"
    if data_dir.exists():
        for d_file in data_dir.glob("*.csv"):
            rel_path = d_file.relative_to(ROOT_DIR).as_posix()
            print(f"⬆️ 上传数据资产: {rel_path}")
            try:
                api.upload_file(
                    path_or_fileobj=str(d_file),
                    path_in_repo=rel_path,
                    repo_id=STUDIO_ID,
                    repo_type="studio",
                    commit_message=f"Deploy {rel_path}"
                )
            except Exception as e:
                print(f"   ⚠️ {rel_path} 上传提示: {e}")

    # 5. 同步最新因子快照
    snapshot_file = ROOT_DIR / "quant_data" / "latest_factor_snapshot.parquet"
    if snapshot_file.exists():
        print(f"⬆️ 上传全市场因子快照...")
        try:
            api.upload_file(
                path_or_fileobj=str(snapshot_file),
                path_in_repo="quant_data/latest_factor_snapshot.parquet",
                repo_id=STUDIO_ID,
                repo_type="studio",
                commit_message="Deploy latest factor snapshot"
            )
            print("   ✅ 因子快照同步成功")
        except Exception as e:
            print(f"   ⚠️ 因子快照上传提示: {e}")

    # 6. 复制 6 款核心标的高精因子
    factors_dir = ROOT_DIR / "quant_data" / "factors"
    if factors_dir.exists():
        for factor_file in factors_dir.glob("*.parquet"):
            rel_path = factor_file.relative_to(ROOT_DIR).as_posix()
            print(f"⬆️ 上传核心标的因子: {rel_path}")
            try:
                api.upload_file(
                    path_or_fileobj=str(factor_file),
                    path_in_repo=rel_path,
                    repo_id=STUDIO_ID,
                    repo_type="studio",
                    commit_message=f"Deploy {rel_path}"
                )
            except Exception as e:
                print(f"   ⚠️ {rel_path} 上传提示: {e}")

    print("\n================================================================================")
    print(f"🎉 [部署完毕] 天衍五维创空间已全部同步完成！")
    print(f"🌐 访问地址: https://www.modelscope.cn/studios/{STUDIO_ID}")
    print("================================================================================")


if __name__ == "__main__":
    deploy_studio()
