import paramiko

def fetch_remote_logs():
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=port, username=username, password=password, timeout=15)
        print("[+] SSH Connection successful!")
        
        # Read remote screener.log tail
        print("=== Remote logs/screener.log tail ===")
        stdin, stdout, stderr = ssh.exec_command("tail -n 40 /root/stockRecommend/logs/screener.log")
        print(stdout.read().decode())
        
        # Read remote app.log tail (database related)
        print("=== Remote logs/app.log tail (database related) ===")
        stdin, stdout, stderr = ssh.exec_command("grep -i -E 'database|db|error|save' /root/stockRecommend/logs/app.log | tail -n 40")
        print(stdout.read().decode())
        
        ssh.close()
    except Exception as e:
        print(f"[x] Connection or command failed: {str(e)}")

if __name__ == "__main__":
    fetch_remote_logs()
