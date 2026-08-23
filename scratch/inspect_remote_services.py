import paramiko

def inspect_services():
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
            "ls -la /etc/systemd/system/ | grep -E 'stock|fastapi|uvicorn|web'",
            "systemctl --type=service --state=running | grep -E 'stock|fastapi|uvicorn|web'",
            "find /etc/systemd/system/ -name '*.service' 2>/dev/null",
            "cat /etc/systemd/system/stock-recommend.service 2>/dev/null || echo 'stock-recommend.service not found'"
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
    inspect_services()
