# 🛰️ 天衍量化系统 · 核心运行规则与工程实战手册 (Antigravity System Playbook)

> **版本**：v7.0 (2026-08-27)  
> **核心定位**：全市场 5,115 只股票微积分物理场 + 192GB GPU 大模型 LoRA 双驱并发训练 + 创空间 7.0 全息量化看板

---

## 📌 一、核心基础设施与连接规范

### 1. 阿里云 ModelScope DSW (算力中心)
- **推荐算力规格**：`方式三 AMD GPU环境（8核 CPU / 200GB 内存 / 192GB 显存 / 100小时免费）`
- **底层架构**：AMD Instinct MI300X 架构，支持 PyTorch ROCm 与 `bfloat16` 原生硬件加速。
- **持久化存储**：`/mnt/workspace` 与 `/mnt/data` 挂载至共享 NAS（1.0 PB 空间），数据与检查点永久保留。

### 2. 隧道与 SSH 连接工作流
1. **启动隧道**：在 DSW Web 终端执行 `bash /mnt/workspace/start_tunnel.sh`。
2. **提取公网地址**：终端打印 `tcp://10.tcp.cpolar.top:XXXXX -> tcp://127.0.0.1:22`。
3. **免密连接**：Mac 本地 `~/.ssh/id_rsa.pub` 已预置在 DSW 的 `~/.ssh/authorized_keys` 中，直接 `ssh -p XXXXX root@10.tcp.cpolar.top` 即可无密接入。
4. **Known Hosts 变更**：若提示 Host identification changed，执行 `ssh-keygen -R "[10.tcp.cpolar.top]:XXXXX"` 即可。

### 3. 三重立体保活体系 (杜绝闲置停机)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🛡️ 第一重：【底层 REST API 探针】(后台常驻)                                │
│    • /tmp/dsw_vscode_activity_simulator.py 每 30 秒向 127.0.0.1:8088 发送 API │
│      请求，直接重置 DSW 系统的 last_activity 闲置时间戳。                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🛡️ 第二重：【前端 Jupyter 单元格心跳】(keepalive.ipynb)                       │
│    • 在 VSCode 打开 jupyter_keepalive.ipynb 点击运行，维持 WebSocket 活跃。   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🛡️ 第三重：【杭州小主机 7x24 小时外部 Pinger】                               │
│    • 阿里云 ECS (root@erth.donglida.xyz) crontab 每 2 分钟发起 SSH 探针。   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 二、大模型微调训练体系 (SFT + LoRA)

