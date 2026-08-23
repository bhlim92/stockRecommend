import paramiko

def read_remote_env():
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=port, username=username, password=password, timeout=15)
        print("[+] SSH Connection successful!")
        
        # Read remote .env
        stdin, stdout, stderr = ssh.exec_command("cat /root/stockRecommend/.env")
        print("\n=== Remote Server .env file ===")
        print(stdout.read().decode())
        
        ssh.close()
    except Exception as e:
        print(f"[x] Failed to read remote env: {str(e)}")

if __name__ == "__main__":
    read_remote_env()
