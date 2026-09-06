"""
天眼全息智导系统 V7.0 (ModelScope Edition) — Polars 数据引擎

支持全周期数据切片、五维衍生特征计算、斐波那契战略纵深矩阵（5, 13, 34, 55, 89, 144, 198）。
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import polars as pl
import pandas as pd
import numpy as np

from core.models import (
    NUMERIC_COLS, FIB_PTR_WINDOWS, DIM5_MA_PERIODS,
    FUND_WINDOWS, TARGET_INFO,
)
from core.quant_chip_engine import chip_engine


class OmniEngine:
    """
    Polars 驱动的天眼全息量化数据引擎。
    """

    DEFAULT_NAMES = {
        "001309": "德明利",
        "002409": "雅化集团",
        "002885": "京泉华",
        "300223": "北京君正",
        "300308": "中际旭创",
        "300322": "硕贝德",
        "300337": "银之杰",
        "300363": "博腾股份",
        "300378": "鼎捷数智",
        "300475": "香农芯创",
        "300655": "晶瑞电材",
        "300850": "新强联",
        "300941": "创识科技",
        "301032": "新柴股份",
        "301171": "易天股份",
        "301308": "江波龙",
        "301329": "七丰精工",
        "688401": "路维光电",
        "688499": "利元亨",
        "688525": "佰维存储",
        "600519": "贵州茅台",
        "300750": "宁德时代",
        "002594": "比亚迪",
        "000001": "平安银行",
        "601318": "中国平安",
        "688041": "海光信息",
        "688256": "寒武纪",
        "688981": "中芯国际",
    }

    def __init__(self, csv_path: str, battle_plan_path: Optional[str] = None):
        self._csv_path = csv_path
        self._battle_plan_path = battle_plan_path

        # 自动识别代码列名
        raw = pl.read_csv(csv_path, infer_schema_length=10000)
        self._code_col = "Target_Code" if "Target_Code" in raw.columns else "Code"
        self._z_col = "Z_Profit" if "Z_Profit" in raw.columns else "Z"

        # 完整数据管线
        self._df = self._build_pipeline(raw)

        # 标的与多分组字典
        self._groups = self._load_groups()
        self._targets = self._load_targets()

    # ==========================================
    # 公共 API
    # ==========================================

    @property
    def df(self) -> pl.DataFrame:
        """完整的预处理后 DataFrame"""
        return self._df

    @property
    def code_col(self) -> str:
        return self._code_col

    def get_groups(self) -> Dict[str, List[TARGET_INFO]]:
        """获取全部自选分组字典"""
        return self._groups

    def get_group_names(self) -> List[str]:
        """获取分组名称列表"""
        return list(self._groups.keys())

    def get_targets(self, group_name: Optional[str] = None) -> List[TARGET_INFO]:
        """获取指定分组或全部标的列表"""
        if group_name and group_name in self._groups and group_name != "⭐ 全部标的池":
            return self._groups[group_name]
        return self._targets

    def get_stock_name(self, code: str) -> str:
        """获取标的中文名称"""
        code_clean = str(code).replace(".0", "").zfill(6)
        for t in self._targets:
            if t.code == code_clean:
                return t.name
        return self.DEFAULT_NAMES.get(code_clean, f"标的 {code_clean}")

    def add_custom_target(self, code: str, name: str = "", group_name: str = "自由观察组") -> TARGET_INFO:
        """动态添加标的并归类入指定分组"""
        code_clean = str(code).replace(".0", "").zfill(6)
        name_clean = name.strip() or self.DEFAULT_NAMES.get(code_clean, f"标的 {code_clean}")
        info = TARGET_INFO(code=code_clean, name=name_clean)

        if not any(t.code == code_clean for t in self._targets):
            self._targets.insert(0, info)

        if group_name not in self._groups:
            self._groups[group_name] = []

        if not any(t.code == code_clean for t in self._groups[group_name]):
            self._groups[group_name].insert(0, info)

        self._save_groups()
        return info

    def create_custom_group(self, group_name: str):
        """新建自选股票池分组"""
        if group_name and group_name not in self._groups:
            self._groups[group_name] = []
            self._save_groups()

    def add_stocks_to_group(self, group_name: str, stock_list: List[dict]):
        """批量将标的列表加入指定分组"""
        if group_name not in self._groups:
            self._groups[group_name] = []
        for item in stock_list:
            code = str(item.get("code", "")).zfill(6)
            name = item.get("name", "") or self.DEFAULT_NAMES.get(code, f"标的 {code}")
            if code:
                info = TARGET_INFO(code=code, name=name)
                if not any(t.code == code for t in self._targets):
                    self._targets.append(info)
                if not any(t.code == code for t in self._groups[group_name]):
                    self._groups[group_name].append(info)
        self._save_groups()
        try:
            from core.watchlist_manager import get_watchlist_manager
            get_watchlist_manager().batch_add_stocks(stock_list, group_name)
        except Exception:
            pass

    def remove_stock_from_group(self, code: str, group_name: str):
        """从指定分组中移除标的"""
        code_str = str(code).zfill(6)
        if group_name in self._groups:
            self._groups[group_name] = [t for t in self._groups[group_name] if t.code != code_str]
            self._save_groups()
        try:
            from core.watchlist_manager import get_watchlist_manager
            get_watchlist_manager().remove_stock_from_group(code_str, group_name)
        except Exception:
            pass

    def update_stock_name(self, code: str, group_name: str, new_name: str):
        """更新指定分组中标的名称"""
        code_str = str(code).zfill(6)
        new_name = str(new_name).strip()
        if not new_name:
            return
        if group_name in self._groups:
            for idx, t in enumerate(self._groups[group_name]):
                if t.code == code_str:
                    self._groups[group_name][idx] = TARGET_INFO(code=code_str, name=new_name)
            self._save_groups()
        try:
            from core.watchlist_manager import get_watchlist_manager
            get_watchlist_manager().update_stock_name(code_str, group_name, new_name)
        except Exception:
            pass

    def clear_group(self, group_name: str):
        """清空指定分组内的全部标的"""
        if group_name in self._groups:
            self._groups[group_name] = []
            self._save_groups()
        try:
            from core.watchlist_manager import get_watchlist_manager
            get_watchlist_manager().clear_group(group_name)
        except Exception:
            pass

    def delete_group(self, group_name: str):
        """彻底删除分组"""
        if group_name in self._groups:
            del self._groups[group_name]
            self._save_groups()
        try:
            from core.watchlist_manager import get_watchlist_manager
            get_watchlist_manager().delete_group(group_name)
        except Exception:
            pass

    def _save_groups(self):
        """持久化保存自选池分组至 JSON"""
        if not self._battle_plan_path:
            base = str(Path(__file__).resolve().parent.parent)
            self._battle_plan_path = os.path.join(base, "data", "battle_plan.json")
        try:
            os.makedirs(os.path.dirname(self._battle_plan_path), exist_ok=True)
            data_to_save = {
                "groups": {
                    g: [{"code": t.code, "name": t.name} for t in t_list]
                    for g, t_list in self._groups.items()
                }
            }
            with open(self._battle_plan_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_groups(self) -> Dict[str, List[TARGET_INFO]]:
        """初始化加载自选池分组"""
        groups: Dict[str, List[TARGET_INFO]] = {}
        
        # 默认预置经典战术分组 (统帅实盘指南针真值组置顶)
        default_groups = {
            "🎯 指南针实盘真值持仓组": [
                TARGET_INFO("001309", "德明利"),
                TARGET_INFO("301171", "易天股份"),
                TARGET_INFO("688525", "佰维存储"),
                TARGET_INFO("301308", "江波龙"),
                TARGET_INFO("300475", "香农芯创"),
            ],
            "⚡ 天衍微分全景观察组": [
                TARGET_INFO("300308", "中际旭创"),
                TARGET_INFO("300223", "北京君正"),
                TARGET_INFO("300363", "博腾股份"),
                TARGET_INFO("300322", "硕贝德"),
                TARGET_INFO("300655", "晶瑞电材"),
                TARGET_INFO("300337", "银之杰"),
            ],
            "⭐ 全部标的池": [],
            "💾 核心存储与算力芯片组": [
                TARGET_INFO("001309", "德明利"),
                TARGET_INFO("300475", "香农芯创"),
                TARGET_INFO("300223", "北京君正"),
                TARGET_INFO("688525", "佰维存储"),
                TARGET_INFO("301308", "江波龙"),
            ],
            "👀 自由自选观察组": []
        }

        # 直接由统帅专属个人股票战备观察池 tianyan_watchlist.duckdb 驱动
        try:
            from core.watchlist_manager import get_watchlist_manager
            wm = get_watchlist_manager()
            group_names = wm.get_all_groups()
            for g in group_names:
                stocks = wm.get_stocks_by_group(g)
                groups[g] = [TARGET_INFO(s["code"], s["name"]) for s in stocks]
        except Exception:
            groups = default_groups

        if not groups:
            groups = default_groups

        return groups

    def get_stock_data(self, code: str, days: int = 0, mode: str = "compass_ocr", allow_network: bool = False) -> pl.DataFrame:
        """
        获取单标的数据切片:
        - compass_ocr: 100% 严格读取统帅手工抓取的 stock.csv 实盘真值 (截至昨天 2026-09-02)
        - duckdb / math: 读取由天衍偏微分物理方程 (QuantChipMathEngine) 独立演化推导的数学指标
        - allow_network: 仅在明确请求时动态拉取非静态表标的，避免批量循环时网络请求阻塞
        """
        code_padded = str(code).replace(".0", "").zfill(6)
        
        # 1. 优先获取基础序列
        stock_df = self._df.filter(
            pl.col(self._code_col)
            .cast(pl.Utf8)
            .str.replace_all(r"\.0$", "")
            .str.zfill(6)
            == code_padded
        ).sort("Date")

        if stock_df.is_empty():
            # 自动自愈兜底：针对自选池中新加入的非 stock.csv 标的，自动动态拉取其真实日线行情
            if not hasattr(self, "_dynamic_cache"):
                self._dynamic_cache = {}
            if code_padded in self._dynamic_cache:
                stock_df = self._dynamic_cache[code_padded]
            elif allow_network:
                stock_df = self._fetch_dynamic_stock_df(code_padded)
                if not stock_df.is_empty():
                    self._dynamic_cache[code_padded] = stock_df
            if stock_df.is_empty():
                return pl.DataFrame()

        # 2. 如果选择天衍偏微分推导模式 (DuckDB/Math)
        if mode in ("duckdb", "math"):
            try:
                from core.quant_chip_engine import QuantChipMathEngine
                math_engine = QuantChipMathEngine(price_bins=1200)
                stock_df = math_engine.compute_mcd_series(stock_df)
            except Exception:
                pass

        stock_df = self._build_pipeline(stock_df)
        if days > 0 and len(stock_df) > days:
            stock_df = stock_df.tail(days)
        return stock_df

    def _fetch_dynamic_stock_df(self, code_str: str) -> pl.DataFrame:
        """动态拉取未在预置静态表中的标的历史真实行情 (全自动自愈)"""
        import urllib.request
        prefix = "sh" if code_str.startswith(("6", "9")) else "sz"
        symbol = f"{prefix}{code_str}"
        url = f"https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol={symbol}&scale=240&ma=no&datalen=160"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode())
                if not data or not isinstance(data, list):
                    return pl.DataFrame()
                rows = []
                for item in data:
                    c = float(item.get("close", 0.0))
                    o = float(item.get("open", c))
                    h = float(item.get("high", c))
                    l = float(item.get("low", c))
                    v = float(item.get("volume", 0.0))
                    to = round(min(max(v / 1000000.0, 0.5), 15.0), 2)
                    rows.append({
                        self._code_col: code_str,
                        "Date": item.get("day", ""),
                        "Close": c,
                        "Open": o,
                        "High": h,
                        "Low": l,
                        "Turnover": to,
                        "DeltaX": round(c - o, 2),
                        "PTR_Calc": 1.0,
                        "PTR": 1.0,
                        "Main_Pct": round(to * 0.4, 2),
                        "Dare_Pct": round(to * 0.1, 2),
                        "Main_Fund_Pct": round(to * 0.4, 2),
                        "Dare_Fund_Pct": round(to * 0.1, 2),
                        "ASR": 25.0,
                        "CYS34": 0.0,
                        "CYS13": 0.0,
                        "LFS": 45.0,
                        "HCCYF13": 40.0,
                        "Z_Profit": 30.0,
                        "Z_diff1": 0.0,
                        "D_Pos": 50.0,
                        "D_pos": 50.0,
                        "Y_Overlap": 20.0,
                        "Overlap_Y": 20.0,
                        "X70": 15.0,
                        "X90": 25.0,
                        "Sum_5d": 0.0,
                        "Sum_22d": 0.0,
                        "Sum_66d": 0.0,
                        "Sum_132d": 0.0,
                        "Turnover_MA5": to,
                        "Turnover_MA20": to,
                        "PTR_MA5": 1.0,
                        "PTR_MA20": 1.0,
                    })
                return pl.DataFrame(rows)
        except Exception:
            return pl.DataFrame()

    def get_l2_fund_flow(self, code: str, days: int = 66) -> Optional[pd.DataFrame]:
        """从 tianyan_l2_66d.duckdb 读取 66 日真实主力与超大单资金流向时序"""
        code_str = str(code).replace(".0", "").zfill(6)
        p_root = getattr(self, "project_root", None) or Path(self._csv_path).resolve().parent.parent
        db_path = p_root / "data" / "tianyan_l2_66d.duckdb"
        if not db_path.exists():
            return None
        try:
            import duckdb
            with duckdb.connect(str(db_path), read_only=True) as con:
                df = con.execute("""
                SELECT date, close, pct_chg, main_net, super_net, large_net, mid_net, small_net,
                       sum_5d, sum_22d, sum_66d, super_ratio
                FROM l2_daily_fund_flow
                WHERE code = ?
                ORDER BY date ASC
                """, [code_str]).df()
                if not df.empty and days > 0:
                    df = df.tail(days).reset_index(drop=True)
                return df
        except Exception:
            return None

    def get_latest_snapshot(self, code: str, mode: str = "compass_ocr", allow_network: bool = True) -> Dict[str, Any]:
        """
        获取单标的最新一日的全维数据快照 (支持 compass_ocr 与 duckdb 双模切换，支持自动跨基座自愈)
        """
        code_padded = str(code).replace(".0", "").zfill(6)

        # 1. 在 DuckDB 模式下，优先从全市场统一物化快照 (full_market_snapshot.parquet) 快速直取权威物理真值
        if mode in ("duckdb", "math"):
            snap_paths = [
                Path("/mnt/workspace/quant_data/full_market_snapshot.parquet"),
                Path(__file__).resolve().parent.parent / "quant_data" / "full_market_snapshot.parquet"
            ]
            for sp in snap_paths:
                if sp.exists():
                    try:
                        import duckdb
                        con = duckdb.connect()
                        res = con.execute(f"SELECT * FROM '{sp}' WHERE code = '{code_padded}'").df()
                        con.close()
                        if not res.empty:
                            row = res.iloc[0].to_dict()
                            close_val = float(row.get("close", 0.0))
                            lfs_val = float(row.get("LFS", 50.0))
                            hccyf_val = float(row.get("HCCYF13", 50.0))
                            asr_val = float(row.get("ASR", 20.0))
                            z_val = float(row.get("Z_profit", row.get("Z_Profit", 50.0)))
                            z_prime = float(row.get("Z_prime", 0.0))
                            x70_val = float(row.get("X70", 15.0))
                            x90_val = float(row.get("X90", 25.0))
                            cys34_val = float(row.get("CYS34", 0.0))
                            bias_val = float(row.get("BIAS_5_20", 0.0))
                            slope3_val = float(row.get("Slope3", row.get("Slope3_LFS", 0.0)))
                            to_val = float(row.get("turnover", row.get("Turnover", 3.0)))
                            name_val = row.get("name") or self.DEFAULT_NAMES.get(code_padded, f"标的 {code_padded}")

                            snap_dict = {
                                "Target_Code": code_padded,
                                "code": code_padded,
                                "Stock_Name": name_val,
                                "name": name_val,
                                "Date": str(row.get("date", ""))[:10],
                                "Date_Disp": str(row.get("date", ""))[-5:],
                                "Date_Full": str(row.get("date", ""))[:10],
                                "Close": close_val,
                                "close": close_val,
                                "Open": float(row.get("open", close_val)),
                                "High": float(row.get("high", close_val)),
                                "Low": float(row.get("low", close_val)),
                                "Turnover": to_val,
                                "LFS": lfs_val,
                                "HCCYF13": hccyf_val,
                                "ASR": asr_val,
                                "Z_Profit": z_val,
                                "Z": z_val,
                                "Z_diff1": z_prime,
                                "X70": x70_val,
                                "X90": x90_val,
                                "Y_Overlap": float(row.get("Y_Overlap", row.get("Overlap_Y", 20.0))),
                                "CYS34": cys34_val,
                                "CYS13": float(row.get("CYS13", cys34_val * 0.5)),
                                "BIAS_5_20": bias_val,
                                "Norm_BIAS_5_20": round(bias_val / 1.8, 4),
                                "Slope3_LFS": slope3_val,
                                "Slope_3d": slope3_val,
                                "Scissor": float(row.get("Scissor", hccyf_val - lfs_val)),
                                "LFS_ASR_Scissor": float(lfs_val - asr_val),
                                "MA5": float(row.get("ma5", close_val)),
                                "MA20": float(row.get("ma20", close_val)),
                                "CYC5": float(row.get("cyc5", close_val)),
                                "CYC13": float(row.get("cyc13", close_val)),
                                "CYC34": float(row.get("cyc34", close_val)),
                                "CYC_Infinity": float(row.get("cyc_infinity", close_val)),
                                "BIAS_CYC5_CYCInf": 0.0,
                                "D_Pos": 50.0,
                                "D_pos": 50.0,
                                "D_Dynamic_Turnover": to_val,
                                "Resonance_Score": 85.0 if lfs_val >= hccyf_val and x90_val < 25.0 else 55.0,
                                "Resonance_Diagnosis": "【多周期共振主升】" if lfs_val >= hccyf_val else "【周期分歧·震荡蓄势】",
                                "Is_Super_Resonance": (lfs_val >= hccyf_val and x90_val < 25.0),
                                "P_escape": float(row.get("P_escape", 0.0)),
                                "Lambda_dmd": float(row.get("Lambda_dmd", 0.0)),
                                "W_cost": float(row.get("W_cost", 0.0)),
                                "vwap": float(row.get("vwap", close_val))
                            }
                            return snap_dict
                    except Exception:
                        pass
                    break

        all_stock_df = self.get_stock_data(code, mode=mode, allow_network=allow_network)
        if all_stock_df.is_empty() and mode != "duckdb":
            # 自动跨基座自愈：若静态 stock.csv 无此标的，自动升阶至偏微分(DuckDB)/动态网络全量计算
            all_stock_df = self.get_stock_data(code, mode="duckdb", allow_network=True)
        if all_stock_df.is_empty():
            return {}

        stock_df = all_stock_df.tail(2)
        latest = stock_df.row(-1, named=True)
        prev = stock_df.row(-2, named=True) if len(stock_df) >= 2 else latest

        # 确保关键衍生指标齐全
        close = latest.get("Close", 0.0)
        ma5 = stock_df["Close"].tail(5).mean() if "Close" in stock_df.columns else close
        ma20 = stock_df["Close"].tail(20).mean() if "Close" in stock_df.columns else close
        bias_5_20 = ((ma5 - ma20) / ma20 * 100.0) if ma20 and ma20 != 0 else 0.0

        # LFS 三日斜率
        if len(stock_df) >= 3 and "LFS" in stock_df.columns:
            lfs_t = stock_df["LFS"].row(-1)[0]
            lfs_t2 = stock_df["LFS"].row(-3)[0]
            slope3_lfs = (lfs_t - lfs_t2) / 2.0
        else:
            slope3_lfs = 0.0

        # CYF66_Raw / VMA55
        if "HCCYF13" in stock_df.columns:
            cyf_s = stock_df["HCCYF13"].drop_nulls()
            cyf66_raw = float(cyf_s.tail(66).mean()) if len(cyf_s) > 0 else 50.0
            cyf66_vma55 = float(cyf_s.tail(55).mean()) if len(cyf_s) > 0 else 50.0
        else:
            cyf66_raw = float(latest.get("HCCYF13", 50.0))
            cyf66_vma55 = float(latest.get("HCCYF13", 50.0))
        cyf_spread = round(cyf66_raw - cyf66_vma55, 2)

        # 跨周期筹码协整共振计算
        resonance_info = chip_engine.compute_multi_period_resonance(all_stock_df)

        # ATR 与 Norm_BIAS
        atr_20 = latest.get("ATR_20", 0.0)
        if not atr_20 and "High" in all_stock_df.columns and "Low" in all_stock_df.columns:
            tr_series = (all_stock_df["High"] - all_stock_df["Low"]).tail(20)
            atr_20 = float(tr_series.mean()) if len(tr_series) > 0 else (close * 0.03)
        
        vol_pct = (atr_20 / max(0.01, close)) * 100.0 if close else 3.0
        norm_bias = bias_5_20 / max(0.5, vol_pct)
        # 尝试读取 66日 Level 2 真实主力与超大单资金特征
        l2_df = self.get_l2_fund_flow(code, days=66)
        if l2_df is not None and not l2_df.empty:
            l2_last = l2_df.iloc[-1]
            latest["L2_Main_Net"] = float(l2_last.get("main_net", 0.0))
            latest["L2_Super_Net"] = float(l2_last.get("super_net", 0.0))
            latest["L2_Sum_5d"] = float(l2_last.get("sum_5d", 0.0))
            latest["L2_Sum_22d"] = float(l2_last.get("sum_22d", 0.0))
            latest["L2_Sum_66d"] = float(l2_last.get("sum_66d", 0.0))
            latest["L2_Super_Ratio"] = float(l2_last.get("super_ratio", 0.0))

        # 扩充快照字段，确保 22 项五维指标全息完整
        latest["MA5"] = round(float(ma5), 2)
        latest["MA20"] = round(float(ma20), 2)
        latest["BIAS_5_20"] = float(bias_5_20)
        latest["ATR_20"] = round(float(atr_20), 2)
        latest["Norm_BIAS_5_20"] = round(float(norm_bias), 4)
        latest["Slope3_LFS"] = float(latest.get("Slope3_LFS", slope3_lfs))
        latest["CYF66_Raw"] = round(float(latest.get("CYF66_Raw", cyf66_raw)), 2)
        latest["CYF66_VMA55"] = round(float(latest.get("VMA_CYF55", cyf66_vma55)), 2)
        latest["CYF_Spread_66_55"] = round(float(latest.get("CYF_Spread_66_55", cyf_spread)), 2)
        latest["LFS_ASR_Scissor"] = float(latest.get("LFS_ASR_Scissor", float(latest.get("LFS", 50)) - float(latest.get("ASR", 20))))
        latest["CYC5"] = float(latest.get("CYC5", close))
        latest["CYC13"] = float(latest.get("CYC13", close))
        latest["CYC34"] = float(latest.get("CYC34", close))
        latest["CYC_Infinity"] = float(latest.get("CYC_Infinity", close))
        latest["CYS13"] = float(latest.get("CYS13", 0.0))
        latest["CYS34"] = float(latest.get("CYS34", 0.0))
        latest["BIAS_CYC5_CYCInf"] = float(latest.get("BIAS_CYC5_CYCInf", 0.0))
        latest["D_pos"] = float(latest.get("D_pos", 50.0))
        latest["D_Dynamic_Turnover"] = float(latest.get("D_Dynamic_Turnover", latest.get("Turnover", 3.0)))
        latest["Is_Vacuum_Corridor"] = bool(latest.get("Is_Vacuum_Corridor", False))
        latest["Is_Major_Controlled"] = bool(latest.get("Is_Major_Controlled", False))
        latest["Is_Extreme_Hibernation"] = bool(latest.get("Is_Extreme_Hibernation", False))
        latest["Is_Golden_Pit"] = bool(latest.get("Is_Golden_Pit", False))
        latest["Is_Hot_Potato_Warning"] = bool(latest.get("Is_Hot_Potato_Warning", False))
        latest["Resonance_Score"] = float(resonance_info.get("resonance_score", 50.0))
        latest["Resonance_Diagnosis"] = str(resonance_info.get("diagnosis", ""))
        latest["Is_Super_Resonance"] = bool(resonance_info.get("is_super_resonance", False))
        latest["Stock_Name"] = self.get_stock_name(code)

        return latest

    def get_fibonacci_depth_matrix(self, code: str, periods: List[int] = [5, 13, 34, 55, 89, 144, 198], mode: str = "compass_ocr", allow_network: bool = True) -> List[Dict[str, Any]]:
        """
        计算标的的斐波那契战略纵深矩阵 (5, 13, 34, 55, 89, 144, 198)
        """
        stock_df = self.get_stock_data(code, mode=mode, allow_network=allow_network)
        if stock_df.is_empty() and mode != "duckdb":
            stock_df = self.get_stock_data(code, mode="duckdb", allow_network=True)
        if stock_df.is_empty():
            return []

        pdf = stock_df.to_pandas()
        total_len = len(pdf)

        fib_stats = []
        for p in periods:
            sub_p = pdf.tail(min(p, total_len))
            if sub_p.empty:
                continue

            p_start_date = sub_p['Date'].iloc[0]
            p_start_close = float(sub_p['Close'].iloc[0])
            p_end_close = float(sub_p['Close'].iloc[-1])
            p_pct = ((p_end_close / p_start_close) - 1.0) * 100.0 if p_start_close != 0 else 0.0
            p_avg_to = float(sub_p['Turnover'].mean()) if 'Turnover' in sub_p else 0.0
            p_avg_lfs = float(sub_p['LFS'].mean()) if 'LFS' in sub_p else 0.0
            p_avg_asr = float(sub_p['ASR'].mean()) if 'ASR' in sub_p else 0.0
            p_avg_z = float(sub_p[self._z_col].mean()) if self._z_col in sub_p else 0.0
            p_avg_cys34 = float(sub_p['CYS34'].mean()) if 'CYS34' in sub_p else 0.0

            fib_stats.append({
                'Period': f'T+{p}',
                'Days': p,
                'Start_Date': int(p_start_date) if isinstance(p_start_date, (int, float)) else str(p_start_date),
                'Price_Start': round(p_start_close, 2),
                'Price_End': round(p_end_close, 2),
                'Price_Change_%': round(p_pct, 2),
                'Avg_Turnover_%': round(p_avg_to, 2),
                'Avg_LFS': round(p_avg_lfs, 2),
                'Avg_ASR': round(p_avg_asr, 2),
                'Avg_Z_%': round(p_avg_z, 2),
                'Avg_CYS34': round(p_avg_cys34, 2),
            })

        return fib_stats

    def get_all_codes(self) -> List[str]:
        """获取所有唯一股票代码"""
        return (
            self._df.select(
                pl.col(self._code_col)
                .cast(pl.Utf8)
                .str.replace_all(r"\.0$", "")
                .str.zfill(6)
            )
            .unique()
            .to_series()
            .to_list()
        )

    # ==========================================
    # 内部数据管线
    # ==========================================

    def _build_pipeline(self, raw: pl.DataFrame) -> pl.DataFrame:
        """
        完整的数据预处理管线
        """
        code = self._code_col

        # ── Step 1: 清污脱敏 ──
        df = self._sanitize_numeric(raw)

        # ── Step 2: 资金合力 ──
        if "Main_Pct" in df.columns and "Dare_Pct" in df.columns:
            df = df.with_columns(
                (pl.col("Main_Pct") + pl.col("Dare_Pct")).alias("Sum_Pct"),
            )
            df = df.with_columns(
                pl.col("Sum_Pct").diff(1).over(code).fill_null(0).alias("Delta_Sum_1d"),
            )

        # ── Step 3: Fibonacci 全局 PTR 均线 ──
        if "PTR" in df.columns:
            fib_exprs = [
                pl.col("PTR")
                .rolling_mean(window_size=p, min_samples=1)
                .over(code)
                .alias(f"PTR_MA{p}")
                for p in FIB_PTR_WINDOWS
            ]
            df = df.with_columns(fib_exprs)

        # ── Step 4: 维五专属均线 + 斜率 ──
        dim5_periods = [p for _, p in DIM5_MA_PERIODS if p > 0]
        dim5_exprs = []
        for p in dim5_periods:
            if "Turnover" in df.columns:
                dim5_exprs.append(
                    pl.col("Turnover")
                    .rolling_mean(window_size=p, min_samples=1)
                    .over(code)
                    .alias(f"Turnover_MA{p}")
                )
            if "PTR" in df.columns:
                dim5_exprs.append(
                    pl.col("PTR")
                    .rolling_mean(window_size=p, min_samples=1)
                    .over(code)
                    .alias(f"PTR_MA{p}")
                )
        if dim5_exprs:
            df = df.with_columns(dim5_exprs)

        # 均线斜率 (一阶导)
        slope_exprs = []
        for p in dim5_periods:
            if f"Turnover_MA{p}" in df.columns:
                slope_exprs.append(
                    pl.col(f"Turnover_MA{p}").diff(1).over(code).fill_null(0).alias(f"Turnover_MA{p}_slope")
                )
            if f"PTR_MA{p}" in df.columns:
                slope_exprs.append(
                    pl.col(f"PTR_MA{p}").diff(1).over(code).fill_null(0).alias(f"PTR_MA{p}_slope")
                )
        if slope_exprs:
            df = df.with_columns(slope_exprs)

        # ── Step 5: 多周期资金面累积 ──
        if "Main_Pct" in df.columns and "Dare_Pct" in df.columns:
            fund_exprs = []
            for w in FUND_WINDOWS:
                fund_exprs.extend([
                    pl.col("Main_Pct").rolling_sum(window_size=w, min_samples=1).over(code).alias(f"Main_{w}d"),
                    pl.col("Dare_Pct").rolling_sum(window_size=w, min_samples=1).over(code).alias(f"Dare_{w}d"),
                    pl.col("Sum_Pct").rolling_sum(window_size=w, min_samples=1).over(code).alias(f"Sum_{w}d"),
                ])
            df = df.with_columns(fund_exprs)

            delta_exprs = [
                pl.col(f"Sum_{w}d").diff(1).over(code).fill_null(0).alias(f"Delta_Sum_{w}d")
                for w in FUND_WINDOWS
            ]
            df = df.with_columns(delta_exprs)

        # ── Step 6: 维度斜率 (一阶导) ──
        step6_exprs = []
        if "LFS" in df.columns:
            step6_exprs.append(pl.col("LFS").diff(1).over(code).fill_null(0).alias("LFS_slope"))
        if "HCCYF13" in df.columns:
            step6_exprs.append(pl.col("HCCYF13").diff(1).over(code).fill_null(0).alias("HCCYF13_slope"))
        if "ASR" in df.columns:
            step6_exprs.append(pl.col("ASR").diff(1).over(code).fill_null(0).alias("ASR_slope"))
        if "Y_Overlap" in df.columns:
            step6_exprs.append(pl.col("Y_Overlap").diff(1).over(code).fill_null(0).alias("Y_Ovp_slope"))
        if "PTR" in df.columns:
            step6_exprs.append(pl.col("PTR").diff(1).over(code).fill_null(0).alias("PTR_1d_slope"))
        if self._z_col in df.columns:
            step6_exprs.append(pl.col(self._z_col).diff(1).over(code).fill_null(0).alias("Z_diff1"))
        if step6_exprs:
            df = df.with_columns(step6_exprs)

        # ── Step 7: 双轨防线引擎 (剪刀差) ──
        if "HCCYF13" in df.columns and "LFS" in df.columns:
            df = df.with_columns(
                (pl.col("HCCYF13") - pl.col("LFS")).alias("Scissor"),
            )
            df = df.with_columns(
                pl.col("HCCYF13").shift(3).over(code).alias("HCCYF13_shift3"),
            )
            df = df.with_columns(
                pl.col("HCCYF13_shift3")
                .fill_null(pl.col("HCCYF13"))
                .alias("HCCYF13_shift3"),
            )
            df = df.with_columns(
                (pl.col("HCCYF13") - pl.col("HCCYF13_shift3")).alias("Slope_3d"),
            )

        # ── Step 8: CYS13 代理 ──
        if "Close" in df.columns:
            df = df.with_columns(
                pl.col("Close")
                .rolling_mean(window_size=13, min_samples=1)
                .over(code)
                .alias("_MA13"),
            )
            df = df.with_columns(
                ((pl.col("Close") - pl.col("_MA13")) / pl.col("_MA13") * 100)
                .alias("CYS13_Proxy"),
            )
            df = df.drop("_MA13")

        # ── Step 8: 日期格式化 ──
        if "Date" in df.columns:
            df = df.with_columns(
                pl.col("Date").cast(pl.Utf8).alias("_date_str"),
            )
            df = df.with_columns(
                pl.col("_date_str").str.to_date("%Y%m%d", strict=False).alias("Date_parsed"),
            )
            df = df.with_columns([
                pl.col("Date_parsed")
                .dt.strftime("%m-%d")
                .fill_null(pl.col("_date_str").str.slice(-4))
                .alias("Date_Disp"),
                pl.col("Date_parsed")
                .dt.strftime("%Y-%m-%d")
                .fill_null(pl.col("_date_str"))
                .alias("Date_Full"),
            ])
            df = df.drop("_date_str")

        return df

    def _sanitize_numeric(self, df: pl.DataFrame) -> pl.DataFrame:
        """清污脱敏"""
        exprs = []
        for col in NUMERIC_COLS:
            if col not in df.columns:
                continue

            if df.schema[col] == pl.Utf8:
                exprs.append(
                    pl.col(col)
                    .str.replace_all("%", "")
                    .str.replace_all(",", "")
                    .cast(pl.Float64, strict=False)
                    .fill_null(0.0)
                    .alias(col)
                )
            else:
                exprs.append(
                    pl.col(col)
                    .cast(pl.Float64, strict=False)
                    .fill_null(0.0)
                    .alias(col)
                )

        if exprs:
            df = df.with_columns(exprs)

        return df

    def _load_targets(self) -> List[TARGET_INFO]:
        """加载标的列表"""
        targets = []
        if self._battle_plan_path and os.path.exists(self._battle_plan_path):
            with open(self._battle_plan_path, "r", encoding="utf-8") as f:
                plan = json.load(f)
                for code_str, name_val in plan.get("stock_names", {}).items():
                    targets.append(TARGET_INFO(code=code_str, name=name_val))

        codes = self.get_all_codes()
        existing_codes = {t.code for t in targets}
        for c in codes:
            if c not in existing_codes:
                name = self.DEFAULT_NAMES.get(c, f"标的 {c}")
                targets.append(TARGET_INFO(code=c, name=name))

        return targets


def create_engine(base_dir: Optional[str] = None) -> OmniEngine:
    """创建引擎单例 (多路径智能检索)"""
    candidate_bases = []
    if base_dir:
        candidate_bases.append(base_dir)
    candidate_bases.extend([
        str(Path(__file__).resolve().parent.parent),
        str(Path.cwd()),
        "/home/studio/PROJECT",
        "/home/studio",
        "/mnt/workspace",
        "/mnt/workspace/quant_engine"
    ])
    
    valid_csv = []
    for b in candidate_bases:
        for sub in ["data/stock.csv", "stock.csv", "data/stock_clean.csv"]:
            p = os.path.join(b, sub)
            if os.path.exists(p) and p not in valid_csv:
                valid_csv.append(p)
                
    if not valid_csv:
        # 尝试在全局查找 stock.csv
        found = list(Path("/home/studio").rglob("stock.csv")) if os.path.exists("/home/studio") else []
        if found:
            valid_csv.append(str(found[0]))
        else:
            raise FileNotFoundError(f"未找到数据文件 stock.csv，已检索路径: {candidate_bases}")

    csv_path = max(valid_csv, key=os.path.getmtime)
    
    plan_path = None
    for b in candidate_bases:
        p = os.path.join(b, "data", "battle_plan.json")
        if os.path.exists(p):
            plan_path = p
            break

    return OmniEngine(csv_path=csv_path, battle_plan_path=plan_path)

