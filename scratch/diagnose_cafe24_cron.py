import paramiko

def diagnose():
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=port, username=username, password=password, timeout=15)
        print("[+] SSH Connection successful!")
        
        # 1. Check Date and Timezone
        stdin, stdout, stderr = ssh.exec_command("date")
        print("\n=== Remote Server Date and Time ===")
        print(stdout.read().decode().strip())
        
        # 2. Check Crontab
        stdin, stdout, stderr = ssh.exec_command("crontab -l")
        print("\n=== Remote Server Crontab ===")
        print(stdout.read().decode().strip())
        err = stderr.read().decode().strip()
        if err:
            print(f"Error reading crontab: {err}")
            
        # 3. Check Scheduler Log (last 20 lines)
        stdin, stdout, stderr = ssh.exec_command("tail -n 20 /root/stockRecommend/logs/scheduler.log")
        print("\n=== Remote Scheduler Log (Last 20 lines) ===")
        print(stdout.read().decode().strip())
        
        # 4. Check App Log (last 20 lines)
        stdin, stdout, stderr = ssh.exec_command("tail -n 20 /root/stockRecommend/logs/app.log")
        print("\n=== Remote App Log (Last 20 lines) ===")
        print(stdout.read().decode().strip())
        
        ssh.close()
    except Exception as e:
        print(f"[x] Diagnosis failed: {str(e)}")

if __name__ == "__main__":
    diagnose()
