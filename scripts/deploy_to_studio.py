#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维量化战术超脑 · ModelScope 创空间 (Studio) 一键全自动资产同步枢纽
将本地 Streamlit 全息超脑、四大前沿数学试验台、核心算法、依赖一键直推至:
【bnpysse/Tianyan-HUD】
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
    print("================================================================================")
    print(f"🚀 [创空间一键同步] 正在将天衍全息作战超脑及前沿试验台直推至: {STUDIO_ID} ...")
    print("================================================================================")
    
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

    # 2. 递归同步 core 核心算法目录 (含全新 advanced_physics_pde.py)
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

    # 3. 同步全新 pages 试验台页面
    pages_dir = ROOT_DIR / "pages"
    if pages_dir.exists():
        for page_file in pages_dir.glob("*.py"):
            rel_path = page_file.relative_to(ROOT_DIR).as_posix()
            print(f"⬆️ 上传前沿试验台页面: {rel_path}")
            try:
                api.upload_file(
                    path_or_fileobj=str(page_file),
                    path_in_repo=rel_path,
                    repo_id=STUDIO_ID,
                    repo_type="studio",
                    commit_message=f"Deploy {rel_path}"
                )
                print(f"   ✅ {rel_path} 同步成功")
            except Exception as e:
                print(f"   ⚠️ {rel_path} 上传提示: {e}")

    # 4. 同步 data 股票列表基础底座
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

    print("\n================================================================================")
    print(f"🎉 [文件同步完毕] 天衍五维核心代码与全新前沿试验台已全部上传至创空间仓库！")
    print(f"🌐 创空间控制台: https://www.modelscope.cn/studios/{STUDIO_ID}")
    print(f"👉 统帅只需进入创空间管理页面，点击【重启】或【构建部署】即可瞬间生效！")
    print("================================================================================")


if __name__ == "__main__":
    deploy_studio()
