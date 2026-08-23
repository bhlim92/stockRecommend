import paramiko
import os

def update():
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=username, password=password, timeout=15)
    
    sftp = ssh.open_sftp()
    
    local_path = os.path.join(os.path.dirname(__file__), "..", "app", "web_server.py")
    remote_path = "/root/stockRecommend/app/web_server.py"
    
    print(f"Uploading {local_path} to {remote_path}...")
    sftp.put(local_path, remote_path)
    sftp.close()
    
    commands = [
        "systemctl restart stock-recommend.service",
        "systemctl status stock-recommend.service --no-pager"
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err:
            print("ERR:", err)
            
    ssh.close()

if __name__ == "__main__":
    update()
