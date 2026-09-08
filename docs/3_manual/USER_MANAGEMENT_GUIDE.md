# 사용자 및 접근 권한 관리 매뉴얼 (User Management Guide)

본 문서는 **1) 웹 대시보드 로그인 사용자(Google OAuth 이메일)** 및 **2) 데이터베이스 접근 IP 화이트리스트**를 추가, 갱신, 삭제하는 방법을 설명합니다.

---

## 1. 웹 대시보드 사용자 관리 (Google OAuth 이메일)

웹 대시보드는 허용된 Google 이메일 목록(`AUTHORIZED_EMAILS`)에 등록된 사용자만 로그인하여 투자 리포트 조회 및 포트폴리오를 관리할 수 있습니다.

### 📌 사용자 추가 (Add User)
새로운 사용자를 추가하려면 `.env` 파일의 `AUTHORIZED_EMAILS` 항목에 이메일을 쉼표(`,`)로 구분하여 추가합니다.

* **로컬 환경 / `.env` 파일**:
  ```ini
  # 기존: bumhyun.lim@gmail.com
  # 신규 추가: kapi123@gmail.com
  AUTHORIZED_EMAILS=bumhyun.lim@gmail.com,kapi123@gmail.com
  ```

* **원격 Cafe24 프로덕션 서버에 반영할 때**:
  1. 원격 서버의 `/root/stockRecommend/.env` 파일 수정:
     ```bash
     ssh root@bhlim123.cafe24.com
     nano /root/stockRecommend/.env
     ```
     `AUTHORIZED_EMAILS=bumhyun.lim@gmail.com,kapi123@gmail.com` 로 수정 후 `Ctrl+O`, `Enter`, `Ctrl+X` 저장.
  2. 웹 서비스 재시작:
     ```bash
     systemctl restart stock_web
     ```

---

### 📌 사용자 갱신 / 변경 (Update User)
기존 사용자의 이메일 주소가 바뀌었거나 권한 명단을 변경할 때는 `.env`의 이메일 값을 직접 수정한 뒤 서비스를 재시작합니다.

```ini
AUTHORIZED_EMAILS=bumhyun.lim@gmail.com,new_account@gmail.com
```

---

### 📌 사용자 삭제 / 권한 회수 (Delete User)
퇴사자나 권한을 회수할 사용자는 목록에서 해당 이메일만 제거합니다.

```ini
# kapi123@gmail.com 제거
AUTHORIZED_EMAILS=bumhyun.lim@gmail.com
```
* 저장 후 서비스를 재시작하면 해당 사용자의 기존 세션 토큰 및 신규 로그인이 즉시 **401/403 차단**됩니다.

---

## 2. 데이터베이스 & 방화벽 접근 관리자 (IP 화이트리스트)

프로덕션 MariaDB(포트 3306)에 원격으로 접속할 수 있는 IP를 관리합니다.

### 📌 IP 추가 (Add IP)

#### 방법 A: 배치 파일 (가장 간편)
* **`add_whitelist.bat`** 더블 클릭 (현재 내 PC IP 자동 감지 및 등록)

#### 방법 B: CLI 명령어
```bash
# 1. 현재 내 PC IP 자동 감지하여 등록
python manage_db_whitelist.py add

# 2. 특정 IP 직접 지정하여 등록
python manage_db_whitelist.py add 182.221.146.85 --comment "HomePC"
```

---

### 📌 등록 현황 조회 (List Whitelist)
현재 방화벽(UFW) 및 MariaDB에 등록되어 있는 모든 IP 목록을 실시간으로 확인합니다.

```bash
python manage_db_whitelist.py list
```

출력 예시:
```text
[1] OS 방화벽 (UFW 3306 포트 허용 규칙):
[ 1] 3306/tcp ALLOW IN 182.221.146.85 # Whitelisted DB Admin

[2] MariaDB 등록된 유저 및 허용 호스트:
User    Host
root    localhost
root    182.221.146.85
```

---

### 📌 IP 갱신 (Update IP)
인터넷 재접속 등으로 공인 IP가 변경된 경우:
1. `add_whitelist.bat`를 실행하거나 `python manage_db_whitelist.py add`를 실행하여 새 IP를 등록합니다.
2. 이전 구 IP는 아래 삭제 명령어로 정리합니다.

---

### 📌 IP 삭제 (Delete IP)
더 이상 접근이 불필요한 IP를 방화벽과 MariaDB에서 완전히 제거합니다.

```bash
python manage_db_whitelist.py remove 182.221.146.85
```

---

### 📌 전체 잠금 모드 (Secure Lockdown)
와일드카드(`'root'@'%'`) 전체 허용 계정을 삭제하고, 오직 등록된 화이트리스트 IP만 접속 가능하도록 보안을 강화합니다.

```bash
python manage_db_whitelist.py secure-lockdown
```
