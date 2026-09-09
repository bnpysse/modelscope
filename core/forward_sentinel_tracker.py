#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维 · AI 哨兵前向跟踪与趋势验证引擎 (Forward Sentinel Tracker)
功能：
1. 每日自动录入四大战法 Top 标的（支持全市场及双创 300/688 板块特化）；
2. 毫秒级直通今日实盘实时价格，实时更新浮动盈亏、最高脉冲、最大回撤；
3. 多周期时序追踪：T+1, T+3, T+5, T+22 (月度), T+66 (季度), T+132 (半年)；
4. 专库专用：持久化至 tianyan_sentinel_forward.duckdb。
"""

import os
import sys
import time
import json
import urllib.request
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


def fetch_bulk_realtime_quotes(codes: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    批量从极速行情接口拉取最新实时现价 (腾讯行情，单次请求可查上百只标的，0 延迟直通)
    返回: {'601985': {'current': 8.92, 'prev_close': 8.91, 'pct_chg': 0.11}, ...}
    """
    if not codes:
        return {}
    
    # 构造标的 symbol 列表
    symbols = []
    for c in codes:
        c_clean = str(c).zfill(6)
        prefix = "sh" if c_clean.startswith(("6", "9")) else "sz"
        symbols.append(f"{prefix}{c_clean}")

    # 分批次请求 (每批 60 只标的)
    quotes = {}
    batch_size = 60
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i+batch_size]
        url = f"http://qt.gtimg.cn/q={','.join(batch)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                text = resp.read().decode("gbk", errors="ignore").strip()
                for line in text.split(";"):
                    line = line.strip()
                    if "~" in line:
                        parts = line.split("~")
                        if len(parts) >= 6:
                            code = parts[2].zfill(6)
                            cur_p = float(parts[3]) if parts[3] else 0.0
                            prev_c = float(parts[4]) if parts[4] else cur_p
                            # 停牌或未开盘保护
                            if cur_p <= 0.0:
                                cur_p = prev_c
                            pct_chg = round((cur_p - prev_c) / prev_c * 100.0, 2) if prev_c > 0 else 0.0
                            quotes[code] = {
                                "current": cur_p,
                                "prev_close": prev_c,
                                "pct_chg": pct_chg,
                                "name": parts[1]
                            }
        except Exception:
            pass

    return quotes


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

    def refresh_realtime_pnl(self) -> int:
        """
        直通腾讯实时行情接口，毫秒级刷新当前所有在踪标的的最新价、浮动盈亏、最高冲刺与最大回撤
        """
        con = self._get_con()
        active_records = con.execute("SELECT * FROM sentinel_forward_records WHERE is_active = TRUE").df()
        if active_records.empty:
            con.close()
            return 0

        codes = list(active_records["code"].unique())
        realtime_map = fetch_bulk_realtime_quotes(codes)
        if not realtime_map:
            con.close()
            return 0

        updated_cnt = 0
        import datetime
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        for _, rec in active_records.iterrows():
            code = str(rec["code"]).zfill(6)
            if code not in realtime_map:
                continue

            rt = realtime_map[code]
            cur_p = rt["current"]
            entry_p = float(rec["entry_close"])
            if entry_p <= 0.0:
                continue

            # 重新精确计算实时浮盈
            pnl_pct = round((cur_p - entry_p) / entry_p * 100.0, 2)
            prev_max_high = float(rec.get("max_high_pct") or 0.0)
            max_high_pct = max(prev_max_high, pnl_pct)

            prev_max_dd = float(rec.get("max_drawdown_pct") or 0.0)
            cur_dd = round(pnl_pct - max_high_pct, 2)
            max_drawdown_pct = min(prev_max_dd, cur_dd)

            # 持仓交易日推算 (自然日简单折算工作日)
            entry_dt = str(rec["entry_date"])[:10]
            try:
                d1 = datetime.datetime.strptime(entry_dt, "%Y-%m-%d").date()
                d2 = datetime.date.today()
                # 计算两个日期之间的周一到周五数量
                workdays = sum(1 for d in range((d2 - d1).days + 1) if (d1 + datetime.timedelta(d)).weekday() < 5)
                holding_days = max(0, workdays - 1)
            except Exception:
                holding_days = int(rec.get("holding_days") or 0)

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
                trend_status = ?
            WHERE id = ?
            """, [
                today_str, cur_p, holding_days, pnl_pct, max_high_pct, max_drawdown_pct,
                trend_st, rec["id"]
            ])
            updated_cnt += 1

        con.close()
        return updated_cnt

    def get_all_records(self, limit: int = 300) -> pd.DataFrame:
        """获取所有跟踪记录（按建仓日期倒序）"""
        con = self._get_con()
        df = con.execute(f"SELECT * FROM sentinel_forward_records ORDER BY entry_date DESC, pnl_pct DESC LIMIT {limit}").df()
        con.close()
        return df

    def get_strategy_performance_stats(self) -> Dict[str, Any]:
        """
        统计各战法在不同周期的胜率与平均收益
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

    def sync_to_watchlist(self, group_name: str = "🤖 AI 哨兵自选跟踪池", sync_by_batch: bool = True):
        """
        将当前在踪标的高速同步到战备库自选池分组
        - 若 sync_by_batch=True: 自动按建仓批次智能裂变创建专属战备池，如【🤖 哨兵-0904批次】、【🤖 哨兵-0908双创批次】
        - 若 sync_by_batch=False: 统一写入指定的全量子池
        """
        con = self._get_con()
        df = con.execute("SELECT DISTINCT entry_date, strategy, code, name FROM sentinel_forward_records WHERE is_active = TRUE").df()
        con.close()
        if df.empty:
            return

        try:
            from core.watchlist_manager import get_watchlist_manager
            from core.engine import create_engine
            wm = get_watchlist_manager()
            eng = create_engine()

            if sync_by_batch:
                for entry_d, group_items in df.groupby("entry_date"):
                    clean_d = str(entry_d).replace("-", "")[4:]
                    batch_group_name = f"🤖 哨兵-{clean_d}批次"
                    s_list = [{"code": str(r["code"]).zfill(6), "name": str(r["name"])} for _, r in group_items.iterrows()]
                    wm.batch_add_stocks(s_list, batch_group_name)
                    eng.add_stocks_to_group(batch_group_name, s_list)

            # 同时维护全量聚合总池
            all_list = [{"code": str(r["code"]).zfill(6), "name": str(r["name"])} for _, r in df.iterrows()]
            wm.batch_add_stocks(all_list, group_name)
            eng.add_stocks_to_group(group_name, all_list)
        except Exception as e:
            print(f"Sync watchlist warning: {e}")



