import ssl
import urllib.request

url = 'https://bba2be68998d9248-189-84-176-250.serveousercontent.com'
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    r = urllib.request.urlopen(url, context=ctx, timeout=10)
    print('STATUS', r.status)
    print(r.read(200).decode('utf-8', errors='replace'))
except Exception as e:
    print(type(e).__name__, e)
