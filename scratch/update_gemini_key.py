import os
import sys
import paramiko

def update_gemini_api_key(new_key):
    new_key = new_key.strip()
    if not new_key.startswith("AIzaSy"):
        print("[!] Warning: The API key does not start with standard prefix 'AIzaSy'. Please make sure it is correct.")
        
    local_env_path = r"c:\Users\samsung\proj\stockRecommend\.env"
    
    # 1. Update local .env
    print(f"[*] Updating local .env at: {local_env_path}")
    if os.path.exists(local_env_path):
        with open(local_env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        updated_lines = []
        key_found = False
        for line in lines:
            if line.strip().startswith("GEMINI_API_KEY="):
                updated_lines.append(f"GEMINI_API_KEY={new_key}\n")
                key_found = True
            else:
                updated_lines.append(line)
        
        if not key_found:
            updated_lines.append(f"\nGEMINI_API_KEY={new_key}\n")
            
        with open(local_env_path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)
        print("[+] Local .env updated successfully.")
    else:
        print("[x] Local .env file not found!")
        return

    # 2. Update remote .env on Cafe24
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    print(f"[*] Connecting to remote server {host}:{port}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=port, username=username, password=password, timeout=15)
        print("[+] SSH Connection successful!")
        
        # Read remote .env
        stdin, stdout, stderr = ssh.exec_command("cat /root/stockRecommend/.env")
        remote_env = stdout.read().decode()
        
        # We can update the remote env by replacing the GEMINI_API_KEY line.
        # Use sed to update the line or replace it.
        # Escape any special characters in new_key if needed, but standard Gemini keys are alphanumeric and dashes.
        escaped_key = new_key.replace("&", "\\&").replace("/", "\\/")
        sed_cmd = f"sed -i 's/^GEMINI_API_KEY=.*/GEMINI_API_KEY={escaped_key}/' /root/stockRecommend/.env"
        print(f"[*] Running remote update command: {sed_cmd}")
        stdin, stdout, stderr = ssh.exec_command(sed_cmd)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("[+] Remote .env updated successfully.")
        else:
            print(f"[x] Remote update failed (exit code: {exit_status}). Error: {stderr.read().decode()}")
            
        # Verify the remote .env change
        stdin, stdout, stderr = ssh.exec_command("grep '^GEMINI_API_KEY=' /root/stockRecommend/.env")
        print(f"Verify remote: {stdout.read().decode().strip()}")
        
        # Restart service if any to apply env changes
        ssh.exec_command("systemctl restart stock-recommend || systemctl restart fastapi || pm2 restart all || killall uvicorn")
        print("[+] Remote service restart command triggered.")
        
        ssh.close()
    except Exception as e:
        print(f"[x] Remote SSH update failed: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_gemini_key.py <NEW_GEMINI_API_KEY>")
        sys.exit(1)
        
    update_gemini_api_key(sys.argv[1])
