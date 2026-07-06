import urllib.request

url = 'http://127.0.0.1:8080/services/api.js'
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        text = r.read().decode('utf-8')
        print('URL:', url)
        print('First 20 lines:')
        for i, line in enumerate(text.splitlines()[:20], start=1):
            print(f'{i}: {line}')
except Exception as e:
    print('ERROR', e)
