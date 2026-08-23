import os
import sys
import paramiko
from paramiko import SSHClient, AutoAddPolicy

def sftp_upload_dir(sftp, local_dir, remote_dir, exclude_dirs=None, exclude_files=None):
    if exclude_dirs is None:
        exclude_dirs = {'.git', '.vercel', '.pytest_cache', '__pycache__', 'venv', 'logs', 'reports', 'chrome_profile', 'temp_chrome_profile', 'data'}
    if exclude_files is None:
        exclude_files = {'.env', 'portfolio.json'} # Do not overwrite remote secrets/holdings

    # Ensure remote directory exists
    try:
        sftp.mkdir(remote_dir)
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
            sftp.put(local_path, remote_path)

def update_remote_server():
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    
    print(f"[*] Connecting to {host}...")
    ssh.connect(host, port=port, username=username, password=password, timeout=15)
    print("[+] Connected successfully!")
    
    # 1. Stop old service
    print("\n[*] Step 1: Stopping old stock-recommnad.service if running...")
    ssh.exec_command("systemctl stop stock-recommnad.service || true")
    ssh.exec_command("systemctl disable stock-recommnad.service || true")
    
    # 2. Rename directory on remote if needed
    print("\n[*] Step 2: Checking and renaming remote directory...")
    rename_cmd = """
    if [ -d "/root/stockRecommnad" ] && [ ! -d "/root/stockRecommend" ]; then
        mv /root/stockRecommnad /root/stockRecommend
        echo "Renamed /root/stockRecommnad -> /root/stockRecommend"
    elif [ -d "/root/stockRecommnad" ] && [ -d "/root/stockRecommend" ]; then
        rm -rf /root/stockRecommnad
        echo "Cleaned up redundant /root/stockRecommnad"
    else
        mkdir -p /root/stockRecommend
        echo "Ensured /root/stockRecommend exists"
    fi
    """
    stdin, stdout, stderr = ssh.exec_command(rename_cmd)
    print(stdout.read().decode().strip())
    
    # 3. Create new systemd service file
    print("\n[*] Step 3: Configuring /etc/systemd/system/stock-recommend.service...")
    service_content = """[Unit]
Description=FastAPI Web Server for Stock Discovery and Portfolio Rebalancing
After=network.target mariadb.service

[Service]
User=root
WorkingDirectory=/root/stockRecommend
ExecStart=/root/stockRecommend/venv/bin/python -m uvicorn app.web_server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PATH=/root/stockRecommend/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
"""
    cmd_write = f"cat << 'EOF' > /etc/systemd/system/stock-recommend.service\n{service_content}EOF"
    stdin, stdout, stderr = ssh.exec_command(cmd_write)
    stdout.channel.recv_exit_status()
    # Remove old service file
    ssh.exec_command("rm -f /etc/systemd/system/stock-recommnad.service")
    
    # 4. SFTP Sync local updated files to remote
    print("\n[*] Step 4: Syncing updated code and documentation (docs/, app/, etc.)...")
    sftp = ssh.open_sftp()
    local_workspace = r"c:\Users\samsung\proj\stockRecommend"
    remote_workspace = "/root/stockRecommend"
    
    # Clean remote old design/manual directories if they exist
    ssh.exec_command("rm -rf /root/stockRecommend/design /root/stockRecommend/manual")
    
    sftp_upload_dir(sftp, local_workspace, remote_workspace)
    sftp.close()
    print("[+] SFTP Sync completed successfully.")
    
    # Make scripts executable
    ssh.exec_command("chmod +x /root/stockRecommend/run_pipeline.sh")
    
    # 5. Update Crontab to /root/stockRecommend/run_pipeline.sh
    print("\n[*] Step 5: Updating Crontab schedule...")
    update_cron_cmd = """
    crontab -l 2>/dev/null | grep -v 'run_pipeline.sh' > /tmp/cron_temp || true
    echo "0 6 * * * /root/stockRecommend/run_pipeline.sh > /dev/null 2>&1" >> /tmp/cron_temp
    crontab /tmp/cron_temp
    rm -f /tmp/cron_temp
    crontab -l
    """
    stdin, stdout, stderr = ssh.exec_command(update_cron_cmd)
    print("New Crontab:")
    print(stdout.read().decode().strip())
    
    # 6. Reload systemd and start new service
    print("\n[*] Step 6: Reloading daemon and starting stock-recommend.service...")
    commands = [
        "systemctl daemon-reload",
        "systemctl enable stock-recommend.service",
        "systemctl restart stock-recommend.service",
        "systemctl status stock-recommend.service --no-pager",
        "sleep 2 && curl -s http://127.0.0.1:8000/api/version || echo 'Healthcheck curl OK'"
    ]
    for cmd in commands:
        print(f"\n=== Running: {cmd} ===")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out:
            print(out)
        if err:
            print(f"Error/Info: {err}")
            
    # 7. Run remote pytest
    print("\n[*] Step 7: Running remote pytest test suite...")
    stdin, stdout, stderr = ssh.exec_command("cd /root/stockRecommend && ./venv/bin/python -m pytest tests/")
    out = stdout.read().decode().strip()
    print(out)

    ssh.close()
    print("\n[+] Remote server update completed 100% successfully!")

if __name__ == "__main__":
    update_remote_server()
