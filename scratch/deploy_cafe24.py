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
    
    # Ensure remote directory exists
    try:
        sftp.mkdir(remote_dir)
        print(f"Created remote dir: {remote_dir}")
    except OSError:
        pass # Already exists or couldn't create

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
            # Check if it's a temp file
            if entry.endswith('.pyc') or entry.endswith('.log') or entry.startswith('.~'):
                continue
            
            print(f"Uploading file: {local_path} -> {remote_path}")
            sftp.put(local_path, remote_path)

def deploy_to_cafe24():
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    
    print(f"Connecting to {host}:{port} as {username}...")
    ssh.connect(host, port=port, username=username, password=password)
    print("Connected.")
    
    # Start SFTP client
    sftp = ssh.open_sftp()
    
    # Sync folders
    local_workspace = r"c:\Users\samsung\proj\stockRecommend"
    remote_workspace = "/root/stockRecommend"
    
    sftp_upload_dir(sftp, local_workspace, remote_workspace)
    sftp.close()
    print("SFTP Sync completed.")
    
    # Run server update commands
    commands = [
        "cd /root/stockRecommend && ./venv/bin/pip install -r requirements.txt",
        "cd /root/stockRecommend && ./venv/bin/python -m pytest tests/",
        "systemctl restart stock-recommend"
    ]
    
    for cmd in commands:
        print(f"\nRunning command: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        print(f"Exit status: {exit_status}")
        out = stdout.read().decode()
        err = stderr.read().decode()
        if out:
            print("Stdout received")
        if err:
            print(f"Stderr:\n{err}")

    ssh.close()
    print("SSH connection closed.")

if __name__ == "__main__":
    deploy_to_cafe24()
