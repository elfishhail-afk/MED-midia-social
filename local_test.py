import urllib.request

try:
    r = urllib.request.urlopen('http://127.0.0.1:5000', timeout=10)
    print('STATUS', r.status)
    print(r.read(80).decode('utf-8', errors='replace'))
except Exception as e:
    print(type(e).__name__, e)
