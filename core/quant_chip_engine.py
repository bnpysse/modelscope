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
    五维筹码物理场数学积分引擎 V2
    升级特性：
    1. 非对称加速度阻尼衰减 (Asymmetric MCD Damping) 抑制高换手对倒冲刷
    2. 无量一字跌停保底衰减机制
    3. ATR 波动率归一化乖离率 (Norm_BIAS_5_20)
    4. 日/周/月跨周期筹码张量协整共振评分
    """

    def __init__(
        self,
        price_bins: int = 1500,
        price_min: float = 0.5,
        price_max: float = 500.0,
        damping_beta: float = 1.8,
        extreme_gamma: float = 0.005,
    ):
        self.bins = price_bins
        self.p_min = price_min
        self.p_max = price_max
        self.damping_beta = damping_beta
        self.extreme_gamma = extreme_gamma
        self.p_axis = np.linspace(price_min, price_max, price_bins)
        self.dp = self.p_axis[1] - self.p_axis[0]

    def compute_mcd_series(
        self,
        df_ohlcv: pl.DataFrame,
        use_damping: bool = True
    ) -> pl.DataFrame:
        """
        输入包含 open, high, low, close, turnover_rate 的历史行情序列
        通过微积分递推求解全时间序列的筹码分布矩阵与一手五维量化指标
        """
        # 字段兼容性处理
        schema_cols = {c.lower(): c for c in df_ohlcv.columns}
        c_col = schema_cols.get("close", "Close")
        h_col = schema_cols.get("high", "High")
        l_col = schema_cols.get("low", "Low")
        o_col = schema_cols.get("open", "Open")
        t_col = schema_cols.get("turnover", schema_cols.get("turnover_rate", schema_cols.get("turn", "Turnover")))
        date_col = schema_cols.get("date", "Date")

        closes = df_ohlcv[c_col].cast(pl.Float64).to_numpy()
        highs = df_ohlcv[h_col].cast(pl.Float64).to_numpy()
        lows = df_ohlcv[l_col].cast(pl.Float64).to_numpy()
        opens = df_ohlcv[o_col].cast(pl.Float64).to_numpy() if o_col in df_ohlcv.columns else closes
        
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
        eff_turnovers = np.zeros(n_days)

        # 初始化第 0 日筹码分布 (首日高低价区间均匀分布)
        chip_dist = np.zeros(self.bins)
        first_lo = int(np.clip((lows[0] - min_p) / dp, 0, self.bins - 1))
        first_hi = int(np.clip((highs[0] - min_p) / dp, 0, self.bins - 1))
        span_0 = max(1, first_hi - first_lo + 1)
        chip_dist[first_lo:first_hi + 1] = 1.0 / (span_0 * dp)

        cyc34 = closes[0]

        # 核心物理场时间步进衰减积分
        for t in range(n_days):
            raw_t_rate = turnovers[t]
            cur_close = closes[t]
            cur_low = lows[t]
            cur_high = highs[t]

            # 1. 阻尼修正与极端行情保底计算
            if use_damping:
                # 非对称饱和阻尼: T_t* = T_t / (1 + beta * T_t)
                t_rate = raw_t_rate / (1.0 + self.damping_beta * raw_t_rate)
                # 一字跌停保底: 换手极低 (T_t < 0.001) 且相比前一日大幅收跌 (>= 9%)
                if t > 0 and raw_t_rate < 0.001 and cur_close <= closes[t - 1] * 0.91:
                    t_rate = max(t_rate, self.extreme_gamma)
            else:
                t_rate = raw_t_rate

            eff_turnovers[t] = t_rate

            # 2. 构造当日成交的日内密度分布 f_t(P) (采用日内高低区间均匀分布)
            lo_idx = int(np.clip((cur_low - min_p) / dp, 0, self.bins - 1))
            hi_idx = int(np.clip((cur_high - min_p) / dp, 0, self.bins - 1))
            span = max(1, hi_idx - lo_idx + 1)
            
            today_dist = np.zeros(self.bins)
            today_dist[lo_idx:hi_idx + 1] = 1.0 / (span * dp)

            # 3. 筹码衰减递推：C_t(P) = (1 - T_t*)*C_{t-1}(P) + T_t**f_t(P)
            chip_dist = (1.0 - t_rate) * chip_dist + t_rate * today_dist
            
            # 归一化积分 ∫ C_t(P) dP = 1.0
            total_mass = np.sum(chip_dist) * dp
            if total_mass > 0:
                chip_dist /= total_mass

            # 4. 积分求解 Z (获利比例: 收盘价下方的累积筹码面积)
            c_idx = int(np.clip((cur_close - min_p) / dp, 0, self.bins - 1))
            z_val = np.sum(chip_dist[:c_idx]) * dp * 100.0
            z_scores[t] = np.clip(z_val, 0.0, 100.0)

            # 5. 积分求解 ASR (活动筹码: 收盘价 ±10% 区间内的筹码面积)
            p_lo_10 = int(np.clip((cur_close * 0.90 - min_p) / dp, 0, self.bins - 1))
            p_hi_10 = int(np.clip((cur_close * 1.10 - min_p) / dp, 0, self.bins - 1))
            asr_val = np.sum(chip_dist[p_lo_10:p_hi_10]) * dp * 100.0
            asr_scores[t] = np.clip(asr_val, 0.0, 100.0)

            # 6. 求解累积分布函数 (CDF) 与反函数分位数 (X70 / X90 集中度)
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

            # 7. 多周期指数换手成本均线 CYC5, CYC13, CYC34, CYC_Infinity 递推
            alpha_5 = 2.0 / (5.0 + 1.0)
            alpha_13 = 2.0 / (13.0 + 1.0)
            alpha_34 = 2.0 / (34.0 + 1.0)
            
            cyc5 = (1.0 - alpha_5 * t_rate) * (cyc5 if t > 0 else cur_close) + (alpha_5 * t_rate) * cur_close
            cyc13 = (1.0 - alpha_13 * t_rate) * (cyc13 if t > 0 else cur_close) + (alpha_13 * t_rate) * cur_close
            cyc34 = (1.0 - alpha_34 * t_rate) * cyc34 + (alpha_34 * t_rate) * cur_close
            # 无穷成本均线 CYC_Infinity (全局筹码质心价格)
            cyc_inf = np.sum(p_axis * chip_dist) * dp
            
            cyc34_scores[t] = cyc34

        # 计算真实波幅 TR 与 ATR_20
        prev_closes = np.roll(closes, 1)
        prev_closes[0] = closes[0]
        tr = np.maximum(highs - lows, np.maximum(np.abs(highs - prev_closes), np.abs(lows - prev_closes)))

        # 将积分向量与 Polars 衍生均线无缝拼装
        res = df_ohlcv.with_columns([
            pl.Series("Z_Profit", z_scores),
            pl.Series("ASR", asr_scores),
            pl.Series("X70", x70_scores),
            pl.Series("X90", x90_scores),
            pl.Series("CYC34", cyc34_scores),
            pl.Series("Effective_Turnover", eff_turnovers),
            pl.Series("TR", tr),
        ])

        # 衍生高阶因子与全套战术指标
        # 1. 维度一（底座与阵地）：LFS, HCCYF13, 剪刀差, 斜率, CYF66_Raw, VMA_CYF55, 斐波那契死锁比
        res = res.with_columns([
            (pl.col("Z_Profit") - pl.col("Z_Profit").shift(1)).fill_null(0.0).alias("Z_diff1"),
            # 筹码锁定因子 LFS (与浮筹 ASR 构成物理互补沉淀)
            (100.0 - pl.col("ASR") * 0.85).alias("LFS"),
            # 20日真实波幅 ATR_20
            pl.col("TR").rolling_mean(20, min_samples=1).alias("ATR_20"),
            # 5日与20日均线
            pl.col(c_col).rolling_mean(5, min_samples=1).alias("MA5"),
            pl.col(c_col).rolling_mean(20, min_samples=1).alias("MA20"),
            # 5日与13日指数成本均线 CYC5, CYC13
            (pl.col(c_col).ewm_mean(span=5)).alias("CYC5"),
            (pl.col(c_col).ewm_mean(span=13)).alias("CYC13"),
            # 无穷成本均线 CYC_Infinity
            (pl.col(c_col).cum_sum() / pl.int_range(1, pl.len() + 1)).alias("CYC_Infinity"),
        ])

        res = res.with_columns([
            # 13日短线锁定均线 (底座护城河)
            pl.col("LFS").rolling_mean(13, min_samples=1).alias("HCCYF13"),
            # 暴力锁仓剪刀差 (LFS 升与 ASR 降)
            (pl.col("LFS") - pl.col("ASR")).alias("LFS_ASR_Scissor"),
            # 3日 LFS 控盘加速度斜率: Slope3 = (LFS_t - LFS_{t-2})/2
            ((pl.col("LFS") - pl.col("LFS").shift(2)) / 2.0).fill_null(0.0).alias("Slope3_LFS"),
            # CYF66 跨周期死锁基底与 T+55 斐波那契均线比
            pl.col("LFS").rolling_mean(66, min_samples=1).alias("CYF66_Raw"),
            # CYS13 与 CYS34 (市场盈亏偏离度)
            ((pl.col(c_col) - pl.col("CYC13")) / pl.col("CYC13") * 100.0).alias("CYS13"),
            ((pl.col(c_col) - pl.col("CYC34")) / pl.col("CYC34") * 100.0).alias("CYS34"),
            # BIAS 5/20
            ((pl.col("MA5") - pl.col("MA20")) / pl.col("MA20") * 100.0).fill_null(0.0).alias("BIAS_5_20"),
            # 活筹换手率 D = Turnover / max(ASR/100, 0.05)
            (pl.col(t_col) / (pl.col("ASR") / 100.0).clip(0.05, 1.0)).alias("D_Dynamic_Turnover"),
        ]).with_columns([
            # 剪刀差 Scissor = HCCYF13 - LFS (死叉为正，稳固为负)
            (pl.col("HCCYF13") - pl.col("LFS")).alias("Scissor"),
            # VMA(T+55) 斐波那契均线
            pl.col("CYF66_Raw").rolling_mean(55, min_samples=1).alias("VMA_CYF55"),
            # ATR 波动率归一化 BIAS
            (pl.col("BIAS_5_20") / ((pl.col("ATR_20") / pl.col(c_col) * 100.0).clip(0.5, 50.0))).fill_null(0.0).alias("Norm_BIAS_5_20"),
            # 庄股雷达 BIAS(CYC5, CYC_Infinity)
            ((pl.col("CYC5") - pl.col("CYC_Infinity")) / pl.col("CYC_Infinity") * 100.0).alias("BIAS_CYC5_CYCInf"),
            # 活筹换手率历史分位 D_pos (0~100)
            ((pl.col("D_Dynamic_Turnover") - pl.col("D_Dynamic_Turnover").rolling_min(60, min_samples=1)) /
             (pl.col("D_Dynamic_Turnover").rolling_max(60, min_samples=1) - pl.col("D_Dynamic_Turnover").rolling_min(60, min_samples=1) + 1e-6) * 100.0).fill_null(50.0).alias("D_pos"),
        ]).with_columns([
            # 斐波那契死锁比值敞口
            (pl.col("CYF66_Raw") - pl.col("VMA_CYF55")).alias("CYF_Spread_66_55"),
            # 2. 维度二：绝对真空走廊判断 (Z' > 10 且 X90 < 10 或 Z' > 15 且 X90 <= 15)
            ((pl.col("Z_diff1") > 10.0) & (pl.col("X90") < 10.0) | ((pl.col("Z_diff1") > 15.0) & (pl.col("X90") <= 15.0))).alias("Is_Vacuum_Corridor"),
            # 庄股加速豁免标记: Z > 95% 且 Turnover < 3% 或 BIAS(CYC5, CYC_Inf) > 30%
            (((pl.col("Z_Profit") > 95.0) & (pl.col(t_col) < 3.0)) | (pl.col("BIAS_CYC5_CYCInf") > 30.0)).alias("Is_Major_Controlled"),
            # 4. 维度四：极限装死区 (Y > 60 且 Turnover < 3.5%)
            ((pl.col("X90") > 25.0) & (pl.col(t_col) < 3.5)).alias("Is_Extreme_Hibernation"),
            # 黄金坑战略买点 (CYS34 < -15% 且底座未死叉 LFS >= HCCYF13)
            ((pl.col("CYS34") < -15.0) & (pl.col("LFS") >= pl.col("HCCYF13"))).alias("Is_Golden_Pit"),
            # 3. 维度三：游资击鼓传花预警 (D_pos > 70)
            (pl.col("D_pos") > 70.0).alias("Is_Hot_Potato_Warning"),
        ])

        return res

    def compute_multi_period_resonance(self, df_daily: pl.DataFrame) -> Dict[str, Any]:
        """
        计算标的日线、周线、月线跨周期筹码张量协整共振得分
        """
        if len(df_daily) < 15:
            return {
                "resonance_score": 50.0,
                "is_super_resonance": False,
                "day_status": "数据不足",
                "week_status": "数据不足",
                "month_status": "数据不足",
                "diagnosis": "历史数据不足 15 交易日"
            }

        daily_mcd = self.compute_mcd_series(df_daily)
        latest_day = daily_mcd.tail(1).to_dicts()[0]

        # 1. 评估日线筹码状态
        day_lock = latest_day.get("LFS", 0) >= latest_day.get("HCCYF13", 0) * 0.95
        day_single_peak = latest_day.get("X90", 100) < 16.0
        day_profit = latest_day.get("Z_Profit", 0) > 40.0
        day_score = (35.0 if day_lock else 10.0) + (15.0 if day_single_peak else 5.0)

        # 2. 模拟周线合成 (每 5 交易日聚合)
        schema_cols = {c.lower(): c for c in df_daily.columns}
        c_col = schema_cols.get("close", "Close")
        h_col = schema_cols.get("high", "High")
        l_col = schema_cols.get("low", "Low")
        o_col = schema_cols.get("open", "Open")
        t_col = schema_cols.get("turnover", schema_cols.get("turnover_rate", schema_cols.get("turn", "Turnover")))
        date_col = schema_cols.get("date", "Date")

        n_weeks = len(df_daily) // 5
        if n_weeks >= 4:
            # 采用 5 日滑动窗口代表周频
            df_week = df_daily.with_columns([
                pl.col(c_col).rolling_mean(5, min_samples=1).alias(c_col),
                pl.col(h_col).rolling_max(5, min_samples=1).alias(h_col),
                pl.col(l_col).rolling_min(5, min_samples=1).alias(l_col),
                pl.col(t_col).rolling_sum(5, min_samples=1).alias(t_col),
            ]).filter(pl.int_range(0, pl.len()) % 5 == 0)
            
            week_mcd = self.compute_mcd_series(df_week)
            latest_week = week_mcd.tail(1).to_dicts()[0]
            week_lock = latest_week.get("LFS", 0) >= latest_week.get("HCCYF13", 0) * 0.9
            week_single_peak = latest_week.get("X90", 100) < 18.0
            week_score = (25.0 if week_lock else 5.0) + (10.0 if week_single_peak else 5.0)
        else:
            week_lock = day_lock
            week_single_peak = day_single_peak
            week_score = 20.0

        # 3. 模拟月线合成 (每 20 交易日聚合)
        n_months = len(df_daily) // 20
        if n_months >= 2:
            df_month = df_daily.with_columns([
                pl.col(c_col).rolling_mean(20, min_samples=1).alias(c_col),
                pl.col(h_col).rolling_max(20, min_samples=1).alias(h_col),
                pl.col(l_col).rolling_min(20, min_samples=1).alias(l_col),
                pl.col(t_col).rolling_sum(20, min_samples=1).alias(t_col),
            ]).filter(pl.int_range(0, pl.len()) % 20 == 0)

            month_mcd = self.compute_mcd_series(df_month)
            latest_month = month_mcd.tail(1).to_dicts()[0]
            month_lock = latest_month.get("LFS", 0) >= latest_month.get("HCCYF13", 0) * 0.85
            month_score = 15.0 if month_lock else 5.0
        else:
            month_lock = week_lock
            month_score = 10.0

        total_resonance = round(min(100.0, day_score + week_score + month_score), 1)
        is_super = (total_resonance >= 80.0 and day_lock and week_lock)

        return {
            "resonance_score": total_resonance,
            "is_super_resonance": is_super,
            "day_lock": bool(day_lock),
            "week_lock": bool(week_lock),
            "month_lock": bool(month_lock),
            "day_single_peak": bool(day_single_peak),
            "diagnosis": "【三周期筹码多头大共振·超级主升浪】" if is_super else (
                "【日/周多头共振·动能健康】" if total_resonance >= 65.0 else (
                    "【周期分歧·震荡蓄势】" if total_resonance >= 45.0 else "【多周期筹码崩塌·弱势规避】"
                )
            )
        }


# 全局单例
chip_engine = QuantChipMathEngine()
