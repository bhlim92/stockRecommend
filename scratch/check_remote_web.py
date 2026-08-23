import paramiko

def check_web():
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=port, username=username, password=password, timeout=15)
        print("[+] SSH Connection successful!")
        
        commands = [
            "ss -tlnp",
            "systemctl list-units --type=service | grep -E 'stock|fastapi|uvicorn|web|nginx|apache'",
            "pm2 list || echo 'pm2 not installed'",
            "docker ps || echo 'docker not running'",
            "cat /etc/nginx/sites-enabled/* 2>/dev/null || cat /etc/nginx/conf.d/* 2>/dev/null || cat /etc/nginx/nginx.conf 2>/dev/null || echo 'nginx config not found'",
            "curl -I http://127.0.0.1:8000/ || curl -I http://127.0.0.1:80/ || echo 'no local connection'",
            "systemctl status stock-recommend 2>&1 || true",
            "systemctl status fastapi 2>&1 || true"
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
    check_web()
