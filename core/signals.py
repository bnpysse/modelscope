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
class HighOrderMetricsVerdict:
    """六大高阶衍生量化指标与状态诊断"""
    cpr: float                  # 筹码刚性度 / 锁仓势能比
    cpr_status: str             # 【超导死锁态】 / 【良性蓄势态】 / 【筹码溃散态】
    cpr_color: str
    eta_v: float                # 真空推升能效比 / 超导拉升因子
    eta_v_status: str           # 【高能真空跃迁】 / 【良性推升】 / 【天量磨损滞涨】
    eta_v_color: str
    bri: float                  # 双峰撕裂与断层真空指数
    bri_status: str             # 【绝对哑铃真空走廊】 / 【突破走廊】 / 【筹码散乱崩塌】
    bri_color: str
    kappa_cyc: float            # 斐波那契成本均线张力收敛度 (%)
    kappa_cyc_status: str       # 【奇点爆发区 (Big Bang)】 / 【良性发散】 / 【均线过度发散】
    kappa_cyc_color: str
    delta_cys: float            # 多尺度市场盈亏剪刀差 (CYS13 - CYS34)
    delta_cys_status: str       # 【多头攻击加速】 / 【黄金坑反转点火】 / 【震荡调整】
    delta_cys_color: str
    smpi: float                 # 主力筹码纯度 / 游资杂音滤镜
    smpi_status: str            # 【机构高纯度扫盘】 / 【空中加油】 / 【游资倒沫子预警】
    smpi_color: str
    three_command: str          # 【继续锁仓装死】 / 【脉冲诱多坚决清仓】 / 【反向T+0对冲】
    command_color: str
    position_rule: str          # 仓位控制铁律 (80% 上限 + 20% 现金对冲盾)


