import sys
import re

try:
    with open('app/config.py', 'rb') as f:
        content_bytes = f.read()
    
    # Force decode ignoring errors
    content = content_bytes.decode('utf-8', errors='ignore')
    
    # Fix the corrupted korean text
    content = content.replace('@강환?', '@강환국"')
    
    with open('app/config.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Fixed!")
except Exception as e:
    print("Error:", e)
