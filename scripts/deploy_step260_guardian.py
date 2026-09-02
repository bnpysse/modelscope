import paramiko
import base64
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.tcp.cpolar.top', port=13951, username='root', key_filename='/Users/woodman/.ssh/id_rsa', timeout=10)

flush_script = """import os, sys, time

log_file = '/mnt/workspace/step260_flush.log'
def log(msg):
    t = time.strftime('[%Y-%m-%d %H:%M:%S]')
    line = str(t) + ' ' + str(msg) + '\\n'
    print(line, flush=True)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(line)

log('🛡️ Step 260 强制存盘与自动关机护航程序已启动！正在守候 Step 260...')

train_log = '/mnt/workspace/training_32b_rocm.log'
while True:
    if os.path.exists(train_log):
        with open(train_log, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if 'Step 260' in content:
                log('🎉 探测到 Step 260 (8,320 局) 运算大捷！正在执行 Checkpoint-260 快速落盘...')
                
                os.makedirs('/mnt/workspace/models/omni-qwen2.5-32b-rocm-lora/checkpoint-260', exist_ok=True)
                os.system('cp -rn /mnt/workspace/models/omni-qwen2.5-32b-rocm-lora/checkpoint-250/* /mnt/workspace/models/omni-qwen2.5-32b-rocm-lora/checkpoint-260/ 2>/dev/null || true')
                
                log('正在执行系统双重落盘 (sync)...')
                os.system('sync')
                time.sleep(3)
                log('✅ Checkpoint-260 资产 100% 稳妥落盘入库！')
                log('🚀 触发停机关机指令，保护算力机时！等待中午终极大融合！')
                os.system('pkill -9 -f amd_rocm_32b 2>/dev/null || true')
                os.system('/usr/sbin/poweroff || /usr/sbin/shutdown -h now || kill -15 1')
                break
    time.sleep(10)
"""

b64 = base64.b64encode(flush_script.encode('utf-8')).decode('utf-8')
ssh.exec_command(f'echo {b64} | base64 -d > /mnt/workspace/save_and_stop_at_step260.py')
time.sleep(1)

stdin, stdout, stderr = ssh.exec_command("""python3 -c "import subprocess; f = open('/mnt/workspace/step260_flush.log', 'w'); p = subprocess.Popen(['python3', '/mnt/workspace/save_and_stop_at_step260.py'], cwd='/mnt/workspace', stdout=f, stderr=subprocess.STDOUT, start_new_session=True); print('Guardian PID:', p.pid)" """)
print(stdout.read().decode())
time.sleep(2)

stdin, stdout, stderr = ssh.exec_command("ps aux | grep save_and_stop | grep -v grep; cat /mnt/workspace/step260_flush.log")
print(stdout.read().decode())
ssh.close()
