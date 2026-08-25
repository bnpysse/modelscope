#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ModelScope 云端实例 SSH 远程自动化调度器
"""
import paramiko
from typing import Tuple

class ModelScopeRemoteExecutor:
    def __init__(self, host: str = "8.tcp.cpolar.cn", port: int = 10183, user: str = "root", password: str = "12345678"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    def run_remote_command(self, cmd: str, timeout: int = 60) -> Tuple[str, str, int]:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=self.host, port=self.port, username=self.user, password=self.password, timeout=15)
            stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode("utf-8")
            err = stderr.read().decode("utf-8")
            exit_code = stdout.channel.recv_exit_status()
            return out, err, exit_code
        finally:
            client.close()

remote_executor = ModelScopeRemoteExecutor()
