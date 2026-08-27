import os
import paramiko
import sys

def test_ssh(host="8.tcp.cpolar.cn", port=10183, username="root", key_path=None):
    if key_path is None:
        key_path = os.path.expanduser("~/.ssh/id_rsa")
    print(f"Connecting via SSH Key to {username}@{host}:{port} using {key_path} ...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=host, port=port, username=username, key_filename=key_path, look_for_keys=True, timeout=10)
        print("🎉 [SSH 证书连接成功] 已经与 ModelScope 云端实例成功建立纯证书安全通道！\n")
        
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
        client.close()
        return True
    except Exception as e:
        print(f"❌ SSH 证书连接失败: {e}")
        return False

if __name__ == "__main__":
    test_ssh()
