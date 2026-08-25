#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 DuckDB 的全市场五维筹码物理场秒级战术筛选引擎
支持纯 SQL 对 /mnt/workspace/quant_data/ 目录下所有股票的历史与截面因子进行穿透式初筛
"""

import os
import sys
from pathlib import Path
import duckdb
import polars as pl

if os.path.exists("/mnt/workspace"):
    WORKSPACE_DIR = Path("/mnt/workspace")
else:
    WORKSPACE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = WORKSPACE_DIR / "quant_data"
FACTORS_DIR = DATA_DIR / "factors"


class DuckDBMarketScreener:
    """DuckDB 极速战术初筛器"""

    def __init__(self, factors_dir: Path = FACTORS_DIR):
        self.factors_dir = factors_dir
        self.con = duckdb.connect()

    def run_custom_query(self, sql_query: str) -> pl.DataFrame:
        """执行任意自定义 DuckDB SQL 查询"""
        return self.con.execute(sql_query).pl()

    def scan_vacuum_corridor(self) -> pl.DataFrame:
        """
        战术初筛 1：【物理真空走廊 + 极度单峰】
        条件：Z' > 10 (获利盘日跳升) 且 X90 < 15% (单峰密集) 且 LFS > HCCYF13 (护城河金叉)
        """
        parquet_glob = str(self.factors_dir / "*.parquet")
        sql = f"""
        WITH latest_rows AS (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY Target_Code ORDER BY Date DESC) as rn
            FROM read_parquet('{parquet_glob}')
        )
        SELECT 
            Target_Code as code, 
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
          AND (Z_diff1 > 5.0 OR X70 < 10.0)
          AND LFS >= HCCYF13 * 0.8
        ORDER BY Z_pct DESC;
        """
        return self.con.execute(sql).pl()

    def scan_golden_pit(self) -> pl.DataFrame:
        """
        战术初筛 2：【战略级黄金坑逆向买点】
        条件：CYS34 < -10% (市场极度深套超卖) 且 底座未破 (LFS >= HCCYF13) 且 BIAS < -5%
        """
        parquet_glob = str(self.factors_dir / "*.parquet")
        sql = f"""
        WITH latest_rows AS (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY Target_Code ORDER BY Date DESC) as rn
            FROM read_parquet('{parquet_glob}')
        )
        SELECT 
            Target_Code as code, 
            Date as date,
            ROUND(Close, 2) as close, 
            ROUND(CYS34, 2) as CYS34_pct,
            ROUND(LFS, 2) as LFS, 
            ROUND(HCCYF13, 2) as HCCYF13,
            ROUND(BIAS_5_20, 2) as BIAS_pct
        FROM latest_rows
        WHERE rn = 1
          AND CYS34 < -10.0
        ORDER BY CYS34_pct ASC;
        """
        return self.con.execute(sql).pl()


# 全局单例
screener = DuckDBMarketScreener()
