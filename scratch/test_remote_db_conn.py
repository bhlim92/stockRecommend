import pymysql
import sys

def test_conn():
    host = "bhlim123.cafe24.com"
    port = 3306
    user = "root"
    password = "cbm"
    db_name = "stock_db"
    
    print(f"[*] Testing connection to Cafe24 MariaDB ({host}:{port}/{db_name}) as {user}...")
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
            connect_timeout=10
        )
        print("[+] Connection successful!")
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"    - MariaDB Version: {version[0]}")
            
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"    - Tables in database: {[t[0] for t in tables]}")
        conn.close()
    except Exception as e:
        print(f"[x] Connection failed: {str(e)}")

if __name__ == "__main__":
    test_conn()
