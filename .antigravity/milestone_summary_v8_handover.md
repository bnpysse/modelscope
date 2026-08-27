# 📜 天衍五维量化大模型系统 · 第八阶段（Phase 8）交接与战备备忘录
> **文档版本**: v8.0-Handover  
> **归档日期**: 2026-08-27  
> **面向对象**: 接任 Agent / 核心开发者 / 统帅  

---

## 🎯 一、 战略架构与系统当前全貌 (Current System State)

本项目为**天衍五维筹码时空全息量化超脑 (Omni-Tactical FinLLM HUD)**，打通了“**连续微积分时空场数学底座 ➔ A股全市场 DuckDB 毫秒级因子流水线 ➔ AMD 192GB GPU 本地大模型 LoRA 强化训练 ➔ Streamlit 创空间全息战斗大屏**”的工业级闭环。

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. 🔬 数理底座 (Mathematical Physics Engine)                                    │
│    • 连续高斯卷积时空场微积分 ∂P(x,t)/∂t                                        │
│    • 主力增仓与机构拆单穿透反解方程 Main% = α·∂LFS/∂t + β·Turnover·[(C-V)/(H-L)]·(1-ASR)│
│    • 六大高阶衍生张量: CPR(筹码刚性), ηV(真空推升能效), BRI(断层真空走廊),       │
│      κCYC(跨周期协整), ΔCYS(偏离斜率), SMPI(主力操盘意图)                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 2. ⚡ 云端超算与大模型训练 (ModelScope DSW - AMD ROCm 192GB VRAM)                 │
│    • 存储分层: /mnt/workspace (100GB 持久化NAS) + /root (560GB 高速NVMe)         │
│    • 容灾机制: 自动滚动修剪 (仅留最新2个) + 实时镜像防关机双保险                 │
│    • Qwen2.5-7B LoRA: 已达 Step 3231 (51,696 题解, Loss 0.0000)                │
│    • 度小满轩辕-13B LoRA: 已达 Step 1191 (19,056 题解, Loss 0.0000)              │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 3. 🎨 全息战斗大屏与 AI 参谋部 (Streamlit HUD)                                  │
│    • 控制总台: 图一(标的/周期/维五)与图二(AI大模型/召唤/配额)完整融合             │
│    • 视觉与释义: 紧凑高亮 AI 审计排版 + 全指标 KaTeX 高阶微积分悬浮释义           │
│    • 生产发布: 已部署至 ModelScope Studio (http://ty.donglida.com)              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 💾 二、 云端环境与关键文件路径 (DSW Storage & Path Registry)

### 1. 双层存储架构铁律（必读）：
* **持久化盘 `/mnt/workspace` (配额 100GB)**：用于存放模型权重、代码库与持久化数据集。严禁堆积中间 Checkpoint！
* **本地高速盘 `/root` (容量 560GB，读写 1.9GB/s)**：用于运行训练输出、临时缓存与高频写入。

### 2. 关键路径清单：
| 资源类别 | 物理路径 | 作用描述 |
| :--- | :--- | :--- |
| **Qwen-7B Checkpoint** | `/mnt/workspace/models/omni-tactical-qwen7b-lora/` | 已安全落盘最新 `checkpoint-3200` |
| **XuanYuan-13B Checkpoint** | `/mnt/workspace/models/omni-tactical-xuanyuan13b-lora/` | 已安全落盘最新 `checkpoint-1150` |
| **基础基座模型** | `/mnt/workspace/models/models/` | 包含 Qwen2.5-7B 与 XuanYuan-13B 原生权重 |
| **训练样本集** | `/mnt/workspace/quant_data/omni_finllm_sft_train.jsonl` | 102,280 条高精量化物理场思维链 |
| **GPU 训练脚本** | `scripts/gpu_rocm_lora_train.py` | 专为 AMD 192GB 优化，支持 `--resume` 与自动瘦身 |
| **Streamlit 主入口** | `app.py` & `streamlit_app/app.py` | 全息大屏主程序 |
| **创空间部署脚本** | `scripts/deploy_to_studio.py` | 一键同步部署至 ModelScope Studio |

---

## 🚀 三、 接任者快速启动与操作指南 (Quickstart Guide for Successor)

### 1. DSW 实例重新开机后如何接力训练：
当统帅在 ModelScope 启动 DSW 实例后：
```bash
# 1. 建立 cpolar SSH 通道 (统帅提供端口，如 11303)
# 2. 检查持久化 Checkpoint:
ls -lh /mnt/workspace/models/omni-tactical-qwen7b-lora/
ls -lh /mnt/workspace/models/omni-tactical-xuanyuan13b-lora/

# 3. 极速一键接力恢复双模型并发训练:
nohup python3 /root/quant_engine/scripts/gpu_rocm_lora_train.py --model qwen7b --resume > /root/quant_data/qwen7b_train_resume.log 2>&1 &
nohup python3 /root/quant_engine/scripts/gpu_rocm_lora_train.py --model xuanyuan13b --resume > /root/quant_data/xuanyuan13b_train_resume.log 2>&1 &

# 4. 查看实时监控:
/usr/bin/rocm-smi
tail -f /root/quant_data/qwen7b_gpu_training_progress.log
```

---

## 📋 四、 下一阶段任务清单 (Next Phase Roadmap)

1. **第一阶段模型训练收口**：
   - 待两模型跑完第一轮 Epoch（总 Step 19,176），执行 LoRA 权重与基座合并（Merge Adapter），导出 `Tianyan-Qwen7B` 与 `Tianyan-XuanYuan13B`；
2. **第二阶段数据合成 (Stage 2 SFT v2)**：
   - 合成融入**六大高阶衍生指标** ($CPR, \eta_V, BRI, \kappa_{CYC}, \Delta CYS, SMPI$) 的 `omni_finllm_sft_v2.jsonl`；
   - 引入 DPO 偏好对齐，强化“超导死锁与真空走廊”的识别精度；
3. **vLLM 私有化微服务上线**：
   - 将合并后的模型通过 vLLM 在 192GB GPU 上部署为 OpenAI 兼容的 API 服务，供 Streamlit 大屏实时调用。
