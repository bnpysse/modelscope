"""
天衍五维量化战术超脑 · ModelScope 创空间 Streamlit 主入口
"""
import sys
from pathlib import Path

ROOT_DIR = str(Path(__file__).resolve().parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入并执行 Streamlit 主界面
from streamlit_app import app

