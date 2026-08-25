#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全标的物理截面与战术定性批量扫描测试
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.engine import create_engine
from core.ai_advisor import evaluate_local_tactical_status

def test_all():
    engine = create_engine(str(ROOT_DIR))
    targets = engine.get_targets()
    print(f"📊 加载全市场监控标的总数: {len(targets)}")

    for t in targets:
        snap = engine.get_latest_snapshot(t.code)
        fib = engine.get_fibonacci_depth_matrix(t.code)
        local_eval = evaluate_local_tactical_status(snap)
        close_val = snap.get("Close", 0.0)
        lfs_val = snap.get("LFS", 0.0)
        scissor_val = snap.get("Scissor", 0.0)
        order_val = local_eval["order"]
        status_val = local_eval["status_title"]
        print(f"  [{t.code}] {t.name:<6} -> 现价: {close_val:<6} | LFS: {lfs_val:<6} | 剪刀差: {scissor_val:<6.2f} | 纵深周期: {len(fib)} | 裁决: {order_val} ({status_val})")

if __name__ == "__main__":
    test_all()
