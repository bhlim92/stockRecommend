import paramiko

def run_remote_dry_run():
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=port, username=username, password=password, timeout=15)
        print("[+] SSH Connection successful!")
        
        cmd = "cd /root/stockRecommend && ./venv/bin/python main.py --dry-run"
        print(f"[*] Running remote command: {cmd}")
        print("[*] This might take a minute, please wait...")
        
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        # Read output stream as it becomes available
        exit_status = stdout.channel.recv_exit_status()
        print(f"[+] Remote process exited with status: {exit_status}")
        
        out = stdout.read().decode()
        err = stderr.read().decode()
        
        if out:
            print("\n=== Remote Stdout ===")
            print(out)
        if err:
            print("\n=== Remote Stderr ===")
            print(err)
            
        # Also print last 20 lines of remote scheduler.log to verify logging
        print("\n=== Remote logs/scheduler.log tail ===")
        stdin, stdout, stderr = ssh.exec_command("tail -n 20 /root/stockRecommend/logs/scheduler.log")
        print(stdout.read().decode().strip())
        
        ssh.close()
    except Exception as e:
        print(f"[x] Remote dry-run execution failed: {str(e)}")

if __name__ == "__main__":
    run_remote_dry_run()
