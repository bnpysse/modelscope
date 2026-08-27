#!/usr/bin/env bash
# ==============================================================================
# 天衍五维量化大模型 (omni-tactical-finllm) · ms-swift 一键 GPU LoRA 自动化微调脚本
# 底座模型: Duxiaoman-DI/XuanYuan-13B-Chat 或 Qwen/Qwen2.5-14B-Instruct
# 训练数据: /mnt/workspace/quant_data/omni_finllm_sft_train.jsonl
# 输出目录: /mnt/workspace/models/omni-tactical-finllm-lora
# ==============================================================================

set -e

echo "================================================================================"
echo "🚀 [天衍五维量化大脑] 启动 ms-swift GPU 自动化 LoRA 强化微调"
echo "================================================================================"

WORKSPACE="/mnt/workspace"
DATA_FILE="${WORKSPACE}/quant_data/omni_finllm_sft_train.jsonl"
BASE_MODEL="${WORKSPACE}/models/models/Duxiaoman-DI--XuanYuan-13B-Chat/snapshots/master"
OUTPUT_DIR="${WORKSPACE}/models/omni-tactical-finllm-13b-lora"

# 若本地路径不存在，则自动降级为在线 ModelScope 标识
if [ ! -d "${BASE_MODEL}" ]; then
    BASE_MODEL="Duxiaoman-DI/XuanYuan-13B-Chat"
fi


# 1. 确保环境与版本兼容
pip install -q "datasets>=2.18.0,<3.0.0" "transformers==4.44.2" "peft==0.12.0" "accelerate==0.34.2" ms-swift



# 2. 生成 SFT 数据集 (若未生成)
if [ ! -f "${DATA_FILE}" ]; then
    echo "📊 正在自动萃取全市场五维筹码物理场 SFT 训练集..."
    python ${WORKSPACE}/quant_engine/scripts/generate_sft_dataset.py
fi

# 3. 启动 ms-swift SFT 训练
echo "🔥 启动 ms-swift LoRA 微调训练 (基座: ${BASE_MODEL})..."

# 智能判断 swift 版本参数格式
if swift sft --help 2>&1 | grep -q "\-\-model "; then
    # swift 3.x+
    swift sft \
        --model "${BASE_MODEL}" \
        --model_type llama \
        --train_type lora \
        --dataset "${DATA_FILE}" \
        --output_dir "${OUTPUT_DIR}" \
        --num_train_epochs 3 \
        --max_length 2048 \
        --per_device_train_batch_size 2 \
        --gradient_accumulation_steps 8 \
        --learning_rate 1e-4 \
        --lora_rank 64 \
        --lora_alpha 128 \
        --gradient_checkpointing true \
        --save_steps 100 \
        --save_total_limit 2
else
    # swift 2.x
    swift sft \
        --model_type llama2-13b-chat \
        --model_id_or_path "${BASE_MODEL}" \
        --sft_type lora \
        --tuner_backend peft \
        --template_type default \
        --dataset "${DATA_FILE}" \
        --output_dir "${OUTPUT_DIR}" \
        --num_train_epochs 3 \
        --max_length 2048 \
        --batch_size 2 \
        --gradient_accumulation_steps 8 \
        --learning_rate 1e-4 \
        --lora_rank 64 \
        --lora_alpha 128 \
        --lora_dropout_p 0.05 \
        --gradient_checkpointing true \
        --save_steps 100 \
        --save_total_limit 2
fi

echo "================================================================================"
echo "🎉 [微调完成] LoRA 适配器权重已落盘至: ${OUTPUT_DIR}"
echo "================================================================================"