# 全局单例
sentinel_tracker = ForwardSentinelTracker()


def extract_daily_top_picks_from_snapshot(
    snapshot_path: Path,
    board_filter: str = "all"
) -> List[Dict[str, Any]]:
    """
    从全市场物化快照 (full_market_snapshot.parquet) 中提取四大战法 Top 3 标的
    board_filter 支持:
    - 'all': 全市场
    - 'chinext_star': 重点聚焦：创业板 (300) & 科创板 (688)
    - 'main': 仅主板 (60/00)
    """
    if not snapshot_path.exists():
        return []

    con = duckdb.connect()
    base_filter = "name NOT LIKE '%退%' AND name NOT LIKE '%ST%' AND close > 2.0"
    if board_filter == "chinext_star":
        base_filter += " AND (code LIKE '300%' OR code LIKE '688%')"
    elif board_filter == "main":
        base_filter += " AND (code NOT LIKE '300%' AND code NOT LIKE '688%' AND code NOT LIKE '8%' AND code NOT LIKE '4%')"

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

    # 3. 💎 战略黄金坑 Top 3
    df_pit = all_df[all_df["LFS"] >= 40.0].sort_values("CYS34", ascending=True).head(3)
    for _, r in df_pit.iterrows():
        d = r.to_dict()
        d["strategy"] = "💎 战略黄金坑"
        d["strategy_key"] = "pit"
        picks.append(d)

    # 4. 👑 超级主升 Top 3
    all_df["rise_score"] = all_df["Z_profit"] * 0.5 + all_df["LFS"] * 0.5
    df_rise = all_df.sort_values("rise_score", ascending=False).head(3)
    for _, r in df_rise.iterrows():
        d = r.to_dict()
        d["strategy"] = "👑 超级主升"
        d["strategy_key"] = "rise"
        picks.append(d)

    return picks


def auto_seed_missing_batches(
    snapshot_path: Path,
    tracker: Optional[ForwardSentinelTracker] = None
) -> Dict[str, Any]:
    """
    盘后/开机自适应补齐与自动建仓机制：
    1. 自动读取快照文件中的最新交易日 (latest_date)；
    2. 查询数据库中是否已存在该交易日的建仓批次；
    3. 若不存在，则自动提取全市场 Top 标的 + 双创 (300/688) 特化标的，执行无感入池；
    4. 自动裂变生成专属自选池并核算现价。
    """
    if tracker is None:
        tracker = sentinel_tracker

    if not snapshot_path.exists():
        return {"status": "skipped", "reason": "snapshot_not_found"}

    con = duckdb.connect()
    try:
        latest_date_res = con.execute(f"SELECT MAX(date) FROM read_parquet('{snapshot_path}')").fetchone()
        latest_date = str(latest_date_res[0]) if latest_date_res and latest_date_res[0] else None
    except Exception as e:
        return {"status": "error", "reason": str(e)}
    finally:
        con.close()

    if not latest_date:
        return {"status": "skipped", "reason": "no_date_in_snapshot"}

    # 检查该日期是否已经建仓
    con_db = tracker._get_con()
    try:
        existing_cnt = con_db.execute("SELECT COUNT(*) FROM sentinel_forward_records WHERE entry_date = ?", [latest_date]).fetchone()[0]
    finally:
        con_db.close()

    if existing_cnt > 0:
        return {"status": "already_exists", "date": latest_date, "count": existing_cnt}

    # 执行全自动建仓：全市场 Top 标的 + 双创 300/688 重点聚焦标的
    all_picks = extract_daily_top_picks_from_snapshot(snapshot_path, board_filter="all")
    star_picks = extract_daily_top_picks_from_snapshot(snapshot_path, board_filter="chinext_star")
    combined_picks = all_picks + star_picks

    added_cnt = tracker.seed_daily_picks(latest_date, combined_picks)
    tracker.refresh_realtime_pnl()
    tracker.sync_to_watchlist("🤖 AI 哨兵自选跟踪池", sync_by_batch=True)

    return {
        "status": "seeded",
        "date": latest_date,
        "added_count": added_cnt
    }

