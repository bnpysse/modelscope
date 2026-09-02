import paramiko
import base64
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('12.tcp.vip.cpolar.cn', port=13803, username='root', key_filename='/Users/woodman/.ssh/id_rsa', timeout=10)

watcher_code = """import os, sys, time

log_file = '/mnt/workspace/auto_shutdown.log'
def log(msg):
    t = time.strftime('[%Y-%m-%d %H:%M:%S]')
    line = str(t) + ' ' + str(msg) + '\\n'
    print(line, flush=True)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(line)

log('🛡️ 自动关机守护神启动！全天候监控 Checkpoint-150 落盘...')

target_path = '/mnt/workspace/models/omni-qwen2.5-32b-rocm-lora/checkpoint-150'
while True:
    if os.path.exists(target_path):
        try:
            files = os.listdir(target_path)
            if any('adapter_model' in f for f in files):
                log('🎉 成功探测到 Checkpoint-150 已 100% 完整落盘写入！')
                log('正在执行操作系统双重落盘同步 (sync)...')
                os.system('sync')
                time.sleep(5)
                log('🚀 触发远程自动关机指令 (poweroff)，完美停机保护算力！')
                os.system('/usr/sbin/poweroff || /usr/sbin/shutdown -h now || kill -15 1')
                break
        except Exception as e:
            pass
    time.sleep(15)
"""

b64 = base64.b64encode(watcher_code.encode('utf-8')).decode('utf-8')
ssh.exec_command(f'echo {b64} | base64 -d > /mnt/workspace/watcher.py && pkill -9 -f watcher.py 2>/dev/null || true')
time.sleep(1)

stdin, stdout, stderr = ssh.exec_command("""python3 -c "import subprocess; f = open('/mnt/workspace/auto_shutdown.log', 'w'); p = subprocess.Popen(['python3', '/mnt/workspace/watcher.py'], cwd='/mnt/workspace', stdout=f, stderr=subprocess.STDOUT, start_new_session=True); print('Watcher PID:', p.pid)" """)
print(stdout.read().decode())
time.sleep(2)

stdin, stdout, stderr = ssh.exec_command("ps aux | grep watcher.py | grep -v grep; cat /mnt/workspace/auto_shutdown.log")
print(stdout.read().decode())
ssh.close()
