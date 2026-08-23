import paramiko

def list_remote():
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=port, username=username, password=password, timeout=15)
        print("[+] SSH Connection successful!")
        
        stdin, stdout, stderr = ssh.exec_command("ls -la /root")
        print("\n=== /root directory ===")
        print(stdout.read().decode())
        
        stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service")
        print("\n=== systemd services ===")
        # Print first 30 lines
        lines = stdout.read().decode().splitlines()
        for line in lines[:50]:
            print(line)
            
        ssh.close()
    except Exception as e:
        print(f"[x] Failed: {str(e)}")

if __name__ == "__main__":
    list_remote()
