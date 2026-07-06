import urllib.request
urls=['/','/pages/login.html','/pages/admin.html','/pages/manager.html','/pages/products.html','/pages/sales.html','/index.html']
base='http://127.0.0.1:8080'
for u in urls:
    try:
        with urllib.request.urlopen(base+u, timeout=5) as r:
            body=r.read()
            print(u, r.status, len(body))
    except Exception as e:
        print(u, 'error', e)
