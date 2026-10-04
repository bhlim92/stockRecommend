"""
Database & Firewall Whitelist Manager for Production (Cafe24 VPS / MariaDB)
Provides an easy 1-click CLI for administrators to add, list, and remove allowed IPs.

Usage:
  python manage_db_whitelist.py add [IP]           # 특정 IP (또는 생략 시 현재 내 IP 자동 감지) 화이트리스트 등록
  python manage_db_whitelist.py list               # 현재 등록된 방화벽 및 DB 화이트리스트 목록 조회
  python manage_db_whitelist.py remove <IP>        # 특정 IP 화이트리스트에서 제거
  python manage_db_whitelist.py secure-lockdown    # 전체 허용('%') 계정 제거하여 화이트리스트 전용 모드로 잠금
"""

import sys
import os
import argparse
import requests
import paramiko

# Windows console UTF-8 support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Remote VPS Connection Config
REMOTE_HOST = os.getenv("REMOTE_HOST", "bhlim123.cafe24.com")
REMOTE_PORT = int(os.getenv("REMOTE_PORT", 22))
REMOTE_USER = os.getenv("REMOTE_USER", "root")
REMOTE_PASS = os.getenv("REMOTE_PASSWORD", "!monk9203!")
DB_PASS = os.getenv("REMOTE_DB_PASSWORD", "cbm")
DB_NAME = os.getenv("REMOTE_DB_NAME", "stock_db")

def get_my_public_ip() -> str:
    """Fetch current public IP address of administrator's machine."""
    services = [
        "https://api.ipify.org?format=json",
        "https://ifconfig.me/ip",
        "https://icanhazip.com"
    ]
    for url in services:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                if "json" in url:
                    return resp.json().get("ip", "").strip()
                return resp.text.strip()
        except Exception:
            continue
    raise RuntimeError("현재 공인 IP를 자동으로 조회할 수 없습니다. IP를 직접 입력해주세요.")

def get_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(REMOTE_HOST, port=REMOTE_PORT, username=REMOTE_USER, password=REMOTE_PASS, timeout=10)
    return ssh

def execute_remote(ssh, cmd: str) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    return exit_code, out, err

def add_ip_whitelist(ip: str = None, comment: str = "Admin"):
    if not ip or ip.lower() in ("my-ip", "me", "auto", ""):
        print("[INFO] 현재 관리자 공인 IP 확인 중...")
        ip = get_my_public_ip()
        print(f"[INFO] 감지된 관리자 공인 IP: {ip}")

    print(f"\n[1/2] 방화벽(UFW)에 {ip} 허용 규칙 등록 중...")
    ssh = get_ssh_client()
    
    # 1. Add UFW rule
    ufw_cmd = f"ufw allow from {ip} to any port 3306 proto tcp comment 'Whitelisted DB {comment}'"
    code, out, err = execute_remote(ssh, ufw_cmd)
    if code == 0 or "Rules updated" in out or "Rule added" in out or "Skipping adding existing rule" in out:
        print(f"  [OK] 방화벽(UFW): {ip} -> 3306 포트 허용 완료")
    else:
        print(f"  [WARN] UFW: {out or err}")

    # 2. Add MariaDB user
    print(f"[2/2] MariaDB 계정 권한 등록 중 ('root'@'{ip}')...")
    sql = f"""
    CREATE USER IF NOT EXISTS 'root'@'{ip}' IDENTIFIED BY '{DB_PASS}';
    GRANT ALL PRIVILEGES ON *.* TO 'root'@'{ip}' WITH GRANT OPTION;
    FLUSH PRIVILEGES;
    """
    db_cmd = f"mysql -u root -p{DB_PASS} -e \"{sql.strip()}\""
    code, out, err = execute_remote(ssh, db_cmd)
    if code == 0:
        print(f"  [OK] MariaDB: 'root'@'{ip}' 권한 부여 완료")
    else:
        print(f"  [ERROR] MariaDB 오류: {err}")

    ssh.close()
    print(f"\n[성공] 이제 IP [{ip}] 에서 원격 데이터베이스에 즉시 접속할 수 있습니다.")

def list_whitelist():
    print(f"==================================================")
    print(f" [화이트리스트 현황 조회] {REMOTE_HOST}")
    print(f"==================================================\n")
    ssh = get_ssh_client()

    print("[1] OS 방화벽 (UFW 3306 포트 허용 규칙):")
    code, out, err = execute_remote(ssh, "ufw status numbered | grep 3306 || echo '  (등록된 3306 규칙 없음)'")
    print(out if out else "  (조회 결과 없음)")

    print("\n[2] MariaDB 등록된 유저 및 허용 호스트:")
    sql = "SELECT user, host FROM mysql.user WHERE user='root';"
    code, out, err = execute_remote(ssh, f"mysql -u root -p{DB_PASS} -e \"{sql}\"")
    if code == 0:
        print(out)
    else:
        print(f"  [ERROR] MariaDB 조회 오류: {err}")

    ssh.close()
    print(f"\n==================================================")