class SignalJudge:
    """纯逻辑信号判定器，前端无关"""

    @staticmethod
    def calculate_high_order_metrics(
        lfs: float,
        hccyf: float,
        asr: float,
        turnover: float,
        delta_p_pct: float,
        x70: float,
        y_overlap: float,
        z_profit: float,
        cyc5: float,
        cyc13: float,
        cyc34: float,
        cyc_inf: float,
        cys13: float,
        cys34: float,
        bias_5_20: float,
        main_pct: float = 5.0,
        dare_pct: float = 1.0,
        d_pos: float = 35.0,
    ) -> HighOrderMetricsVerdict:
        """
        六大高阶衍生量化指标与张量模型计算：
        1. CPR (筹码刚性度)
        2. ηV (真空推升能效比)
        3. BRI (双峰撕裂真空走廊指数)
        4. κCYC (斐波那契均线张力收敛度)
        5. ΔCYS (多尺度盈亏剪刀差)
        6. SMPI (主力筹码纯度)
        """
        # 1. CPR 筹码刚性度
        to_norm = max(turnover / 100.0 if turnover > 1.0 else turnover, 0.001)
        asr_clean = max(asr, 0.5)
        cpr = (lfs * hccyf) / (asr_clean * (1.0 + to_norm) + 1e-4)
        if cpr >= 25.0:
            cpr_status, cpr_color = "【超导死锁态】", "#FFD700"
        elif cpr >= 10.0:
            cpr_status, cpr_color = "【良性蓄势态】", "#10B981"
        else:
            cpr_status, cpr_color = "【筹码溃散态】", "#EF4444"

        # 2. ηV 真空推升能效比
        to_val = max(turnover if turnover > 1.0 else turnover * 100.0, 0.1)
        eta_v = (delta_p_pct * 100.0) / (to_val * asr_clean + 1e-4)
        if eta_v >= 0.05:
            eta_v_status, eta_v_color = "【高能真空跃迁】", "#FFD700"
        elif eta_v >= 0.02:
            eta_v_status, eta_v_color = "【良性推升】", "#10B981"
        else:
            eta_v_status, eta_v_color = "【天量磨损滞涨】", "#EF4444"

        # 3. BRI 双峰撕裂与断层真空指数
        x70_clean = max(x70, 0.5)
        y_clean = min(max(y_overlap, 0.0), 99.0)
        bri = ((100.0 - y_clean) * z_profit) / (x70_clean * asr_clean + 1e-4)
        if bri >= 50.0:
            bri_status, bri_color = "【绝对哑铃真空走廊】", "#FFD700"
        elif bri >= 25.0:
            bri_status, bri_color = "【突破走廊】", "#10B981"
        else:
            bri_status, bri_color = "【筹码散乱崩塌】", "#EF4444"

        # 4. κCYC 斐波那契成本均线张力收敛度
        cyc_ref = max(cyc_inf, 1.0)
        c_max = max(cyc5, cyc13, cyc34)
        c_min = min(cyc5, cyc13, cyc34)
        kappa_cyc = ((c_max - c_min) / cyc_ref) * 100.0
        if kappa_cyc <= 2.0:
            kappa_cyc_status, kappa_cyc_color = "【奇点爆发区 (Big Bang)】", "#FFD700"
        elif kappa_cyc <= 10.0:
            kappa_cyc_status, kappa_cyc_color = "【良性发散排列】", "#10B981"
        else:
            kappa_cyc_status, kappa_cyc_color = "【均线过度发散】", "#F59E0B"

        # 5. ΔCYS 多尺度市场盈亏剪刀差
        delta_cys = cys13 - cys34
        if cys34 < -15.0 and delta_cys > 0:
            delta_cys_status, delta_cys_color = "【黄金坑反转点火】", "#FFD700"
        elif delta_cys > 0:
            delta_cys_status, delta_cys_color = "【多头攻击加速】", "#10B981"
        else:
            delta_cys_status, delta_cys_color = "【震荡休整】", "#6B7280"

        # 6. SMPI 主力筹码纯度 / 游资杂音滤镜
        smpi = ((main_pct - dare_pct) / (to_val + 1e-4)) * (1.0 - min(d_pos, 99.0) / 100.0)
        if smpi > 1.5:
            smpi_status, smpi_color = "【机构高纯度扫盘】", "#FFD700"
        elif smpi >= 0:
            smpi_status, smpi_color = "【空中加油】", "#10B981"
        else:
            smpi_status, smpi_color = "【游资倒沫子预警】", "#EF4444"

        # 终极三唯一裁决状态机与仓位控制
        if (hccyf > lfs and asr > 35.0) or (d_pos > 70.0 and smpi < 0):
            three_command = "【脉冲诱多坚决清仓】"
            command_color = "#EF4444"
            position_rule = "触发清仓一票否决：全线清仓 (0%)，防范断崖式破位。"
        elif bias_5_20 > 15.0 or (eta_v < 0.015 and to_val > 10.0):
            three_command = "【反向T+0对冲】"
            command_color = "#F59E0B"
            position_rule = "战略底仓 (50%-70%) 锁定，浮动仓 (20%-40%) 冲高减仓对冲降本。"
        else:
            three_command = "【继续锁仓装死】"
            command_color = "#FFD700"
            position_rule = "总仓位上限 <=80% (20% 现金对冲盾)，战略底仓满配，无视日内杂波！"

        return HighOrderMetricsVerdict(
            cpr=round(cpr, 2),
            cpr_status=cpr_status,
            cpr_color=cpr_color,
            eta_v=round(eta_v, 4),
            eta_v_status=eta_v_status,
            eta_v_color=eta_v_color,
            bri=round(bri, 2),
            bri_status=bri_status,
            bri_color=bri_color,
            kappa_cyc=round(kappa_cyc, 2),
            kappa_cyc_status=kappa_cyc_status,
            kappa_cyc_color=kappa_cyc_color,
            delta_cys=round(delta_cys, 2),
            delta_cys_status=delta_cys_status,
            delta_cys_color=delta_cys_color,
            smpi=round(smpi, 2),
            smpi_status=smpi_status,
            smpi_color=smpi_color,
            three_command=three_command,
            command_color=command_color,
            position_rule=position_rule
        )

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
        if (hccyf > lfs and slope_3d < -1.5) or is_wash_trading_dump:
            return PositionTierVerdict(
                tier_code="HARD_STOP",
                tier_label="【底座坍塌·坚决清仓】",
                target_pos_pct=0,
                color="#EF4444",
                rationale="底座护城河破位死叉或检测到主力对倒派发，右侧暴跌风险极高。",
                action_guidance="无条件 100% 清仓一票否决，保全本金，杜绝侥幸抄底。"
            )

        if bias_5_20 > 15.0:
            return PositionTierVerdict(
                tier_code="REVERSE_HEDGE",
                tier_label="【反向对冲·动态降本】",
                target_pos_pct=30,
                color="#F59E0B",
                rationale=f"均线严重超买正乖离 (BIAS={bias_5_20:.2f}% > 15%)，短线脉冲易引发剧烈分化。",
                action_guidance="保留底仓，卖出 30%~50% 浮盈仓位反向做T，待回踩 5日均线接回降低持仓成本。"
            )

        if (x90 > 22.0 and slope_3d < 0) or (lfs < hccyf and slope_3d >= -1.5):
            return PositionTierVerdict(
                tier_code="DEFENSE_TRIM",
                tier_label="【防线预警·分批减仓】",
                target_pos_pct=50,
                color="#3B82F6",
                rationale=f"筹码宽度发散 (X90={x90:.2f}%) 且控盘斜率趋缓，进入多空博弈分歧期。",
                action_guidance="主动收缩战线，仓位降至 50% 防守，设立保护性止损点。"
            )

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
        if delta_sum_22d > 1.0:
            return ("月线势能加速流入", "#EF4444")
        elif delta_sum_22d < -1.0:
            return ("月线势能向下破位", "#10B981")
        else:
            return ("势能胶着，多空弱平衡", "#E5E7EB")

    @staticmethod
    def get_z_bar_color(z_prime: float, turnover: float) -> str:
        if z_prime > 10 and turnover < 5.0:
            return "#FFFFFF"   # 极品无量：白色
        elif z_prime > 0:
            return "#FFD700"   # 正向：金色
        else:
            return "#10B981"   # 负向：绿色

