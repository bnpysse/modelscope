#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ModelScope 云端实例 SSH 远程自动化调度器 (纯证书免密认证版)
"""
import os
import paramiko
from typing import Tuple, Optional

class ModelScopeRemoteExecutor:
    def __init__(self, host: str = "8.tcp.cpolar.cn", port: int = 10183, user: str = "root", key_path: Optional[str] = None):
        self.host = host
        self.port = port
        self.user = user
        # 优先读取用户标准 SSH 证书/私钥
        if key_path and os.path.exists(key_path):
            self.key_path = key_path
        else:
            default_keys = [
                os.path.expanduser("~/.ssh/id_rsa"),
                os.path.expanduser("~/.ssh/id_ed25519")
            ]
            valid_keys = [k for k in default_keys if os.path.exists(k)]
            self.key_path = valid_keys[0] if valid_keys else None

    def run_remote_command(self, cmd: str, timeout: int = 60) -> Tuple[str, str, int]:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.user,
                key_filename=self.key_path,
                look_for_keys=True,
                timeout=15
            )
            stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode("utf-8")
            err = stderr.read().decode("utf-8")
            exit_code = stdout.channel.recv_exit_status()
            return out, err, exit_code
        finally:
            client.close()

remote_executor = ModelScopeRemoteExecutor()
