#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高精移动成本分布 (Moving Cost Distribution, MCD) 物理场与全市场五维筹码数学引擎
1. 采用高分辨率连续价格网格积分 (Price-Bin Integral) 求解筹码演化偏微分方程
2. 递推计算：Z(获利比例), ASR(活动筹码), X70/X90(单峰集中度), LFS(锁定因子), CYS34(成本偏离), BIAS 5/20
3. 支持单标的高精度历史全周期回溯与全市场批量增量状态递推
"""

import os
import time
import numpy as np
import polars as pl
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class QuantChipMathEngine:
    """
    五维筹码物理场数学积分引擎
    """

    def __init__(self, price_bins: int = 1500, price_min: float = 0.5, price_max: float = 500.0):
        self.bins = price_bins
        self.p_min = price_min
        self.p_max = price_max
        self.p_axis = np.linspace(price_min, price_max, price_bins)
        self.dp = self.p_axis[1] - self.p_axis[0]

    def compute_mcd_series(self, df_ohlcv: pl.DataFrame) -> pl.DataFrame:
        """
        输入包含 open, high, low, close, turnover_rate 的历史行情序列
        通过微积分递推求解全时间序列的筹码分布矩阵与一手五维量化指标
        """
        # 字段兼容性处理
        schema_cols = {c.lower(): c for c in df_ohlcv.columns}
        c_col = schema_cols.get("close", "Close")
        h_col = schema_cols.get("high", "High")
        l_col = schema_cols.get("low", "Low")
        t_col = schema_cols.get("turnover", schema_cols.get("turnover_rate", schema_cols.get("turn", "Turnover")))
        date_col = schema_cols.get("date", "Date")

        closes = df_ohlcv[c_col].cast(pl.Float64).to_numpy()
        highs = df_ohlcv[h_col].cast(pl.Float64).to_numpy()
        lows = df_ohlcv[l_col].cast(pl.Float64).to_numpy()
        
        # 换手率规范化为 [0, 1] 比例
        raw_to = df_ohlcv[t_col].cast(pl.Float64).to_numpy()
        turnovers = np.where(raw_to > 1.0, raw_to / 100.0, raw_to)
        turnovers = np.clip(np.nan_to_num(turnovers, nan=0.03), 0.0001, 0.9999)

        n_days = len(closes)
        if n_days == 0:
            return df_ohlcv

        # 动态根据该股票的历史极值自适应调整价格区间
        min_p = max(0.1, np.min(lows) * 0.7)
        max_p = np.max(highs) * 1.3
        p_axis = np.linspace(min_p, max_p, self.bins)
        dp = p_axis[1] - p_axis[0]

        z_scores = np.zeros(n_days)
        asr_scores = np.zeros(n_days)
        x70_scores = np.zeros(n_days)
        x90_scores = np.zeros(n_days)
        cyc34_scores = np.zeros(n_days)

        # 初始化第 0 日筹码分布 (首日高低价区间均匀分布)
        chip_dist = np.zeros(self.bins)
        first_lo = int(np.clip((lows[0] - min_p) / dp, 0, self.bins - 1))
        first_hi = int(np.clip((highs[0] - min_p) / dp, 0, self.bins - 1))
        span_0 = max(1, first_hi - first_lo + 1)
        chip_dist[first_lo:first_hi + 1] = 1.0 / (span_0 * dp)

        cyc34 = closes[0]

        # 核心物理场时间步进衰减积分
        for t in range(n_days):
            t_rate = turnovers[t]
            cur_close = closes[t]
            cur_low = lows[t]
            cur_high = highs[t]

            # 1. 构造当日成交的日内密度分布 f_t(P) (采用日内高低区间均匀三角加权近似)
            lo_idx = int(np.clip((cur_low - min_p) / dp, 0, self.bins - 1))
            hi_idx = int(np.clip((cur_high - min_p) / dp, 0, self.bins - 1))
            span = max(1, hi_idx - lo_idx + 1)
            
            today_dist = np.zeros(self.bins)
            today_dist[lo_idx:hi_idx + 1] = 1.0 / (span * dp)

            # 2. 筹码衰减递推：C_t(P) = (1 - T_t)*C_{t-1}(P) + T_t*f_t(P)
            chip_dist = (1.0 - t_rate) * chip_dist + t_rate * today_dist
            
            # 归一化积分 ∫ C_t(P) dP = 1.0
            total_mass = np.sum(chip_dist) * dp
            if total_mass > 0:
                chip_dist /= total_mass

            # 3. 积分求解 Z (获利比例: 收盘价下方的累积筹码面积)
            c_idx = int(np.clip((cur_close - min_p) / dp, 0, self.bins - 1))
            z_val = np.sum(chip_dist[:c_idx]) * dp * 100.0
            z_scores[t] = np.clip(z_val, 0.0, 100.0)

            # 4. 积分求解 ASR (活动筹码: 收盘价 ±10% 区间内的筹码面积)
            p_lo_10 = int(np.clip((cur_close * 0.90 - min_p) / dp, 0, self.bins - 1))
            p_hi_10 = int(np.clip((cur_close * 1.10 - min_p) / dp, 0, self.bins - 1))
            asr_val = np.sum(chip_dist[p_lo_10:p_hi_10]) * dp * 100.0
            asr_scores[t] = np.clip(asr_val, 0.0, 100.0)

            # 5. 求解累积分布函数 (CDF) 与反函数分位数 (X70 / X90 集中度)
            cdf = np.cumsum(chip_dist) * dp
            
            # X90: 90% 筹码区间 (5% ~ 95%)
            idx_05 = np.searchsorted(cdf, 0.05)
            idx_95 = np.searchsorted(cdf, 0.95)
            p_05 = p_axis[min(idx_05, self.bins - 1)]
            p_95 = p_axis[min(idx_95, self.bins - 1)]
            x90_scores[t] = ((p_95 - p_05) / (p_95 + p_05 + 1e-6)) * 100.0

            # X70: 70% 筹码区间 (15% ~ 85%)
            idx_15 = np.searchsorted(cdf, 0.15)
            idx_85 = np.searchsorted(cdf, 0.85)
            p_15 = p_axis[min(idx_15, self.bins - 1)]
            p_85 = p_axis[min(idx_85, self.bins - 1)]
            x70_scores[t] = ((p_85 - p_15) / (p_85 + p_15 + 1e-6)) * 100.0

            # 6. 34日指数换手成本均线 CYC34 递推
            alpha = 2.0 / (34.0 + 1.0)
            cyc34 = (1.0 - alpha * t_rate) * cyc34 + (alpha * t_rate) * cur_close
            cyc34_scores[t] = cyc34

        # 将积分向量与 Polars 衍生均线无缝拼装
        res = df_ohlcv.with_columns([
            pl.Series("Z_Profit", z_scores),
            pl.Series("ASR", asr_scores),
            pl.Series("X70", x70_scores),
            pl.Series("X90", x90_scores),
            pl.Series("CYC34", cyc34_scores),
        ])

        # 衍生高阶因子：LFS, HCCYF13, CYS34, BIAS, 剪刀差, 斜率
        res = res.with_columns([
            (pl.col("Z_Profit") - pl.col("Z_Profit").shift(1)).fill_null(0.0).alias("Z_diff1"),
            # 筹码锁定因子 LFS (与浮筹 ASR 构成物理互补沉淀)
            (100.0 - pl.col("ASR") * 0.85).alias("LFS"),
            # CYS34 (市场盈亏偏离度)
            ((pl.col(c_col) - pl.col("CYC34")) / pl.col("CYC34") * 100.0).alias("CYS34"),
            # BIAS 5/20
            ((pl.col(c_col).rolling_mean(5) - pl.col(c_col).rolling_mean(20)) /
             pl.col(c_col).rolling_mean(20) * 100.0).fill_null(0.0).alias("BIAS_5_20"),
        ]).with_columns([
            # 13日短线锁定均线 (底座护城河)
            pl.col("LFS").rolling_mean(13, min_periods=1).alias("HCCYF13"),
            # 3日 LFS 控盘加速度斜率
            ((pl.col("LFS") - pl.col("LFS").shift(2)) / 2.0).fill_null(0.0).alias("Slope3_LFS"),
        ]).with_columns([
            # 剪刀差 Scissor = HCCYF13 - LFS
            (pl.col("HCCYF13") - pl.col("LFS")).alias("Scissor"),
        ])

        return res


# 全局单例
chip_engine = QuantChipMathEngine()
