# ModelScope Notebook 云端环境与运维配置手册

---

## 一、 云端实例基础架构

*   **平台规格**：ModelScope PAI-DSW 免费云端实例（CPU / 24G NVIDIA GPU / 192G AMD GPU）。
*   **操作系统**：Linux x86_64 (Alibaba Cloud Linux 3 / Docker 容器环境)。
*   **运行时**：Python 3.11.11 / Python 3.9，内置 PyTorch、Polars、NumPy、DuckDB、BaoStock、AkShare。
*   **生命周期约束**：实例闲置 1 小时后会自动关机休眠。

---

## 二、 关键磁盘持久化策略（防休眠数据丢失）

ModelScope PAI-DSW 容器中，**只有 `/mnt/workspace` 目录下的磁盘文件在关机重启后永久保留**，临时内存与根目录会被重置。

### 目录持久化布局：
```
/mnt/workspace/
├── quant_engine/               # 量化核心代码仓库 (Git 托管)
│   ├── core/                   # 五维数学引擎、AI 参谋部、DuckDB 初筛
│   ├── streamlit_app/          # 全息 HUD 交互面板
│   └── scripts/                # 全市场日线采集与微积分流水线
└── quant_data/                 # 持久化量化数据中心 (永久保留，不断点丢失)
    ├── all_a_shares_parquet/   # 全市场 5115 只 A 股前复权日线 (ZSTD 压缩)
    ├── factors/                # 5115 只标的历史全周期五维衍生因子库
    ├── full_market_snapshot.parquet # 最新全市场截面快照宽表
    └── modelscope_budget.db    # 本地 SQLite 免费配额门神台账
```

---

## 三、 国内专线反向 SSH 隧道直连配置 (cpolar)

由于 ModelScope 容器处于阿里云 VPC 内网，通过 **cpolar（国内 BGP 机房专线）** 实现本地 Mac 与云端实例的毫秒级双向直连。

### 1. 云端自动部署证书 (实现 4096-bit RSA 金融级免密直连)
*   **本地公钥**：自动将 Mac 的 `~/.ssh/id_rsa.pub` (4096-bit RSA) 注入云端；
*   **持久化保存**：公钥已持久化写入 `/mnt/workspace/.ssh/authorized_keys`；
*   **安全加固**：每次启动实例自动生效，**无需输入任何明文密码，防暴力破解，零泄漏风险**！

### 2. 本地 Mac 终端一键免密直连
```bash
ssh -p 10183 root@8.tcp.cpolar.cn
# 无需输入密码，直接以 4096-bit 密钥秒连入容器！
```

### 3. 本地 VS Code Remote-SSH 直连 (`~/.ssh/config`)
```ssh-config
Host modelscope
    HostName 8.tcp.cpolar.cn
    Port 10183
    User root
```

---

## 四、 ModelScope 免费大模型 API 网关与预算门神

### 1. API 接口规范
*   **Endpoint**：`https://api-inference.modelscope.cn/v1/chat/completions`
*   **官方配额**：每日 2,000 次免费调用（每日 00:00 自动重置）。

### 2. 本地 SQLite 预算硬锁门神 (`core/providers/modelscope_client.py`)
*   **安全硬顶**：`1,800 次/天`（90% 安全水位，到达后本地自动硬熔断，100% 杜绝扣费）。
*   **自动级联调度 (Auto-Cascading)**：
    `MiniMax-M1-80k` (长文思考) ➔ `Qwen3-Coder-30B` (1.2s 极速) ➔ `Qwen3-235B` (旗舰大模型) ➔ 本地规则回退。

---

## 五、 Git 仓库与敏感密钥隔离铁律

*   **GitHub 远程仓库**：`https://github.com/bnpysse/modelscope.git`
*   **安全隔离规范**：
    *   `.env`、`client_secret.json`、`service_account.json`、`*.db`、`*.key` **绝对严禁入库**；
    *   所有代码仅通过 `os.environ.get("MODELSCOPE_API_KEY")` 读取环境变量，代码中严禁任何硬编码 Key。
