#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户偏好持久化模块 (User Preference Persistence)
保证用户在前端所选的【数据源基座】、【默认分组】等配置，无论如何强刷页面 (F5 / Cmd+R) 都 100% 稳固保留！
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

PREF_FILE = Path(__file__).resolve().parent.parent / "data" / "user_preference.json"


def get_user_preference() -> Dict[str, Any]:
    defaults = {
        "data_source_mode": "compass_ocr",  # compass_ocr | duckdb
        "selected_group": "🎯 指南针实盘真值持仓组",
        "selected_days": 55,
    }
    if PREF_FILE.exists():
        try:
            with open(PREF_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults


def save_user_preference(key: str, value: Any) -> None:
    PREF_FILE.parent.mkdir(parents=True, exist_ok=True)
    prefs = get_user_preference()
    prefs[key] = value
    try:
        with open(PREF_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
