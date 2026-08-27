#!/usr/bin/env python3
"""
DSW VSCode / JupyterLab 真实终端与网页编辑器活跃度模拟守护进程
自动挂接 DSW 内核 API，更新 last_activity 时间戳，保持 100% 活跃状态，防止云端闲置停机！
"""
import time
import urllib.request
import json
import subprocess
import os

def get_base_url():
    try:
        out = subprocess.check_output(['/etc/dsw/cache/pre-install/plugins/jupyter-lab/v3.6.5/venv/bin/jupyter', 'server', 'list'], text=True)
        for line in out.splitlines():
            if 'http://127.0.0.1:8088/' in line:
                url_part = line.split('::')[0].strip()
                return url_part if url_part.endswith('/') else url_part + '/'
    except Exception as e:
        pass
    return 'http://127.0.0.1:8088/'

base_url = get_base_url()
print(f'🚀 [VSCode/Jupyter 保活核心] 挂载至 DSW 内核: {base_url}')

terminal_name = 'keepalive_terminal'

try:
    req = urllib.request.Request(base_url + 'api/terminals', data=b'', headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as resp:
        t_data = json.loads(resp.read().decode())
        terminal_name = t_data.get('name', '1')
        print(f'✅ 成功在 VSCode/Jupyter 内部创建活跃终端: {terminal_name}')
except Exception as e:
    print(f'⚠️ 终端就绪或已存在: {e}')

while True:
    try:
        now_str = time.strftime('%Y-%m-%d %H:%M:%S')
        with open('/mnt/workspace/.vscode_activity.log', 'a') as f:
            f.write(f'[{now_str}] VSCode Editor & Terminal Active Pulse\n')
        
        status_url = base_url + 'api/status'
        with urllib.request.urlopen(status_url) as resp:
            st_data = json.loads(resp.read().decode())
            # print(f"[{now_str}] 💓 Web IDE 活跃状态刷新: last_activity={st_data.get('last_activity')}")
    except Exception as e:
        print(f'心跳探测异常: {e}')
    
    time.sleep(30)
