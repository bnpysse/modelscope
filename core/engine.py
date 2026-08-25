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


class OmniEngine:
    """
    Polars 驱动的天眼全息量化数据引擎。
    """

    DEFAULT_NAMES = {
        "300475": "香农芯创",
        "300223": "北京君正",
        "300322": "硕贝德",
        "001309": "德明利",
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

        # 标的列表
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

    def get_targets(self) -> List[TARGET_INFO]:
        """获取标的列表"""
        return self._targets

    def get_stock_name(self, code: str) -> str:
        """获取标的中文名称"""
        code_clean = str(code).replace(".0", "").zfill(6)
        for t in self._targets:
            if t.code == code_clean:
                return t.name
        return self.DEFAULT_NAMES.get(code_clean, f"标的 {code_clean}")

    def get_stock_data(self, code: str, days: int = 0) -> pl.DataFrame:
        """
        获取单标的数据切片。
        """
        code_padded = str(code).replace(".0", "").zfill(6)

        stock_df = self._df.filter(
            pl.col(self._code_col)
            .cast(pl.Utf8)
            .str.replace_all(r"\.0$", "")
            .str.zfill(6)
            == code_padded
        ).sort("Date")

        if days > 0:
            stock_df = stock_df.tail(days)

        return stock_df

    def get_latest_snapshot(self, code: str) -> Dict[str, Any]:
        """
        获取单标的最新一日的全维数据快照。
        """
        stock_df = self.get_stock_data(code, days=2)
        if stock_df.is_empty():
            return {}

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
            cyf66_raw = stock_df["HCCYF13"].tail(66).mean()
            cyf66_vma55 = stock_df["HCCYF13"].tail(55).mean()
        else:
            cyf66_raw = latest.get("HCCYF13", 50.0)
            cyf66_vma55 = latest.get("HCCYF13", 50.0)

        # 扩充快照字段
        latest["MA5"] = round(float(ma5), 2)
        latest["MA20"] = round(float(ma20), 2)
        latest["BIAS_5_20"] = float(bias_5_20)
        latest["Slope3_LFS"] = float(slope3_lfs)
        latest["CYF66_Raw"] = float(cyf66_raw) if cyf66_raw else 50.0
        latest["CYF66_VMA55"] = float(cyf66_vma55) if cyf66_vma55 else 50.0
        latest["Stock_Name"] = self.get_stock_name(code)

        return latest

    def get_fibonacci_depth_matrix(self, code: str, periods: List[int] = [5, 13, 34, 55, 89, 144, 198]) -> List[Dict[str, Any]]:
        """
        计算标的的斐波那契战略纵深矩阵 (5, 13, 34, 55, 89, 144, 198)
        """
        stock_df = self.get_stock_data(code)
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
                .rolling_mean(window_size=p, min_periods=1)
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
                    .rolling_mean(window_size=p, min_periods=1)
                    .over(code)
                    .alias(f"Turnover_MA{p}")
                )
            if "PTR" in df.columns:
                dim5_exprs.append(
                    pl.col("PTR")
                    .rolling_mean(window_size=p, min_periods=1)
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
                    pl.col("Main_Pct").rolling_sum(window_size=w, min_periods=1).over(code).alias(f"Main_{w}d"),
                    pl.col("Dare_Pct").rolling_sum(window_size=w, min_periods=1).over(code).alias(f"Dare_{w}d"),
                    pl.col("Sum_Pct").rolling_sum(window_size=w, min_periods=1).over(code).alias(f"Sum_{w}d"),
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
                .rolling_mean(window_size=13, min_periods=1)
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
    """创建引擎单例"""
    base = base_dir or str(Path(__file__).resolve().parent.parent)
    csv_candidates = [
        os.path.join(base, "data", "stock.csv"),
        os.path.join(base, "stock.csv"),
        os.path.join(base, "data", "stock_clean.csv"),
    ]
    valid_csv = [p for p in csv_candidates if os.path.exists(p)]
    if not valid_csv:
        raise FileNotFoundError(f"未找到数据文件 stock.csv 于 {base}")

    csv_path = max(valid_csv, key=os.path.getmtime)
    plan_path = os.path.join(base, "data", "battle_plan.json")
    if not os.path.exists(plan_path):
        plan_path = None

    return OmniEngine(csv_path=csv_path, battle_plan_path=plan_path)
