#!/usr/bin/env bash
# ==============================================================================
# 天衍量化系统 — N100 小主机 / 阿里云定时数据采集与 Level-2 归库部署脚本
# 调度时刻：每个交易日 11:35 (午盘快照) 与 15:35 (收盘终审)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_BIN="$(which python3)"

echo "================================================================================"
echo "🛰️  【天衍量化系统】N100 小主机 / 阿里云 盘中盘后自动采集任务部署"
echo "📁  工作目录: ${ROOT_DIR}"
echo "🐍  Python 路径: ${PYTHON_BIN}"
echo "================================================================================"

CRON_JOB_NOON="35 11 * * 1-5 cd ${ROOT_DIR} && ${PYTHON_BIN} scripts/daily_post_market_updater.py --session noon >> ${ROOT_DIR}/quant_data/cron_noon.log 2>&1"
CRON_JOB_CLOSE="35 15 * * 1-5 cd ${ROOT_DIR} && ${PYTHON_BIN} scripts/daily_post_market_updater.py --session close >> ${ROOT_DIR}/quant_data/cron_close.log 2>&1"

# 读取当前 crontab 并避免重复添加
CURRENT_CRON=$(crontab -l 2>/dev/null || true)

NEW_CRON=$(echo "$CURRENT_CRON" | grep -v "daily_post_market_updater.py" || true)
NEW_CRON="${NEW_CRON}
# --- 天衍五维量化大脑每日自动化数据归并管线 ---
${CRON_JOB_NOON}
${CRON_JOB_CLOSE}
"

echo "$NEW_CRON" | crontab -

echo "✅ Crontab 定时任务部署成功！"
echo "⏰ 每日触发计划："
echo "   • 周一至周五 11:35: 抓取上午半天 Level-2 逐笔订单流与行情，生成午间审计宽表"
echo "   • 周一至周五 15:35: 抓取全天 Level-2 逐笔订单流与收盘行情，完成全量因子递推并推送到创空间"
echo "================================================================================"
crontab -l | grep daily_post_market_updater.py
echo "================================================================================"
