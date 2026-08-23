import sys

try:
    content = open('app/config.py', 'rb').read().decode('cp949', errors='replace')
    content = content.replace('@강환?', '@강환국"')
    open('app/config.py', 'w', encoding='utf-8').write(content)
    print("Fixed!")
except Exception as e:
    print(e)
