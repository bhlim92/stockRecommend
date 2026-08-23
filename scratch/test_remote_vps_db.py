import paramiko

def test_vps_db():
    host = "bhlim123.cafe24.com"
    port = 22
    username = "root"
    password = "!monk9203!"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"[*] Connecting to Cafe24 VPS via SSH ({host}:{port}) to test database locally...")
    try:
        ssh.connect(host, port=port, username=username, password=password, timeout=15)
        print("[+] SSH connection successful.")
        
        # 1. Check if mariadb service is running
        print("\n[*] Checking MariaDB service status on VPS...")
        stdin, stdout, stderr = ssh.exec_command("systemctl status mariadb | grep Active")
        print(f"    - Status: {stdout.read().decode().strip()}")
        
        # 2. Run local mysql command to query databases and tables
        print("\n[*] Querying database list locally on VPS...")
        stdin, stdout, stderr = ssh.exec_command("mysql -u root -pcbm -e 'SHOW DATABASES;'")
        print("    - Databases found:\n" + stdout.read().decode().strip())
        
        # 3. Query tables in stock_db
        print("\n[*] Querying tables in 'stock_db' database...")
        stdin, stdout, stderr = ssh.exec_command("mysql -u root -pcbm -e 'USE stock_db; SHOW TABLES;'")
        print("    - Tables found:\n" + stdout.read().decode().strip())
        
        # 4. Check row count in screener_results
        print("\n[*] Querying row count in 'screener_results'...")
        stdin, stdout, stderr = ssh.exec_command("mysql -u root -pcbm -e 'USE stock_db; SELECT COUNT(*) FROM screener_results;'")
        print("    - Row count:\n" + stdout.read().decode().strip())
        
        ssh.close()
        print("\n[+] Local database tests on Cafe24 VPS completed successfully!")
    except Exception as e:
        print(f"[x] Local VPS DB test failed: {str(e)}")

if __name__ == "__main__":
    test_vps_db()
