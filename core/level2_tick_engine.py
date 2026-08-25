#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Level-2 逐笔订单流与微观结构推升效率分析引擎 (Level-2 Microstructure Order Flow Engine)
1. 提取全天 4000~10000 笔逐笔成交明细 (带主动买盘/主动卖盘/中性盘属性)
2. 计算高频主动买盘占比 (Active Buy Ratio, ABR)、超大单/大单/中小单资金净流入
3. 求解微观结构真实推升效率 eta_micro 与主力高位对倒出货识别
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import polars as pl
import akshare as ak


class Level2TickEngine:
    """Level-2 逐笔微观结构分析引擎"""

    def fetch_stock_tick_series(self, code: str) -> pl.DataFrame:
        """
        拉取单只标的单日全量逐笔成交数据 (支持 sh/sz/bj)
        """
        symbol = code.lower()
        if not symbol.startswith(("sh", "sz", "bj")):
            if symbol.startswith(("60", "688")):
                symbol = f"sh{symbol}"
            else:
                symbol = f"sz{symbol}"

        # 通过腾讯/网易 Level-2 逐笔快照通道拉取
        raw_df = ak.stock_zh_a_tick_tx_js(symbol=symbol)
        if raw_df is None or raw_df.empty:
            raise ValueError(f"未能拉取到 {code} 的 Level-2 逐笔数据")

        # 转换为 Polars DataFrame
        df = pl.from_pandas(raw_df).rename({
            "成交时间": "Time",
            "成交价格": "Price",
            "价格变动": "Price_Change",
            "成交量": "Volume_Lots", # 手
            "成交金额": "Amount",     # 元
            "性质": "Side"           # 买盘 / 卖盘 / 中性盘
        })

        return df

    def compute_level2_micro_features(self, df_tick: pl.DataFrame, daily_turnover: float = 0.0) -> Dict[str, Any]:
        """
        微积分与订单流融合：从逐笔成交中提炼 Level-2 高频微观特征
        """
        total_volume = df_tick["Volume_Lots"].sum()
        total_amount = df_tick["Amount"].sum()

        # 1. 主动买盘 / 主动卖盘 / 中性盘聚合
        buy_df = df_tick.filter(pl.col("Side") == "买盘")
        sell_df = df_tick.filter(pl.col("Side") == "卖盘")
        neutral_df = df_tick.filter(pl.col("Side") == "中性盘")

        active_buy_vol = buy_df["Volume_Lots"].sum() if len(buy_df) > 0 else 0
        active_sell_vol = sell_df["Volume_Lots"].sum() if len(sell_df) > 0 else 0
        active_buy_amt = buy_df["Amount"].sum() if len(buy_df) > 0 else 0.0
        active_sell_amt = sell_df["Amount"].sum() if len(sell_df) > 0 else 0.0

        # 主动买盘占比 (Active Buy Ratio, ABR)
        abr = float(active_buy_vol / max(1, total_volume)) * 100.0
        asr_ratio = float(active_sell_vol / max(1, total_volume)) * 100.0

        # 2. 单笔大单分层 (根据成交金额分层: 超大单 > 100万, 大单 20万~100万, 中单 5万~20万, 小单 < 5万)
        super_large_df = df_tick.filter(pl.col("Amount") >= 1_000_000)
        large_df = df_tick.filter((pl.col("Amount") >= 200_000) & (pl.col("Amount") < 1_000_000))
        small_df = df_tick.filter(pl.col("Amount") < 50_000)

        super_large_buy_amt = super_large_df.filter(pl.col("Side") == "买盘")["Amount"].sum() if len(super_large_df) > 0 else 0.0
        super_large_sell_amt = super_large_df.filter(pl.col("Side") == "卖盘")["Amount"].sum() if len(super_large_df) > 0 else 0.0
        super_large_net = super_large_buy_amt - super_large_sell_amt

        large_buy_amt = large_df.filter(pl.col("Side") == "买盘")["Amount"].sum() if len(large_df) > 0 else 0.0
        large_sell_amt = large_df.filter(pl.col("Side") == "卖盘")["Amount"].sum() if len(large_df) > 0 else 0.0
        large_net = large_buy_amt - large_sell_amt

        main_capital_net = super_large_net + large_net # 主力大单净额

        # 3. 微观推升效率 eta_micro (结合价格变动与主动买盘)
        prices = df_tick["Price"].to_numpy()
        price_pct_chg = (prices[-1] - prices[0]) / max(0.01, prices[0]) * 100.0
        
        turnover_base = daily_turnover if daily_turnover > 0.01 else 1.0
        # 推升效率 = (价格变动 / 换手率) * (2 * ABR - 1)
        # 当 ABR > 50% 时为正推升，当 ABR < 50% 时为负推升
        eta_micro = (price_pct_chg / turnover_base) * (2.0 * (abr / 100.0) - 1.0)

        # 4. 主力对倒出货识别警报 (Wash Trading Detector)
        # 特征：换手率高、成交密集，但主动买盘占比 < 45% 且主力大单净流出 > 0
        is_wash_trading_dump = (turnover_base > 8.0 and abr < 45.0 and main_capital_net < 0)
        # 主力隐蔽吸筹识别
        is_stealth_accumulation = (turnover_base < 3.0 and abr > 65.0 and super_large_net > 0)

        return {
            "total_ticks": len(df_tick),
            "total_amount_wan": round(total_amount / 10000.0, 2),
            "active_buy_ratio_%": round(abr, 2),
            "active_sell_ratio_%": round(asr_ratio, 2),
            "super_large_net_wan": round(super_large_net / 10000.0, 2),
            "large_net_wan": round(large_net / 10000.0, 2),
            "main_capital_net_wan": round(main_capital_net / 10000.0, 2),
            "eta_micro_thrust": round(eta_micro, 4),
            "is_wash_trading_dump": bool(is_wash_trading_dump),
            "is_stealth_accumulation": bool(is_stealth_accumulation),
            "micro_diagnosis": "【主力高位对倒出货·警惕诱多】" if is_wash_trading_dump else (
                "【主力隐蔽吸筹·底座强行锁定】" if is_stealth_accumulation else (
                    "【主动多头强力推升】" if abr > 55.0 else "【多空常规微观博弈】"
                )
            )
        }


level2_engine = Level2TickEngine()
