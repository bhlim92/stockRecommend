import paramiko

def check_ufw():
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
            "ufw status",
            "iptables -L -n -v | grep -E '8000|3306|80'"
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
    check_ufw()
