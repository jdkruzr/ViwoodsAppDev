#!/usr/bin/env python3
"""Helper to run commands on the Viwoods tablet via SSH."""
import sys
import warnings
import paramiko

warnings.filterwarnings("ignore")

def run(cmd, timeout=30):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.8.156', port=8022, username='u0_a155', password='ehhjqb', timeout=10)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    client.close()
    if out:
        print(out, end='')
    if err:
        print(err, end='', file=sys.stderr)

if __name__ == '__main__':
    run(' '.join(sys.argv[1:]))
