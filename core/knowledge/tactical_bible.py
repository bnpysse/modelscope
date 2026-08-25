"""
天眼全息智导系统 V7.0 (ModelScope Edition) — 参谋部量化战术知识库 (Tactical Bible)

收录五维量化指标数学逻辑、物理真值判定边界、战术铁律、斐波那契战略纵深与军令下发规范。
"""
from dataclasses import dataclass
from typing import Any, Dict, List

# ==============================================================================
# 一、 核心量化指标物理真值定义字典 (Five-Dimension Quantitative Matrix)
# ==============================================================================

INDICATOR_DICTIONARY: Dict[str, Dict[str, Any]] = {
    # 维度一：底座与阵地
    "LFS": {
        "name": "筹码锁定因子 (Lock Factor Score)",
        "definition": "衡量下峰筹码在面对震荡甚至下跌时的冻结程度。剥离出不受日内波动影响的固态筹码占比。LFS ∈ [0, 100]，数值越高，筹码锁定越死。",
        "thresholds": {
            "绝对锁死": "LFS > 50 且持续向上扩张",
            "常规博弈": "40 <= LFS <= 50",
            "筹码松动": "LFS < 40 或 Slope_3(LFS) < -3.0"
        }
    },
    "HCCYF13": {
        "name": "13日短线锁定均线 / 护城河",
        "definition": "VMA_13(CYF) 或短周期筹码锁定因子均线。当 VMA(HCCYF13) > LFS 发生死叉时，代表中短期锁仓底座坍塌，触发无条件清仓；金叉或多头运行则护城河稳固。"
    },
    "ASR": {
        "name": "活动筹码浮动比率 (Active Shares Ratio)",
        "definition": "处于当前价格上下各 ±10% 波动区间内的有效活动筹码比例。ASR = ∫[0.9P, 1.1P] f(P) dP。",
        "thresholds": {
            "冰点死锁区": "ASR < 15% (极限个位数 8~12% 最佳，流通浮筹被彻底抽干，零抛压摩擦力)",
            "常规博弈区": "15% <= ASR <= 25%",
            "浮筹泛滥区": "ASR > 25% (散户浮动筹码过重，上行摩擦力大)"
        }
    },
    "CYF66_Raw / VMA(T+55)": {
        "name": "斐波那契跨周期死锁比值",
        "definition": "以 66 日博弈筹码为基底，在 T+55 斐波那契中长期战略纵深周期下，计算其原始值与均线比值。CYF66_Raw > VMA(T+55) 且敞口持续扩大，为超级战略庄家深度死锁标志。"
    },
    # 维度二：空间与抛压
    "Z / Z'": {
        "name": "获利比例与一阶导数",
        "definition": "Z 为当前收盘价以下持仓筹码占总流通盘百分比；Z' 为获利盘单日差分变化 (Z_diff1)。",
        "thresholds": {
            "绝对真空走廊": "Z' > 10 且 X90 < 10 (或 Z' > 15 且 X90 < 15)，微小价格波动带动获利盘大幅跃升，上方毫无阻力层。",
            "庄股雷达豁免": "Z > 95% 且 Turnover < 3%，判定为高度控盘庄股锁仓拉升，豁免流动性惩罚。"
        }
    },
    "X70 / X90": {
        "name": "筹码集中度 (Concentration 70/90)",
        "definition": "全市场 70% 与 90% 筹码的价格跨度分布紧密度。数值越小，筹码越单峰密集。",
        "thresholds": {
            "极限单峰聚拢": "X70 < 10% (筹码高度锁定，主力成本极度一致)",
            "发散磨损": "X70 > 15% (高位换庄或多空分歧)"
        }
    },
    "Y_Overlap": {
        "name": "空间几何重合度",
        "definition": "高位套牢重合度 Y > 60%~70%（散户高位深套躺平装死），低位主力筹码死锁，中间夹层无任何筹码堆积，构成【哑铃型两极冻结真空走廊】。"
    },
    # 维度三：点火与流速
    "PTR": {
        "name": "盘口动能比率 (Price Trend Rate)",
        "definition": "结合盘口买卖挂单速率与成交冲击成本计算的即时点火动能。PTR > 6 且 Main% > 0 判定为主力合力发动进攻。"
    },
    "D_Pos": {
        "name": "活筹换手率指标位置",
        "definition": "D_pos < 50 表明主力强吸/缩量锁仓主升；D_pos > 70 异常飙升伴随分时放量尖头，预警游资倒手派发，严禁追高。"
    },
    "拉升效率 η": {
        "name": "单位换手推升效率",
        "formula": "η = ΔP / Turnover = 涨幅(%) / 换手率(%)",
        "thresholds": {
            "顶级真空推升": "η >= 0.85 (以极低换手打出高涨幅，真龙绝对锁仓)",
            "高磨损推升": "η <= 0.60 (换手剧烈消耗，博弈摩擦力大)",
            "放量滞涨": "η <= 0.40"
        }
    },
    # 维度四：情绪冰点
    "CYS34 / CYS13": {
        "name": "市场盈亏与黄金坑",
        "definition": "全市场 34 天内买入该股的平均持仓盈亏比例。CYS34 < -15% 且底座未死叉（VMA(HCCYF13) <= LFS）触发【黄金坑战略买点】。"
    },
    # 维度五：均线偏离
    "BIAS 5/20": {
        "name": "均线空间离散度与粘合",
        "formula": "BIAS_5/20 = (MA5 - MA20) / MA20 * 100%",
        "thresholds": {
            "均线粘合蓄势": "BIAS_5/20 ∈ [-5%, +5%] (中短期成本高度一致，主升爆发前夜)",
            "脉冲诱多超买": "BIAS_5/20 > +15% (严禁追高，反向 T+0 减仓)",
            "均值回归超卖": "BIAS_5/20 < -10% (短线严重超卖，底仓强锁)"
        }
    }
}

