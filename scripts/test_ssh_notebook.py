#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通过 cpolar 隧道连接 ModelScope 云端实例并执行指令
"""
import paramiko
import sys

def test_ssh(host="8.tcp.cpolar.cn", port=10183, username="root", password="12345678"):
    print(f"Connecting to {username}@{host}:{port} ...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        print("🎉 [SSH 连接成功] 已经与 ModelScope 云端实例成功建立双向通道！\n")
        
        # 执行远程命令
        cmd = "whoami && uname -a && lscpu | head -n 8 && python -V"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8')
        err = stderr.read().decode('utf-8')
        
        print("---【云端返回信息】---")
        print(out)
        if err:
            print("STDERR:", err)
        print("-----------------------")
        
        # 写入并执行一个云端探针
        cmd2 = "cd /mnt/workspace/quant_engine && python run_cloud_compute.py"
        print(f"Executing: {cmd2}")
        stdin, stdout, stderr = client.exec_command(cmd2)
        out2 = stdout.read().decode('utf-8')
        print(out2)
        
        client.close()
        return True
    except Exception as e:
        print(f"❌ SSH 连接失败: {e}")
        return False

if __name__ == "__main__":
    test_ssh()
