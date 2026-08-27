"""
天眼全息智导系统 V7.0 (ModelScope Edition) — 五维信号与动态仓位判定引擎

提供纯逻辑判定层：
1. 4 级动态仓位分层管理 (100% 满配锁仓 / 50% 防线减仓 / 30% 反向对冲 / 0% 底座清仓)
2. 战区定性 (S/A/B/C) 与动能等级判定
3. 微观订单流与主力对倒异常识别
"""
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class ZoneVerdict:
    """战区定性结果"""
    zone_code: str    # S / A / B / C
    zone_label: str   # 中文描述
    color: str        # 主题色
    command: str      # 战术裁决


@dataclass(frozen=True)
class PositionTierVerdict:
    """4 级动态仓位分层裁决"""
    tier_code: str          # FULL_LOCK / DEFENSE_TRIM / REVERSE_HEDGE / HARD_STOP
    tier_label: str         # 中文军令
    target_pos_pct: int     # 建议仓位 (100 / 50 / 30 / 0)
    color: str              # 徽章主题色
    rationale: str          # 核心判定逻辑
    action_guidance: str    # 具体实战操作指令


@dataclass(frozen=True)
class MomentumTier:
    """动能等级 (维一专用)"""
    tier_label: str
    tier_color: str


class SignalJudge:
    """纯逻辑信号判定器，前端无关"""

    @staticmethod
    def judge_position_tier(
        lfs: float,
        hccyf: float,
        scissor: float,
        slope_3d: float,
        bias_5_20: float,
        x90: float = 15.0,
        z_profit: float = 50.0,
        cys34: float = 0.0,
        is_wash_trading_dump: bool = False
    ) -> PositionTierVerdict:
        """
        4 级动态仓位分层判定矩阵：
        1. 【底座坍塌·坚决清仓】(0%): HCCYF13 > LFS 死叉 或 对倒出货 或 跌破防线
        2. 【反向对冲·动态降本】(30%): BIAS_5_20 > 15% 严重超买脉冲
        3. 【防线预警·分批减仓】(50%): 单峰松动 (X90 > 22%) 且 动能衰减 (Slope3 < 0)
        4. 【满配主升·绝对锁仓】(100%): 底座金叉 (LFS >= HCCYF13) 且 乖离合理
        """
        # 1. 触发清仓一票否决
        if (hccyf > lfs and slope_3d < -1.5) or is_wash_trading_dump:
            return PositionTierVerdict(
                tier_code="HARD_STOP",
                tier_label="【底座坍塌·坚决清仓】",
                target_pos_pct=0,
                color="#EF4444",
                rationale="底座护城河破位死叉或检测到主力对倒派发，右侧暴跌风险极高。",
                action_guidance="无条件 100% 清仓一票否决，保全本金，杜绝侥幸抄底。"
            )

        # 2. 触发短线超买反向做 T
        if bias_5_20 > 15.0:
            return PositionTierVerdict(
                tier_code="REVERSE_HEDGE",
                tier_label="【反向对冲·动态降本】",
                target_pos_pct=30,
                color="#F59E0B",
                rationale=f"均线严重超买正乖离 (BIAS={bias_5_20:.2f}% > 15%)，短线脉冲易引发剧烈分化。",
                action_guidance="保留底仓，卖出 30%~50% 浮盈仓位反向做T，待回踩 5日均线接回降低持仓成本。"
            )

        # 3. 触发防线松动减仓防守
        if (x90 > 22.0 and slope_3d < 0) or (lfs < hccyf and slope_3d >= -1.5):
            return PositionTierVerdict(
                tier_code="DEFENSE_TRIM",
                tier_label="【防线预警·分批减仓】",
                target_pos_pct=50,
                color="#3B82F6",
                rationale=f"筹码宽度发散 (X90={x90:.2f}%) 且控盘斜率趋缓，进入多空博弈分歧期。",
                action_guidance="主动收缩战线，仓位降至 50% 防守，设立保护性止损点。"
            )

        # 4. 满配主升绝对锁仓
        return PositionTierVerdict(
            tier_code="FULL_LOCK",
            tier_label="【满配主升·绝对锁仓】",
            target_pos_pct=100,
            color="#FFD700",
            rationale=f"量化底座坚实 (LFS={lfs:.2f} >= HCCYF={hccyf:.2f})，真空走廊通畅，主力高度控盘。",
            action_guidance="保持 80%~100% 满配仓位不动如山，允许日内震荡洗盘，绝不轻易交出廉价筹码。"
        )

    @staticmethod
    def judge_zone(scissor: float, slope_3d: float) -> ZoneVerdict:
        """
        基于剪刀差和3日斜率判定战区等级。

        S档 (Scissor > 20)：绝对护城河
        A档 (Scissor > 0, 斜率 > 0)：常规博弈
        B档 (Scissor > 0, 斜率 ≤ 0)：防线松动
        C档 (Scissor ≤ 0)：极寒死叉
        """
        if scissor > 20:
            return ZoneVerdict(
                zone_code="S",
                zone_label="★ S档：绝对护城河 (满配主升)",
                color="#FFD700",
                command="战术裁决：允许常规洗盘。防线极厚，绝不轻易交出底仓。",
            )
        elif scissor > 0:
            if slope_3d > 0:
                return ZoneVerdict(
                    zone_code="A",
                    zone_label="■ A档：常规博弈区 (点火上攻)",
                    color="#10B981",
                    command="战术裁决：动能健康。盯紧流速，跌破零轴前坚定持有。",
                )
            else:
                return ZoneVerdict(
                    zone_code="B",
                    zone_label="◆ B档：防线松动区 (滞涨预警)",
                    color="#F59E0B",
                    command="战术裁决：动能衰减。内部筹码松动，随时准备右侧止盈。",
                )
        else:
            return ZoneVerdict(
                zone_code="C",
                zone_label="✖ C档：极寒死叉区 (无条件清算)",
                color="#EF4444",
                command="战术裁决：防线崩塌，右侧杀跌风险极高！立刻清仓！",
            )

    @staticmethod
    def judge_momentum(slope_3d: float) -> MomentumTier:
        """维一动能等级判定 (VMA 3日斜率)"""
        if slope_3d > 2.0:
            return MomentumTier("★ 点火级 (绝对主升)", "#FFD700")
        elif slope_3d > 0:
            return MomentumTier("■ 滞涨级 (动能衰减)", "#10B981")
        elif slope_3d > -2.0:
            return MomentumTier("◆ 松动级 (筹码外泄)", "#F59E0B")
        else:
            return MomentumTier("✖ 崩塌级 (恐慌抛售)", "#EF4444")

    @staticmethod
    def judge_z_quality(z_prime: float, turnover: float) -> str:
        """Z' 动能质量判定"""
        if z_prime > 10 and turnover < 5.0:
            return "极品无量穿透"
        elif z_prime > 10:
            return "真空爆破"
        elif z_prime > 0:
            return "正向动能"
        else:
            return "负向压制"

    @staticmethod
    def judge_fund_momentum(delta_sum_22d: float) -> tuple[str, str]:
        """月线资金势能判定 → (描述, 颜色)"""
        if delta_sum_22d > 1.0:
            return ("月线势能加速流入", "#EF4444")
        elif delta_sum_22d < -1.0:
            return ("月线势能向下破位", "#10B981")
        else:
            return ("势能胶着，多空弱平衡", "#E5E7EB")

    @staticmethod
    def get_z_bar_color(z_prime: float, turnover: float) -> str:
        """Z' 柱状图着色逻辑"""
        if z_prime > 10 and turnover < 5.0:
            return "#FFFFFF"   # 极品无量：白色
        elif z_prime > 0:
            return "#FFD700"   # 正向：金色
        else:
            return "#10B981"   # 负向：绿色
