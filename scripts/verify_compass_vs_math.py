import sys
from pathlib import Path
import polars as pl
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.quant_chip_engine import QuantChipMathEngine

COMPASS_CSV = "/Users/woodman/dev/python/Rapid/stock.csv"

def compare_stock(code="001309"):
    print(f"\n" + "=" * 80)
    print(f"📊 开始科学验算: 标的 [{code}] 指南针手工抓取真值 VS 天衍物理微分方程推导值")
    print("=" * 80)
    
    # 1. 读取指南针 CSV
    df = pl.read_csv(COMPASS_CSV)
    sub = df.filter(pl.col("Target_Code").cast(pl.Utf8).str.zfill(6) == str(code).zfill(6)).sort("Date")
    if sub.is_empty():
        print(f"❌ 未在指南针数据中找到标的: {code}")
        return
        
    print(f"✓ 成功载入指南针真实历史序列: 共 {len(sub)} 个交易日 (自 {sub['Date'].min()} 至 {sub['Date'].max()})")
    
    # 2. 仅提取基础行情输入微积分引擎
    ohlcv_input = sub.select(["Date", "Open", "High", "Low", "Close", "Turnover"])
    engine = QuantChipMathEngine(price_bins=1500)
    computed = engine.compute_mcd_series(ohlcv_input)
    
    # 3. 跨周期误差统计
    compass_pdf = sub.to_pandas()
    math_pdf = computed.to_pandas()
    
    # 重点对比指标: Z (获利比例), ASR (活动筹码), LFS (锁定因子), CYS34 (成本偏离)
    metrics = [
        ("Z (获利盘比例)", "Z_Profit", "Z"),
        ("ASR (浮动活动筹码)", "ASR", "ASR"),
        ("CYS34 (成本偏离度)", "CYS34", "CYS34"),
        ("LFS (主力锁定因子)", "LFS", "LFS"),
    ]
    
    results = []
    for label, c_col, m_col in metrics:
        if c_col not in compass_pdf.columns or m_col not in math_pdf.columns:
            continue
        c_vals = compass_pdf[c_col].to_numpy(dtype=float)
        m_vals = math_pdf[m_col].to_numpy(dtype=float)
        
        # 处理有效值
        mask = ~(np.isnan(c_vals) | np.isnan(m_vals))
        c_valid = c_vals[mask]
        m_valid = m_vals[mask]
        
        # 1) 全样本点对点绝对误差均值 (MAE) 与 相关系数 r
        corr = np.corrcoef(c_valid, m_valid)[0, 1] if len(c_valid) > 1 else 0
        mae_all = np.mean(np.abs(c_valid - m_valid))
        
        # 2) 最近 5 日 (短线) 均值
        c_5 = np.mean(c_valid[-5:])
        m_5 = np.mean(m_valid[-5:])
        diff_5 = abs(c_5 - m_5)
        
        # 3) 最近 132 日 (半年期) 均值
        span = min(132, len(c_valid))
        c_132 = np.mean(c_valid[-span:])
        m_132 = np.mean(m_valid[-span:])
        diff_132 = abs(c_132 - m_132)
        
        results.append({
            "指标名称": label,
            "皮尔逊相关性 r": f"{corr:.3f}",
            "日度 MAE 误差": f"{mae_all:.2f}",
            "5日指南针均值": f"{c_5:.2f}",
            "5日天衍微分均值": f"{m_5:.2f}",
            "5日短线偏差": f"{diff_5:.2f}",
            "132日指南针均值": f"{c_132:.2f}",
            "132日天衍微分均值": f"{m_132:.2f}",
            "132日半年期偏差": f"{diff_132:.2f}",
        })
        
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
    
    # 打印昨日 (2026-09-02) 两个体系的最新切片数值
    last_c = compass_pdf.iloc[-1]
    last_m = math_pdf.iloc[-1]
    print(f"\n🎯 最新一日 ({last_c['Date']}) 战备切片数值直接对照:")
    print(f"   ● 收盘价 Close: 指南针={last_c['Close']} | 天衍={last_m['Close']}")
    print(f"   ● 获利盘 Z:     指南针={last_c.get('Z_Profit', 0):.2f}% | 天衍={last_m.get('Z', 0):.2f}%")
    print(f"   ● 活动筹码 ASR: 指南针={last_c.get('ASR', 0):.2f} | 天衍={last_m.get('ASR', 0):.2f}")
    print(f"   ● 成本偏离 CYS: 指南针={last_c.get('CYS34', 0):.2f}% | 天衍={last_m.get('CYS34', 0):.2f}%")
    print(f"   ● 锁定因子 LFS: 指南针={last_c.get('LFS', 0):.2f} | 天衍={last_m.get('LFS', 0):.2f}")

if __name__ == "__main__":
    compare_stock("001309")
    compare_stock("688525")
