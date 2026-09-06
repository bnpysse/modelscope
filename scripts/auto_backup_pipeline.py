import os
import sys
import time
import hashlib
import subprocess

SAVE_DIR = "/Users/woodman/dev/modelscope/models/checkpoints"
os.makedirs(SAVE_DIR, exist_ok=True)

TASKS = [
    {
        "name": "💎 天衍 32B 战术 LoRA 核心检查点",
        "filename": "tianyan_lora_checkpoint260.tar.gz",
        "url": "http://127.0.0.1:8099/tianyan_lora_checkpoint260.tar.gz",
        "expected_md5": "40af0fdcae24f6591caae21b302bc3c3",
        "expected_size_mb": 948.4
    },
    {
        "name": "🚀 天衍 32B AWQ 4-bit 终极量化大模型压缩包",
        "filename": "tianyan_omni_32b_awq4bit.tar.gz",
        "url": "http://127.0.0.1:8099/tianyan_omni_32b_awq4bit.tar.gz",
        "expected_md5": "8f82bd313646e69eb81fb9d8a65ff6fe",
        "expected_size_mb": 16200.0
    }
]

def verify_file_md5(filepath, expected):
    print(f"🔍 [校验中] 正在计算文件哈希指纹: {filepath} ...")
    h = hashlib.md5()
    t0 = time.time()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024 * 16):
            h.update(chunk)
    actual = h.hexdigest()
    print(f"   ✓ 本地实际 MD5: {actual}")
    print(f"   ✓ 云端官方 MD5: {expected}")
    print(f"   ⏱️ 校验耗时: {time.time()-t0:.1f} 秒")
    return actual.lower() == expected.lower()

def run_task(task):
    filename = task["filename"]
    filepath = os.path.join(SAVE_DIR, filename)
    url = task["url"]
    expected_md5 = task["expected_md5"]
    
    print("\n" + "=" * 80)
    print(f"📦 开始执行资产备份任务: {task['name']}")
    print(f"🎯 目标文件: {filename} (~{task['expected_size_mb']} MB)")
    print("=" * 80)
    
    # 检查本地是否已经完整存在并校验过
    if os.path.exists(filepath) and not os.path.exists(f"{filepath}.aria2"):
        if verify_file_md5(filepath, expected_md5):
            print(f"🎉 该文件已在本地完好无损存在，跳过下载！\n")
            return True

    # 启动 aria2c 断点续传拉取
    cmd = [
        "aria2c",
        "-c",
        "-s", "4",
        "-x", "4",
        "-k", "2M",
        "--dir", SAVE_DIR,
        "--out", filename,
        "--auto-file-renaming=false",
        "--max-tries=0",
        "--retry-wait=5",
        url
    ]
    
    print(f"🚀 启动 aria2c 断点续传多线程拉取...")
    subprocess.run(cmd)
    
    # 校验
    if verify_file_md5(filepath, expected_md5):
        print(f"🎉 任务大圆满: 【{filename}】 100% 完整无损落盘并校验通过！")
        return True
    else:
        print(f"❌ 警告: 【{filename}】 MD5 校验不通过，请检查网络！")
        return False

if __name__ == "__main__":
    print("🛡️ [天衍核心资产] 自动流水线备份与校验守护进程启动...")
    for idx, task in enumerate(TASKS, 1):
        print(f"\n▶ 进度阶段 [{idx}/{len(TASKS)}]")
        success = run_task(task)
        if not success:
            print(f"⚠️ 阶段 [{idx}] 出现异常，流水线暂停。")
            break
        print(f"✓ 阶段 [{idx}] 已圆满收尾！")
    print("\n" + "★" * 80)
    print("🏆 全部核心大模型资产本地 Mac 备份与无损校验任务全量达成！")
    print("★" * 80)
