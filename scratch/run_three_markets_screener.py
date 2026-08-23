import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dotenv
dotenv.load_dotenv()

from app.database import engine, ScreenerResult, SessionLocal, init_db, Base
from app.screener import ScreenerManager

def main():
    print("[*] Initializing Database...")
    if not init_db():
        print("[!] Database initialization failed.")
        sys.exit(1)
        
    db = SessionLocal()
    try:
        print("[*] Clearing DB screener_results table...")
        num_deleted = db.query(ScreenerResult).delete()
        db.commit()
        print(f"[+] Successfully deleted {num_deleted} rows.")
    except Exception as e:
        db.rollback()
        print(f"[!] Error deleting rows: {str(e)}")
        # Recreate table as fallback
        try:
            print("[*] Dropping and recreating screener_results table...")
            ScreenerResult.__table__.drop(bind=engine)
            Base.metadata.create_all(bind=engine)
            print("[+] Table recreated.")
        except Exception as ex:
            print(f"[!] Recreate failed: {str(ex)}")
            sys.exit(1)
    finally:
        db.close()
        
    # Run screener for the 3 markets
    manager = ScreenerManager()
    
    markets = ["sp500", "kospi200", "kosdaq"]
    for m in markets:
        print(f"\n[*] Starting screening for market: {m}")
        try:
            # Run synchronously in this thread
            manager._run_screener_worker(m)
            print(f"[+] Completed screening for {m}")
        except Exception as e:
            print(f"[!] Error screening {m}: {str(e)}")
            
    print("\n[+] All tasks finished successfully!")

if __name__ == "__main__":
    main()
