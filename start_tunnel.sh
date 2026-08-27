#!/usr/bin/env bash
# ==============================================================================
# ModelScope Notebook 开机一键拉起 SSH 与 cpolar 隧道 (全自动认证 + 路径自愈)
# ==============================================================================

echo "================================================================================"
echo "🚀 [ModelScope 算力工厂] 一键启动 SSH 证书直连与 cpolar 专线隧道"
echo "================================================================================"

AUTHTOKEN="ZWY0YTYyNWYtYzA0Yy00MDY5LTgyYzEtOTk4Zjg0YTkyMjY1"
BIN_DIR="/mnt/workspace/bin"
CPOLAR_BIN="${BIN_DIR}/cpolar"

# 1. 确保目录与 cpolar 可执行文件存在
mkdir -p "${BIN_DIR}" ~/.ssh /mnt/workspace/.ssh

if [ ! -f "${CPOLAR_BIN}" ]; then
    echo "📦 正在自动下载 cpolar 客户端至 ${BIN_DIR} ..."
    curl -fsSL https://static.cpolar.com/downloads/cpolar-stable-linux-amd64.zip -o /tmp/cpolar.zip
    unzip -o -q /tmp/cpolar.zip -d "${BIN_DIR}"
    chmod +x "${CPOLAR_BIN}"
    rm -f /tmp/cpolar.zip
fi

# 挂载到系统 PATH
chmod +x "${CPOLAR_BIN}"
ln -sf "${CPOLAR_BIN}" /usr/local/bin/cpolar 2>/dev/null || true
export PATH="${BIN_DIR}:/usr/local/bin:$PATH"

# 2. 绑定 cpolar 专属认证口令
echo "🔑 正在配置 cpolar 专属认证口令..."
"${CPOLAR_BIN}" authtoken "${AUTHTOKEN}" >/dev/null 2>&1 || true

# 3. 恢复 4096-bit RSA 免密证书
if [ -f /mnt/workspace/.ssh/authorized_keys ]; then
    cp /mnt/workspace/.ssh/authorized_keys ~/.ssh/authorized_keys
    chmod 700 ~/.ssh
    chmod 600 ~/.ssh/authorized_keys
    echo "🔑 4096-bit RSA 免密证书已恢复！"
fi

# 4. 启动/重启 SSH 守护进程
service ssh restart 2>/dev/null || /usr/sbin/sshd 2>/dev/null || true
echo "✅ SSH 守护进程已启动 (Port 22)"

# 5. 补齐核心量化依赖
echo "📦 检查并补齐量化依赖 (Polars, DuckDB, BaoStock, AkShare, ModelScope)..."
pip install --quiet polars duckdb baostock akshare modelscope python-dotenv pydantic

# 6. 杀掉可能残留的旧 cpolar 并启动新隧道
killall cpolar 2>/dev/null || true
sleep 1
nohup "${CPOLAR_BIN}" tcp 22 > /mnt/workspace/cpolar.log 2>&1 &
echo "⏳ 等待 cpolar 建立公网专线..."
sleep 4

# 7. 获取并输出最新的公网 TCP 直连地址
echo "================================================================================"
echo "📡 cpolar 隧道已成功建立！公网连接信息如下："
echo "================================================================================"
TUNNEL_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | grep -o 'tcp://[^"]*' | head -n 1)

if [ -n "$TUNNEL_URL" ]; then
    HOST=$(echo $TUNNEL_URL | sed 's/tcp:\/\///' | cut -d: -f1)
    PORT=$(echo $TUNNEL_URL | sed 's/tcp:\/\///' | cut -d: -f2)
    echo "🎯 直连地址: $TUNNEL_URL"
    echo "👉 Mac 终端直连命令: ssh -p $PORT root@$HOST"
else
    echo "📄 正在从日志解析连接地址:"
    grep -o 'tcp://.*' /mnt/workspace/cpolar.log | head -n 1 || cat /mnt/workspace/cpolar.log
fi
echo "================================================================================"