### 1. 数据集规范
- **文件路径**：`/mnt/workspace/quant_data/omni_finllm_sft_train.jsonl` (542.28 MB)
- **样本容量**：102,280 条全市场 5,115 只股票微积分物理场标准思维链题解（CoT）。
- **字段规范**：包含 `system`, `messages` (`user` 包含 28 项微观物理因子，`assistant` 输出战术定性、支撑阻力与定量操盘军令）。

### 2. 双大模型同卡并行训练架构 (192GB 显存)
- **调度脚本**：`/mnt/workspace/quant_engine/scripts/gpu_rocm_lora_train.py`
- **并发状态**：
  1. **Qwen2.5-7B-Instruct**：`--model qwen7b`（占用显存 ~17.5 GB，5 秒/步）。
  2. **度小满轩辕-13B**：`--model xuanyuan13b`（占用显存 ~30.8 GB，15 秒/步）。
  3. **显存总负荷**：~103.89 GB / 191.69 GB（富余近 90 GB 充裕安全空间）。

### 3. 检查点（Checkpoint）高频存盘策略
- **早期阶段点**：`[Step 10, Step 25, Step 50, Step 100, Step 150, Step 200, ...]`
- **存储路径**：
  - Qwen2.5：`/mnt/workspace/models/omni-tactical-qwen7b-lora/checkpoint-{step}`
  - 度小满 13B：`/mnt/workspace/models/omni-tactical-xuanyuan13b-lora/checkpoint-{step}`
- **断点续训**：每个检查点均包含完整 `adapter_model.safetensors`、`adapter_config.json` 与 `tokenizer`，任意中断均可直接无缝加载。

---

## 📊 三、ModelScope 创空间 (Tianyan-HUD) 展现规范

### 1. 访问与权限
- **创空间标识**：`bnpysse/Tianyan-HUD`
- **自定义域名**：`http://ty.donglida.com`
- **源码保护规范**：
  - 创空间默认对外展示为 Streamlit 应用页面；
  - 若需避免他人查看代码，可进入创空间“设置”将可见性调整为“非公开”或隐藏 Files 标签。

### 2. UI 视觉与排版黄金法则
- **字体与组件紧凑度**：全站核心控件统一使用 `11px` 微字体，下拉框与输入框固定 `30px` 紧凑高度，保证单行展示不折行。
- **页面组件自上而下层级**：
  1. 顶部控制栏（分组选择、股票代码、斐波那契周期、无穷均线模式、AI 大模型选择）。
  2. 自选股与多分组管理抽屉（单行紧凑排列）。
  3. **DuckDB 全市场毫秒级多因子初筛引擎**（物理真空走廊、战略黄金坑、超级主升浪三大 Top-15 榜单，支持一键批量导入自选）。
  4. 五维量化战术状态栏与 5D 指标卡片（LFS、Z'、ASR、微观推升力、券商一致空间）。
  5. 198 斐波那契全周期深潜矩阵与 AI 参谋部穿透审计。
  6. 全息 5D 雷达图与 HUD 交互看板。

### 3. DuckDB 向量化计算定位
- DuckDB 是嵌入式内存列式 SQL 引擎，直接在内存中对全市场 5,115 只股票的 28 维因子进行秒级复杂过滤（单次全表扫描 < 30ms），无需启动庞大数据库服务。

---

## 🛠️ 四、常见故障排查与避坑指南 (Troubleshooting)

| 故障现象 | 根因分析 | 标准解决解法 |
| :--- | :--- | :--- |
| **超出磁盘配额 (EDQUOT)** | 误下载超大模型（如 63G FinX1）或未清理缓存 | 删除冗余模型碎片，保持磁盘使用率在 60% 以下安全区 |
| **内存溢出 (OOM / SIGKILL)** | 在 32GB CPU 实例上全精度跑 13B 模型 | 立即迁移至 AMD 192GB 显存实例，或开启 `bfloat16` + `low_cpu_mem_usage` |
| **1 小时/8 小时自动关机** | 触发闲置检测或免费实例 8 小时强制回收 | 1. 部署 3 重保活探针；2. 依靠 GPU 20~30 分钟极速完工并在高频 Checkpoint 存盘 |
| **SSH 报错 Host identification changed** | cpolar 随机分配了已连接过的端口导致指纹变动 | 执行 `ssh-keygen -R "[10.tcp.cpolar.top]:PORT"` 移除旧指纹 |
| **Streamlit 报错类型比较错误** | `sel_dim5` 下拉框返回了字符串而非整数 | 强制在 `app.py` 中做映射转换：`dim5_mode = int(re.search(r'\d+', sel_dim5).group())` |

---

## 🚀 五、一键启动命令速查表

```bash
# 1. 启动 DSW 隧道 (DSW 终端)
bash /mnt/workspace/start_tunnel.sh

# 2. 检查两路大模型 GPU 训练实时进展
tail -f /mnt/workspace/quant_data/gpu_live_training_progress.log
tail -f /mnt/workspace/quant_data/xuanyuan13b_gpu_training_progress.log

# 3. 检查显卡显存与利用率
rocm-smi --showmeminfo vram --showuse

# 4. 本地同步代码并推送到创空间
python scripts/deploy_to_studio.py
```
