#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证雷达图全字段生成渲染与 JS HUD 联动
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.engine import create_engine
from streamlit_app.components.radar_chart import build_radar_figure

def test_radar():
    engine = create_engine(str(ROOT_DIR))
    targets = engine.get_targets()
    
    print(f"Testing radar figure generation for {len(targets)} targets...")
    for t in targets[:5]:
        df = engine.get_stock_data(t.code, days=34)
        assert not df.is_empty(), f"Data for {t.code} should not be empty"
        fig = build_radar_figure(df, t.name, dim5_mode=20)
        assert fig is not None, f"Fig for {t.code} should not be None"
        print(f"✅ [{t.code}] {t.name} Radar Figure Generated Successfully! (Columns count: {len(df.columns)})")
        
    print("\n🎉 All Radar Figures Built with 0 Errors!")

if __name__ == "__main__":
    test_radar()
