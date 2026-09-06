#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维 · AI 哨兵前向跟踪与趋势验证引擎 (Forward Sentinel Tracker)
功能：
1. 每日自动录入四大战法 Top 3 黄金标的（建仓日期、基准成本价、物理初始张量）；
2. 每日收盘后滚动更新历史在踪标的收益、最高脉冲、最大回撤与多周期趋势收益率：
   - T+1 / T+3 / T+5 (短线冲击与防守)
   - T+22 (月度趋势形成，核心检验期)
   - T+66 (季度波段趋势)
   - T+132 (半年大级别战略护城河趋势)
3. 追踪微观筹码物理演化（主力继续锁仓 vs 放量出逃派发）；
4. 专库专用：持久化至 tianyan_sentinel_forward.duckdb，并自动联动战备库自选池。
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import duckdb
import pandas as pd
import numpy as np

# 确定工作空间路径
if os.path.exists("/mnt/workspace/quant_data"):
    DATA_DIR = Path("/mnt/workspace/quant_data")
else:
    DATA_DIR = Path(__file__).resolve().parent.parent / "quant_data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "tianyan_sentinel_forward.duckdb"


class ForwardSentinelTracker:
    """AI 哨兵前向跟踪管理器"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_con(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path))

    def _init_db(self):
        """初始化前向跟踪专库及结构表"""
        con = self._get_con()
        con.execute("""
        CREATE TABLE IF NOT EXISTS sentinel_forward_records (
            id VARCHAR PRIMARY KEY,
            entry_date VARCHAR,
            strategy VARCHAR,
            strategy_key VARCHAR,
            code VARCHAR,
            name VARCHAR,
            entry_close DOUBLE,
            entry_lfs DOUBLE,
            entry_hccyf13 DOUBLE,
            entry_cpr DOUBLE,
            entry_bri DOUBLE,
            entry_z_profit DOUBLE,
            latest_date VARCHAR,
            latest_close DOUBLE,
            holding_days INTEGER,
            pnl_pct DOUBLE,
            max_high_pct DOUBLE,
            max_drawdown_pct DOUBLE,
            t1_return DOUBLE,
            t3_return DOUBLE,
            t5_return DOUBLE,
            t22_return DOUBLE,
            t66_return DOUBLE,
            t132_return DOUBLE,
            trend_status VARCHAR,
            chip_evolution VARCHAR,
            is_active BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        con.close()

    def seed_daily_picks(self, entry_date: str, picks: List[Dict[str, Any]]) -> int:
        """
        录入某交易日的新建仓标的
        """
        con = self._get_con()
        added_cnt = 0
        for p in picks:
            code = str(p["code"]).zfill(6)
            strat_key = p.get("strategy_key", "common")
            rec_id = f"{entry_date}_{strat_key}_{code}"
            
            # 检查是否已存在
            exists = con.execute("SELECT COUNT(*) FROM sentinel_forward_records WHERE id = ?", [rec_id]).fetchone()[0]
            if exists > 0:
                continue

            entry_close = float(p.get("close", 0.0))
            con.execute("""
            INSERT INTO sentinel_forward_records (
                id, entry_date, strategy, strategy_key, code, name,
                entry_close, entry_lfs, entry_hccyf13, entry_cpr, entry_bri, entry_z_profit,
                latest_date, latest_close, holding_days, pnl_pct, max_high_pct, max_drawdown_pct,
                t1_return, t3_return, t5_return, t22_return, t66_return, t132_return,
                trend_status, chip_evolution, is_active
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, 0, 0.0, 0.0, 0.0,
                NULL, NULL, NULL, NULL, NULL, NULL,
                '🚀 新建仓', '🔒 初始锁仓', TRUE
            )
            """, [
                rec_id, entry_date, p.get("strategy", "核心选股"), strat_key, code, p.get("name", f"标的{code}"),
                entry_close, float(p.get("LFS", 50.0)), float(p.get("HCCYF13", 50.0)),
                float(p.get("CPR", 10.0)), float(p.get("BRI", 10.0)), float(p.get("Z_profit", 50.0)),
                entry_date, entry_close
            ])
            added_cnt += 1

        con.close()
        return added_cnt

    def update_forward_tracking(self, latest_date: str, snapshot_df: Optional[pd.DataFrame] = None) -> int:
        """
        根据最新日期的全市场快照更新所有在踪标的
        """
        if snapshot_df is None or snapshot_df.empty:
            snap_path = DATA_DIR / "full_market_snapshot.parquet"
            if not snap_path.exists():
                return 0
            con_snap = duckdb.connect()
            snapshot_df = con_snap.execute(f"SELECT * FROM '{snap_path}'").df()
            con_snap.close()

        if snapshot_df.empty:
            return 0

        # 构建以 code 为 key 的行情快查字典
        snap_map = {}
        for _, r in snapshot_df.iterrows():
            c = str(r["code"]).zfill(6)
            snap_map[c] = r.to_dict()

        con = self._get_con()
        active_records = con.execute("SELECT * FROM sentinel_forward_records WHERE is_active = TRUE").df()
        if active_records.empty:
            con.close()
            return 0

        updated_cnt = 0
        for _, rec in active_records.iterrows():
            code = str(rec["code"]).zfill(6)
            if code not in snap_map:
                continue

            curr_data = snap_map[code]
            curr_close = float(curr_data.get("close", rec["latest_close"]))
            entry_close = float(rec["entry_close"])
            if entry_close <= 0:
                continue

            # 收益率计算
            pnl_pct = round((curr_close - entry_close) / entry_close * 100.0, 2)
            prev_max_high = float(rec.get("max_high_pct") or 0.0)
            max_high_pct = max(prev_max_high, pnl_pct)

            prev_max_dd = float(rec.get("max_drawdown_pct") or 0.0)
            cur_dd = round(pnl_pct - max_high_pct, 2)
            max_drawdown_pct = min(prev_max_dd, cur_dd)

            # 交易日数增量 (如果日期更新)
            prev_latest_date = str(rec.get("latest_date") or "")
            prev_days = int(rec.get("holding_days") or 0)
            new_days = prev_days + (1 if latest_date > prev_latest_date else 0)

            # 关键时间周期收益落盘 (首次触达 T+N 交易日时记录固定值)
            t1_ret = rec.get("t1_return")
            t3_ret = rec.get("t3_return")
            t5_ret = rec.get("t5_return")
            t22_ret = rec.get("t22_return")
            t66_ret = rec.get("t66_return")
            t132_ret = rec.get("t132_return")

            if new_days == 1 and t1_ret is None:
                t1_ret = pnl_pct
            if new_days == 3 and t3_ret is None:
                t3_ret = pnl_pct
            if new_days == 5 and t5_ret is None:
                t5_ret = pnl_pct
            if new_days == 22 and t22_ret is None:
                t22_ret = pnl_pct
            if new_days == 66 and t66_ret is None:
                t66_ret = pnl_pct
            if new_days == 132 and t132_ret is None:
                t132_ret = pnl_pct

            # 筹码物理形态演化追踪
            curr_lfs = float(curr_data.get("LFS", 50.0))
            curr_hccyf = float(curr_data.get("HCCYF13", 50.0))
            curr_asr = float(curr_data.get("ASR", 20.0))
            
            if curr_lfs >= curr_hccyf and curr_asr < 15.0:
                chip_evo = "🔒 主力持续锁仓"
            elif curr_lfs < curr_hccyf and curr_asr > 30.0:
                chip_evo = "🚨 筹码松动/主力派发"
            else:
                chip_evo = "⚖️ 正常博弈换手"

            # 趋势定性评价
            if pnl_pct >= 15.0:
                trend_st = "🚀 强劲主升"
            elif pnl_pct >= 3.0:
                trend_st = "📈 稳健上行"
            elif pnl_pct >= -3.0:
                trend_st = "⏳ 蓄势洗盘"
            elif pnl_pct >= -8.0:
                trend_st = "⚠️ 防守预警"
            else:
                trend_st = "✖ 趋势破坏破位"

            con.execute("""
            UPDATE sentinel_forward_records
            SET latest_date = ?,
                latest_close = ?,
                holding_days = ?,
                pnl_pct = ?,
                max_high_pct = ?,
                max_drawdown_pct = ?,
                t1_return = ?,
                t3_return = ?,
                t5_return = ?,
                t22_return = ?,
                t66_return = ?,
                t132_return = ?,
                trend_status = ?,
                chip_evolution = ?
            WHERE id = ?
            """, [
                latest_date, curr_close, new_days, pnl_pct, max_high_pct, max_drawdown_pct,
                t1_ret, t3_ret, t5_ret, t22_ret, t66_ret, t132_ret,
                trend_st, chip_evo, rec["id"]
            ])
            updated_cnt += 1

        con.close()
        return updated_cnt

    def get_all_records(self, limit: int = 200) -> pd.DataFrame:
        """获取所有跟踪记录（按建仓日期倒序）"""
        con = self._get_con()
        df = con.execute(f"SELECT * FROM sentinel_forward_records ORDER BY entry_date DESC, pnl_pct DESC LIMIT {limit}").df()
        con.close()
        return df

    def get_strategy_performance_stats(self) -> Dict[str, Any]:
        """
        统计各战法在不同周期的胜率 (Win Rate) 与平均收益 (Avg Return)
        核心周期：T+5 (短线), T+22 (月度趋势), T+66 (季度趋势)
        """
        con = self._get_con()
        df = con.execute("SELECT * FROM sentinel_forward_records").df()
        con.close()

        if df.empty:
            return {
                "total_picks": 0,
                "overall_win_rate": 0.0,
                "avg_pnl": 0.0,
                "strategy_breakdown": {}
            }

        total_picks = len(df)
        win_picks = len(df[df["pnl_pct"] > 0])
        overall_win_rate = round(win_picks / total_picks * 100.0, 1) if total_picks else 0.0
        avg_pnl = round(float(df["pnl_pct"].mean()), 2)

        # 战法分层统计
        strat_stats = {}
        for st_name, group in df.groupby("strategy"):
            cnt = len(group)
            w_cnt = len(group[group["pnl_pct"] > 0])
            w_rate = round(w_cnt / cnt * 100.0, 1) if cnt else 0.0
            a_pnl = round(float(group["pnl_pct"].mean()), 2)
            max_pnl = round(float(group["max_high_pct"].max()), 2) if not group.empty else 0.0
            strat_stats[st_name] = {
                "count": cnt,
                "win_rate": w_rate,
                "avg_pnl": a_pnl,
                "max_pnl": max_pnl
            }

        return {
            "total_picks": total_picks,
            "overall_win_rate": overall_win_rate,
            "avg_pnl": avg_pnl,
            "strategy_breakdown": strat_stats
        }

    def sync_to_watchlist(self, group_name: str = "🤖 AI 哨兵自选跟踪池"):
        """将当前在踪标的高速同步到 tianyan_watchlist 战备库分组"""
        con = self._get_con()
        df = con.execute("SELECT DISTINCT code, name FROM sentinel_forward_records WHERE is_active = TRUE").df()
        con.close()
        if df.empty:
            return

        stock_list = [{"code": str(r["code"]).zfill(6), "name": str(r["name"])} for _, r in df.iterrows()]
        try:
            from core.watchlist_manager import get_watchlist_manager
            wm = get_watchlist_manager()
            wm.batch_add_stocks(stock_list, group_name)
        except Exception:
            pass


# 全局单例
sentinel_tracker = ForwardSentinelTracker()


def extract_daily_top_picks_from_snapshot(snapshot_path: Path) -> List[Dict[str, Any]]:
    """
    从全市场物化快照 (full_market_snapshot.parquet) 中自动提取四大战法各 Top 3 标的
    """
    if not snapshot_path.exists():
        return []

    con = duckdb.connect()
    # 基础过滤: 去除退市、ST、微盘仙股
    base_filter = "name NOT LIKE '%退%' AND name NOT LIKE '%ST%' AND close > 2.0"

    sql = f"""
    SELECT 
        code, name, date, close, LFS, HCCYF13, ASR, Z_profit, X70, X90, CYS34,
        ROUND((LFS * HCCYF13) / (GREATEST(ASR, 0.5) * (1.0 + 3.0 / 100.0) + 0.001), 2) as CPR,
        ROUND(((100.0 - 20.0) * Z_profit) / (GREATEST(X70, 0.5) * GREATEST(ASR, 0.5) + 0.001), 2) as BRI
    FROM read_parquet('{snapshot_path}')
    WHERE {base_filter}
    """
    all_df = con.execute(sql).df()
    con.close()

    if all_df.empty:
        return []

    picks = []

    # 1. ⚡ 超导死锁 Top 3
    df_lock = all_df.sort_values("CPR", ascending=False).head(3)
    for _, r in df_lock.iterrows():
        d = r.to_dict()
        d["strategy"] = "⚡ 超导死锁"
        d["strategy_key"] = "lock"
        picks.append(d)

    # 2. 🌟 物理真空 Top 3
    df_vac = all_df.sort_values("BRI", ascending=False).head(3)
    for _, r in df_vac.iterrows():
        d = r.to_dict()
        d["strategy"] = "🌟 物理真空"
        d["strategy_key"] = "vacuum"
        picks.append(d)

    # 3. 💎 战略黄金坑 Top 3 (CYS34 负向超卖且 LFS 稳固)
    df_pit = all_df[all_df["LFS"] >= 40.0].sort_values("CYS34", ascending=True).head(3)
    for _, r in df_pit.iterrows():
        d = r.to_dict()
        d["strategy"] = "💎 战略黄金坑"
        d["strategy_key"] = "pit"
        picks.append(d)

    # 4. 👑 超级主升 Top 3 (获利盘高度饱和 + LFS 高)
    all_df["rise_score"] = all_df["Z_profit"] * 0.5 + all_df["LFS"] * 0.5
    df_rise = all_df.sort_values("rise_score", ascending=False).head(3)
    for _, r in df_rise.iterrows():
        d = r.to_dict()
        d["strategy"] = "👑 超级主升"
        d["strategy_key"] = "rise"
        picks.append(d)

    return picks


if __name__ == "__main__":
    print(f"Initializing Forward Sentinel Tracker at: {DB_PATH}")
    tracker = ForwardSentinelTracker()
    stats = tracker.get_strategy_performance_stats()
    print("Initial Sentinel Stats:", stats)
