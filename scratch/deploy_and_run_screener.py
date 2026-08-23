import os
import sys
import subprocess

try:
    import paramiko
except ImportError:
    print("[*] Installing paramiko library for SSH...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

from paramiko import SSHClient, AutoAddPolicy

def sftp_upload_dir(sftp, local_dir, remote_dir, exclude_dirs=None, exclude_files=None):
    if exclude_dirs is None:
        exclude_dirs = {'.git', '.vercel', '.pytest_cache', '__pycache__', 'venv', 'logs', 'reports', 'chrome_profile', 'temp_chrome_profile', 'data'}
    if exclude_files is None:
        exclude_files = {'.env', 'portfolio.json'} # Do not overwrite remote configs/holdings

    print(f"Syncing directory: {local_dir} -> {remote_dir}")
    
    try:
        sftp.mkdir(remote_dir)
        print(f"Created remote dir: {remote_dir}")
    except OSError:
        pass

    for entry in os.listdir(local_dir):
        local_path = os.path.join(local_dir, entry)
        remote_path = remote_dir + '/' + entry
        
        if os.path.isdir(local_path):
            if entry in exclude_dirs:
                continue
            sftp_upload_dir(sftp, local_path, remote_path, exclude_dirs, exclude_files)
        else:
            if entry in exclude_files:
                continue
            if entry.endswith('.pyc') or entry.endswith('.log') or entry.startswith('.~'):
                continue
            
            print(f"Uploading file: {local_path} -> {remote_path}")
            sftp.put(local_path, remote_path)

def run_deployment():
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    
    print(f"Connecting to remote server {host}:{port}...")
    ssh.connect(host, port=port, username=username, password=password)
    print("[+] SSH Connected.")
    
    # 1. Sync code
    sftp = ssh.open_sftp()
    local_workspace = r"c:\Users\samsung\proj\stockRecommend"
    remote_workspace = "/root/stockRecommend"
    
    print("[*] Uploading updated files to remote server...")
    sftp_upload_dir(sftp, local_workspace, remote_workspace)
    sftp.close()
    print("[+] SFTP sync completed.")
    
    # 2. Run database cleanup and full screening
    cmd_run_screener = "cd /root/stockRecommend && ./venv/bin/python scratch/run_three_markets_screener.py"
    print(f"\n[*] Running database cleanup and full screening on Cafe24:\n    Command: {cmd_run_screener}")
    
    stdin, stdout, stderr = ssh.exec_command(cmd_run_screener)
    
    # Read output line-by-line in real-time
    while True:
        line = stdout.readline()
        if not line:
            break
        print(f"    [REMOTE] {line.strip()}")
        
    err = stderr.read().decode().strip()
    exit_status = stdout.channel.recv_exit_status()
    print(f"[+] Screen execution finished with exit status: {exit_status}")
    if err:
        print(f"[!] Stderr:\n{err}")
        
    # 3. Restart systemd service
    cmd_restart = "systemctl restart stock-recommend"
    print(f"\n[*] Restarting web service on Cafe24:\n    Command: {cmd_restart}")
    stdin, stdout, stderr = ssh.exec_command(cmd_restart)
    exit_status_restart = stdout.channel.recv_exit_status()
    print(f"[+] Web service restarted. Status code: {exit_status_restart}")
    
    ssh.close()
    print("\n[+] Deployment and database rebuild completed successfully!")

if __name__ == "__main__":
    run_deployment()