# ==============================================================================
# 二、 参谋部实战三大战术铁律与终极军令
# ==============================================================================

COMMANDS = {
    "LOCK": "【继续锁仓装死】",
    "CLEAR": "【脉冲诱多坚决清仓】",
    "HEDGE_T0": "【反向T+0对冲】",
}

TACTICAL_LAWS = [
    {
        "id": "LAW_PINCER",
        "name": "【黄金反向钳形律】(无阻力真空主升模型)",
        "condition": "CYF在 40~65 黄金区 ∩ ASR < 15 冰点死锁 ∩ X70 < 10%",
        "action": "唯一战术指令：【继续锁仓装死】"
    },
    {
        "id": "LAW_OVERFLOW_BRANCH",
        "name": "【动能溢出态双轨分流定律】",
        "condition": "ΔCYF > +15 时的极端分化判定"
    }
]

COMMANDER_PORTFOLIO = {
    "300475": {"name": "香农芯创", "role": "AI 算力与 HBM 存储分销+封测核心"},
    "300223": {"name": "北京君正", "role": "车规级与工控存储隐形冠军"},
    "300322": {"name": "硕贝德", "role": "天线与射频龙头·小账户死锁资产"},
    "001309": {"name": "德明利", "role": "企业级存储主控与模组龙头"}
}

# ==============================================================================
# 三、 ModelScope 结构化 System Prompt 规范模板
# ==============================================================================

SYSTEM_PROMPT_STAFF_EXPERT = """# Role: A股新质生产力量化战术总参谋部 (Quantitative Tactical General Staff)

## Strict Behavioral Constraints:
1. Tone: Dry, sharp, strictly rational, military-grade discipline. Absolute ban on ambiguous words: "可能", "也许", "大概", "预计", "谨慎看好", "观察一下".
2. Trigger Prefixes:
   - Single intraday snapshot / brief query: MUST start with "天眼静默，常规穿透。"
   - Full CSV dataset / multi-cycle review / deep strategic depth: MUST start with "全景引擎启动。"
3. Terminal Decision Discipline:
   - The report MUST conclude with EXACTLY ONE explicit tactical verdict from the following set:
     【继续锁仓装死】 OR 【脉冲诱多坚决清仓】 OR 【反向T+0对冲】

## Quantitative Matrix (Five-Dimension Holographic Architecture):
- 维度一 (底座与阵地): LFS (锁定因子), HCCYF13 (13日护城河), ASR (活动筹码). 铁律: VMA(HCCYF13) > LFS 发生死叉为底座坍塌清仓信号; LFS ↑ + ASR ↓ 为暴力锁仓剪刀差; Slope3(LFS) > +2.0 为控盘加速度爆发.
- 维度二 (空间与抛压): Z (获利比), Z' (日变化), X70/X90 (集中度), Y (空间重合度). 铁律: Z' > 10 且 X90 < 10 构成物理真空走廊; Y > 60% 且高位深套构成哑铃型两极冻结; Z > 95% 且 Turnover < 3% 触发高控盘庄股锁仓拉升豁免.
- 维度三 (点火与流速): PTR (动能比率), Main% (主力占比), Dare% (游资占比), D_pos (活筹位置). 铁律: PTR > 6 且 Main% > 0 为点火成立; D_pos < 50 为主力强吸锁仓; D_pos > 70 伴随放量尖头为游资倒手派发预警.
- 维度四 (情绪冰点与黄金坑): CYS34 / CYS13 (市场盈亏). 铁律: CYS34 < -15% 且底座未破为战略黄金坑; Y > 60% 且 Turnover < 3.5% 为极限装死区.
- 维度五 (均线偏离与均值回归): BIAS_5_20 = (MA5 - MA20)/MA20 * 100%. 铁律: BIAS ∈ [-5%, +5%] 为均线完全粘合蓄势区; BIAS > +15% 为脉冲诱多超买; BIAS < -10% 为均值回归超卖.

## Strategic Asset Portfolio (统帅战略兵力部署档案):
- 300475 香农芯创: AI 算力与 HBM 存储战略核心，SK海力士中国特级分销+海普先进封测，基石资本运作平台.
- 300223 北京君正: 车规与工控存储全球隐形冠军，自研 CPU/NPU 存算一体自主可控.
- 300322 硕贝德: 小账户死锁资产，天线与射频龙头，极端筹码单峰锁定.
- 001309 德明利: 企业级存储主控与模组龙头.
"""
