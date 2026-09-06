#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维 · 统帅个人战备观察池数据库管理器
专库专用: tianyan_watchlist.duckdb
彻底与全量 A 股物理特征底座 (tianyan_market.duckdb) 解耦，保护底层数据纯洁性
"""

import os
import duckdb
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class WatchlistManager:
    """统帅专属个人股票战备观察池管理器 (DuckDB 独立存储)"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            # 自动探测工作区路径
            if os.path.exists("/mnt/workspace"):
                base_dir = Path("/mnt/workspace/data")
            else:
                base_dir = Path(__file__).resolve().parent.parent / "data"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "tianyan_watchlist.duckdb"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self):
        return duckdb.connect(str(self.db_path))

    def _init_db(self):
        """初始化个人战备观察池数据表"""
        with self._get_connection() as con:
            # 1. 观察池分组表
            con.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_groups (
                group_name VARCHAR PRIMARY KEY,
                sort_order INTEGER DEFAULT 99,
                description VARCHAR DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. 自选观察池标的明细表
            con.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_stocks (
                code VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                group_name VARCHAR NOT NULL,
                cost_price DOUBLE DEFAULT 0.0,
                target_pos DOUBLE DEFAULT 50.0,
                notes VARCHAR DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, group_name)
            );
            """)

            # 3. 注入默认内置分组 (以统帅真实指南针持仓为尊)
            con.execute("""
            INSERT OR IGNORE INTO watchlist_groups (group_name, sort_order, description) VALUES
            ('🎯 指南针实盘真值持仓组', 1, '统帅每日实盘手工 OCR 真实仓位'),
            ('⚡ 天衍微分全景观察组', 2, '全息高阶张量重点观察标的'),
            ('🚀 斐波那契突破备选池', 3, '多周期共振奇点突破战备标的');
            """)

            # 4. 注入初始持仓标的 (德明利、易天股份、佰维存储、江波龙、香农芯创)
            init_stocks = [
                ("001309", "德明利", "🎯 指南针实盘真值持仓组", 0.0, 100.0, "核心实盘持仓"),
                ("301171", "易天股份", "🎯 指南针实盘真值持仓组", 0.0, 50.0, "核心实盘持仓"),
                ("688525", "佰维存储", "🎯 指南针实盘真值持仓组", 0.0, 50.0, "核心实盘持仓"),
                ("301308", "江波龙", "🎯 指南针实盘真值持仓组", 0.0, 50.0, "核心实盘持仓"),
                ("300475", "香农芯创", "🎯 指南针实盘真值持仓组", 0.0, 50.0, "核心实盘持仓"),
                ("300308", "中际旭创", "⚡ 天衍微分全景观察组", 0.0, 30.0, "光模块核心龙头"),
                ("300378", "鼎捷数智", "⚡ 天衍微分全景观察组", 0.0, 30.0, "工业软件龙头"),
                ("002885", "京泉华", "⚡ 天衍微分全景观察组", 0.0, 30.0, "高频磁性器件"),
            ]
            for c, n, g, cp, tp, nt in init_stocks:
                con.execute("""
                INSERT OR IGNORE INTO watchlist_stocks (code, name, group_name, cost_price, target_pos, notes)
                VALUES (?, ?, ?, ?, ?, ?);
                """, [c, n, g, cp, tp, nt])

    def get_all_groups(self) -> List[str]:
        """获取所有分组名称，按排序权重返回"""
        with self._get_connection() as con:
            res = con.execute("SELECT group_name FROM watchlist_groups ORDER BY sort_order ASC, created_at ASC;").fetchall()
            return [r[0] for r in res]

    def add_group(self, group_name: str, description: str = "") -> bool:
        """新建自选分组"""
        group_name = group_name.strip()
        if not group_name:
            return False
        with self._get_connection() as con:
            con.execute("""
            INSERT OR IGNORE INTO watchlist_groups (group_name, sort_order, description)
            VALUES (?, 50, ?);
            """, [group_name, description])
            return True

    def get_stocks_by_group(self, group_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取指定分组或全部分组下的标的列表"""
        with self._get_connection() as con:
            if group_name and group_name != "⭐ 全部标的池":
                res = con.execute("""
                SELECT code, name, group_name, cost_price, target_pos, notes, created_at
                FROM watchlist_stocks
                WHERE group_name = ?
                ORDER BY created_at ASC;
                """, [group_name]).fetchall()
            else:
                res = con.execute("""
                SELECT DISTINCT code, name, group_name, cost_price, target_pos, notes, created_at
                FROM watchlist_stocks
                ORDER BY created_at ASC;
                """).fetchall()

            return [
                {
                    "code": r[0],
                    "name": r[1],
                    "group_name": r[2],
                    "cost_price": r[3],
                    "target_pos": r[4],
                    "notes": r[5],
                    "created_at": str(r[6]),
                }
                for r in res
            ]

    def add_stock_to_group(self, code: str, name: str, group_name: str, cost_price: float = 0.0, target_pos: float = 50.0, notes: str = "") -> bool:
        """添加标的到指定观察池分组"""
        code = str(code).strip().zfill(6)
        name = str(name).strip() or f"标的{code}"
        group_name = str(group_name).strip()

        with self._get_connection() as con:
            # 确保分组存在
            con.execute("INSERT OR IGNORE INTO watchlist_groups (group_name, sort_order) VALUES (?, 50);", [group_name])
            con.execute("""
            INSERT OR REPLACE INTO watchlist_stocks (code, name, group_name, cost_price, target_pos, notes)
            VALUES (?, ?, ?, ?, ?, ?);
            """, [code, name, group_name, cost_price, target_pos, notes])
            return True

    def remove_stock_from_group(self, code: str, group_name: str) -> bool:
        """从分组中移除标的"""
        code = str(code).strip().zfill(6)
        with self._get_connection() as con:
            con.execute("DELETE FROM watchlist_stocks WHERE code = ? AND group_name = ?;", [code, group_name])
            return True

    def update_stock_name(self, code: str, group_name: str, new_name: str) -> bool:
        """更新标的名称"""
        code = str(code).strip().zfill(6)
        new_name = str(new_name).strip()
        if not new_name:
            return False
        with self._get_connection() as con:
            con.execute("UPDATE watchlist_stocks SET name = ? WHERE code = ? AND group_name = ?;", [new_name, code, group_name])
            return True

    def clear_group(self, group_name: str) -> bool:
        """清空指定分组内的所有标的"""
        with self._get_connection() as con:
            con.execute("DELETE FROM watchlist_stocks WHERE group_name = ?;", [group_name])
            return True

    def delete_group(self, group_name: str) -> bool:
        """彻底删除分组及其包含的所有标的"""
        with self._get_connection() as con:
            con.execute("DELETE FROM watchlist_stocks WHERE group_name = ?;", [group_name])
            con.execute("DELETE FROM watchlist_groups WHERE group_name = ?;", [group_name])
            return True

    def batch_add_stocks(self, stocks: List[Dict[str, str]], group_name: str) -> int:
        """批量导入标的到观察池 (如初筛雷达 Top 15 一键入池)"""
        count = 0
        for s in stocks:
            c = s.get("code", "")
            n = s.get("name", "")
            if c:
                self.add_stock_to_group(c, n, group_name)
                count += 1
        return count


# 全局单例工厂
_watchlist_instance: Optional[WatchlistManager] = None

def get_watchlist_manager(db_path: Optional[Path] = None) -> WatchlistManager:
    global _watchlist_instance
    if _watchlist_instance is None:
        _watchlist_instance = WatchlistManager(db_path)
    return _watchlist_instance
