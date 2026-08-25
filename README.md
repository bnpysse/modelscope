# 天眼全息智导系统 V7.0 (ModelScope Edition)

🛰️ **基于 ModelScope 免费金融大模型与移动成本分布 (MCD) 物理场微积分的高吞吐量化战术体系**

---

## 🌟 核心特性

- **高精移动成本分布 (MCD) 数学计算引擎 (`core/quant_chip_engine.py`)**：
  - 基于 NumPy 1500 价格网格自适应积分，从原始 OHLCV + 换手率直接求解 $C_t(P)$ 物理场递推；
  - 毫秒级计算一手五维物理真值指标（$Z$ 获利比、$ASR$ 活动筹码、$X_{70}/X_{90}$ 单峰集中度、$LFS$ 锁定因子、$CYS_{34}$ 成本偏离度、$BIAS_{5/20}$）。
- **ModelScope 官方 Serverless 免费大模型网关 (`core/providers/modelscope_client.py`)**：
  - 内置 **1,800 次/天（90% 安全水位）本地 SQLite 预算硬锁门神**，100% 杜绝扣费风险；
  - 多模型自动级联容灾（`MiniMax M1 80K`、`Qwen 3 Coder 30B`、`Qwen 3 235B`）；
  - 原生支持 `<think>` 思维链提取与三唯一绝对战术军令下发。
- **198 交易日斐波那契战略纵深矩阵 (`core/engine.py`)**：
  - 自动解构 `T+5`, `T+13`, `T+34`, `T+55`, `T+89`, `T+144`, `T+198` 多周期战略演变。
- **DuckDB 全市场毫秒级战术初筛器 (`core/full_market_screener.py`)**：
  - 纯 SQL 秒级初筛【物理真空走廊】与【战略黄金坑】标的。
- **云端持久化与断点续算 (`run_cloud_compute.py` & `deploy_to_notebook.sh`)**：
  - 专为 ModelScope Notebook 1 小时自动休眠机制设计，重启秒级增量恢复。
- **全屏沉浸式全息 HUD 交互面板 (`streamlit_app/app.py`)**：
  - 顶栏 5 合 1 紧凑控制台，全 JS 雷达图与 HUD 实时联动。

---

## 🚀 极速起步

### 1. 本地启动 Streamlit 全息看板

```bash
# 安装依赖
pip install polars numpy duckdb akshare streamlit requests pydantic

# 复制环境变量模板并配置
cp .env.example .env

# 启动交互面板
streamlit run streamlit_app/app.py
```

### 2. ModelScope 云端一键高吞吐计算

在 ModelScope Notebook (PAI-DSW) 终端中运行：

```bash
cd /mnt/workspace
bash deploy_to_notebook.sh
```

---

## 📁 目录结构

```
.
├── core/
│   ├── quant_chip_engine.py       # MCD 筹码物理场微积分递推引擎
│   ├── engine.py                  # Polars 全周期数据管线与斐波那契矩阵
│   ├── signals.py                 # 五维信号判定与 S/A/B/C 战区定性
│   ├── ai_advisor.py              # 参谋部穿透审计与军令下发
│   ├── full_market_screener.py    # DuckDB 全市场秒级战术初筛
│   ├── knowledge/
│   │   └── tactical_bible.py      # 参谋部战术法典与提示词规范
│   └── providers/
│       └── modelscope_client.py   # ModelScope 免费大模型与预算门神
├── streamlit_app/
│   ├── app.py                     # Streamlit 主看板
│   └── components/                # 雷达图与 HUD 交互组件
├── data/                          # 样例数据与标的配置
├── quant_data/                    # 因子库与持久化 Parquet 数据库
├── run_cloud_compute.py           # 云端高吞吐计算主入口
├── deploy_to_notebook.sh          # 云端一键部署脚本
└── tests/                         # 端到端集成测试集
```

---

## 📜 战术裁决与风控纪律

参谋部战术输出严格收敛至三唯一绝对军令：
1. `【继续锁仓装死】`：底座金叉稳固、真空走廊成型、主力绝对锁仓；
2. `【脉冲诱多坚决清仓】`：护城河死叉坍塌、游资倒手派发、防线破位；
3. `【反向T+0对冲】`：BIAS 严重超买脉冲、分时尖头不封板、短线降本。
