#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 DuckDB 的全市场五维筹码物理场秒级战术筛选引擎
支持纯 SQL 对 /mnt/workspace/quant_data/ 目录下所有股票的历史与截面因子进行穿透式初筛
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import duckdb
import polars as pl

if os.path.exists("/mnt/workspace/quant_data"):
    WORKSPACE_DIR = Path("/mnt/workspace")
else:
    WORKSPACE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = WORKSPACE_DIR / "quant_data"
FACTORS_DIR = DATA_DIR / "factors"


class DuckDBMarketScreener:
    """DuckDB 极速战术初筛器 V2"""

    def __init__(self, factors_dir: Path = FACTORS_DIR):
        self.factors_dir = factors_dir
        self.con = duckdb.connect()

    def _get_target_parquet_glob(self) -> str:
        """获取因子 Parquet 文件路径 Glob"""
        if self.factors_dir.exists() and list(self.factors_dir.glob("*.parquet")):
            return str(self.factors_dir / "*.parquet")
        # 兼容备选路径
        fallback_dir = Path(__file__).resolve().parent.parent / "quant_data" / "factors"
        if fallback_dir.exists() and list(fallback_dir.glob("*.parquet")):
            return str(fallback_dir / "*.parquet")
        return str(self.factors_dir / "*.parquet")

    def run_custom_query(self, sql_query: str) -> pl.DataFrame:
        """执行任意自定义 DuckDB SQL 查询"""
        return self.con.execute(sql_query).pl()

    def scan_vacuum_corridor(self) -> pl.DataFrame:
        """
        战术初筛 1：【物理真空走廊 + 极度单峰】
        条件：Z' > 5.0 (获利盘跃升) 或 X70 < 10% (单峰密集) 且 LFS 护城河多头
        """
        parquet_glob = self._get_target_parquet_glob()
        sql = f"""
        WITH latest_rows AS (
            SELECT *, 
                   regexp_extract(filename, '([0-9]{{6}})', 1) as clean_code,
                   ROW_NUMBER() OVER(PARTITION BY regexp_extract(filename, '([0-9]{{6}})', 1) ORDER BY Date DESC) as rn
            FROM read_parquet('{parquet_glob}', filename=true, union_by_name=true)
        )
        SELECT 
            clean_code as code, 
            Date as date,
            ROUND(Close, 2) as close, 
            ROUND(Z_Profit, 2) as Z_pct, 
            ROUND(Z_diff1, 2) as Z_prime,
            ROUND(X70, 2) as X70_pct,
            ROUND(X90, 2) as X90_pct, 
            ROUND(LFS, 2) as LFS, 
            ROUND(HCCYF13, 2) as HCCYF13,
            ROUND(BIAS_5_20, 2) as BIAS_pct
        FROM latest_rows
        WHERE rn = 1
          AND (Z_diff1 > 3.0 OR X70 < 15.0)
          AND LFS >= HCCYF13 * 0.75
        ORDER BY Z_pct DESC;
        """
        return self.con.execute(sql).pl()

    def scan_golden_pit(self) -> pl.DataFrame:
        """
        战术初筛 2：【战略级黄金坑逆向买点】
        条件：CYS34 < -8% (市场超卖) 且 底座未破 且 BIAS 负向超卖
        """
        parquet_glob = self._get_target_parquet_glob()
        sql = f"""
        WITH latest_rows AS (
            SELECT *, 
                   regexp_extract(filename, '([0-9]{{6}})', 1) as clean_code,
                   ROW_NUMBER() OVER(PARTITION BY regexp_extract(filename, '([0-9]{{6}})', 1) ORDER BY Date DESC) as rn
            FROM read_parquet('{parquet_glob}', filename=true, union_by_name=true)
        )
        SELECT 
            clean_code as code, 
            Date as date,
            ROUND(Close, 2) as close, 
            ROUND(CYS34, 2) as CYS34_pct,
            ROUND(LFS, 2) as LFS, 
            ROUND(HCCYF13, 2) as HCCYF13,
            ROUND(BIAS_5_20, 2) as BIAS_pct
        FROM latest_rows
        WHERE rn = 1
          AND CYS34 < -5.0
        ORDER BY CYS34_pct ASC;
        """
        return self.con.execute(sql).pl()

    def scan_super_resonance(self) -> pl.DataFrame:
        """
        战术初筛 3：【超级主升浪·筹码锁定多头金叉榜】
        条件：LFS >= HCCYF13 且 3日控盘斜率 > 0 且 单峰集中 X90 < 20%
        """
        parquet_glob = self._get_target_parquet_glob()
        sql = f"""
        WITH latest_rows AS (
            SELECT *, 
                   regexp_extract(filename, '([0-9]{{6}})', 1) as clean_code,
                   ROW_NUMBER() OVER(PARTITION BY regexp_extract(filename, '([0-9]{{6}})', 1) ORDER BY Date DESC) as rn
            FROM read_parquet('{parquet_glob}', filename=true, union_by_name=true)
        )
        SELECT 
            clean_code as code, 
            Date as date,
            ROUND(Close, 2) as close, 
            ROUND(LFS, 2) as LFS, 
            ROUND(HCCYF13, 2) as HCCYF13,
            ROUND(Slope3_LFS, 2) as Slope3,
            ROUND(X90, 2) as X90_pct,
            ROUND(Z_Profit, 2) as Z_pct
        FROM latest_rows
          AND LFS >= HCCYF13
          AND Slope3_LFS >= 0.0
          AND X90 < 25.0
        ORDER BY LFS DESC;
        """
        return self.con.execute(sql).pl()

    def scan_cpr_superconductor(self) -> pl.DataFrame:
        """
        战术初筛 4: 【超导死锁态与真空跃迁真龙榜 (CPR & BRI 高阶张量)】
        条件: CPR (筹码刚性度) >= 20.0 且 BRI (断层真空指数) >= 30.0 且 LFS 护城河完好
        """
        parquet_glob = self._get_target_parquet_glob()
        sql = f"""
        WITH latest_rows AS (
            SELECT *, 
                   regexp_extract(filename, '([0-9]{{6}})', 1) as clean_code,
                   ROW_NUMBER() OVER(PARTITION BY regexp_extract(filename, '([0-9]{{6}})', 1) ORDER BY Date DESC) as rn
            FROM read_parquet('{parquet_glob}', filename=true, union_by_name=true)
        )
        SELECT 
            clean_code as code, 
            Date as date,
            ROUND(Close, 2) as close, 
            ROUND((LFS * HCCYF13) / (GREATEST(ASR, 0.5) * (1.0 + GREATEST(Turnover, 0.5)/100.0) + 0.001), 2) as CPR,
            ROUND(((100.0 - LEAST(COALESCE(Overlap_Y, 20.0), 99.0)) * Z_Profit) / (GREATEST(X70, 0.5) * GREATEST(ASR, 0.5) + 0.001), 2) as BRI,
            ROUND(LFS, 2) as LFS,
            ROUND(ASR, 2) as ASR,
            ROUND(Z_Profit, 2) as Z_pct,
            ROUND(X70, 2) as X70_pct
        FROM latest_rows
        WHERE rn = 1
          AND LFS >= HCCYF13 * 0.8
        ORDER BY CPR DESC;
        """
        return self.con.execute(sql).pl()


# 全局单例
screener = DuckDBMarketScreener()

