import paramiko

def setup_service():
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=port, username=username, password=password, timeout=15)
        print("[+] SSH Connection successful!")
        
        # 1. Define the systemd service content
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
        
        # 2. Write the service file
        # We can write it by using echo with EOF to avoid escaping issues
        print("Creating systemd service file...")
        cmd_write = f"cat << 'EOF' > /etc/systemd/system/stock-recommend.service\n{service_content}EOF"
        stdin, stdout, stderr = ssh.exec_command(cmd_write)
        print("Write exit status:", stdout.channel.recv_exit_status())
        
        # 3. Reload systemd daemon, enable and start service
        commands = [
            "systemctl daemon-reload",
            "systemctl enable stock-recommend.service",
            "systemctl restart stock-recommend.service",
            "systemctl status stock-recommend.service --no-pager",
            "ss -tlnp | grep 8000"
        ]
        
        for cmd in commands:
            print(f"\n=== Running: {cmd} ===")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode()
            err = stderr.read().decode()
            if out:
                print(out)
            if err:
                print(f"Stderr:\n{err}")
                
        ssh.close()
    except Exception as e:
        print(f"[x] Failed: {str(e)}")

if __name__ == "__main__":
    setup_service()
