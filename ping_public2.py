import urllib.request
from urllib.error import HTTPError, URLError

url = 'https://bba2be68998d9248-189-84-176-250.serveousercontent.com'
try:
    r = urllib.request.urlopen(url, timeout=10)
    print('STATUS', r.status)
    print(r.read(200).decode('utf-8', errors='replace'))
except HTTPError as e:
    print('HTTPError', e.code, e.reason)
except URLError as e:
    print('URLError', e.reason)
except Exception as e:
    print(type(e).__name__, e)