def remove_ip_whitelist(ip: str):
    if not ip:
        print("[ERROR] 제거할 IP를 입력해주세요. 예: python manage_db_whitelist.py remove 123.45.67.89")
        return

    print(f"[진행] IP [{ip}] 화이트리스트 제거 작업 시작...")
    ssh = get_ssh_client()

    # 1. Remove UFW
    ufw_cmd = f"ufw delete allow from {ip} to any port 3306 proto tcp"
    code, out, err = execute_remote(ssh, ufw_cmd)
    print(f"  방화벽: {out or err}")

    # 2. Drop MariaDB user
    sql = f"DROP USER IF EXISTS 'root'@'{ip}'; FLUSH PRIVILEGES;"
    db_cmd = f"mysql -u root -p{DB_PASS} -e \"{sql}\""
    code, out, err = execute_remote(ssh, db_cmd)
    if code == 0:
        print(f"  MariaDB: 'root'@'{ip}' 사용자 삭제 완료")
    else:
        print(f"  [ERROR] MariaDB 오류: {err}")

    ssh.close()
    print(f"[성공] IP [{ip}] 가 화이트리스트에서 제거되었습니다.")

def secure_lockdown():
    print("==================================================")
    print(" [보안 잠금] 전체 오픈('%') 계정 제거 및 화이트리스트 모드 전환")
    print("==================================================")
    confirm = input("경고: 'root'@'%' 계정을 삭제하면 화이트리스트에 등록되지 않은 IP는 모두 차단됩니다. 계속하시겠습니까? (y/N): ")
    if confirm.lower() != 'y':
        print("작업이 취소되었습니다.")
        return

    ssh = get_ssh_client()
    
    # 1. Add current admin IP first to avoid lockout
    my_ip = get_my_public_ip()
    print(f"\n[안전장치] 관리자 차단 방지를 위해 현재 접속 IP ({my_ip})를 먼저 등록합니다.")
    add_ip_whitelist(my_ip, "Admin-SafeLock")

    # 2. Drop root@%
    print("\n[진행] 'root'@'%' 전체 허용 계정 삭제 중...")
    sql = "DROP USER IF EXISTS 'root'@'%'; FLUSH PRIVILEGES;"
    db_cmd = f"mysql -u root -p{DB_PASS} -e \"{sql}\""
    code, out, err = execute_remote(ssh, db_cmd)
    if code == 0:
        print("  [OK] 'root'@'%' 계정 삭제 완료 (등록된 화이트리스트 IP만 접속 허용됨)")
    else:
        print(f"  [ERROR] MariaDB 오류: {err}")

    ssh.close()
    print("\n[성공] 보안 잠금 완료! 오직 등록된 화이트리스트 IP에서만 접속이 허용됩니다.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MariaDB & Firewall Whitelist Manager")
    subparsers = parser.add_subparsers(dest="command", help="명령어")

    # add
    add_parser = subparsers.add_parser("add", help="IP 화이트리스트 추가 (IP 생략 시 현재 내 IP 자동 감지)")
    add_parser.add_argument("ip", nargs="?", default=None, help="추가할 IP (생략 시 현재 내 IP 자동 감지)")
    add_parser.add_argument("--comment", default="Admin", help="설명 메모")

    # list
    subparsers.add_parser("list", help="현재 등록된 화이트리스트 목록 조회")

    # remove
    remove_parser = subparsers.add_parser("remove", help="IP 화이트리스트 제거")
    remove_parser.add_argument("ip", help="제거할 IP")

    # secure-lockdown
    subparsers.add_parser("secure-lockdown", help="전체 허용 계정(%) 삭제 및 화이트리스트 전용 잠금")

    if len(sys.argv) == 1:
        # Default behavior: interactive / add current IP
        add_ip_whitelist()
    else:
        args = parser.parse_args()
        if args.command == "add":
            add_ip_whitelist(args.ip, args.comment)
        elif args.command == "list":
            list_whitelist()
        elif args.command == "remove":
            remove_ip_whitelist(args.ip)
        elif args.command == "secure-lockdown":
            secure_lockdown()
        else:
            parser.print_help()
