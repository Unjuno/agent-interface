import json,subprocess,sys,importlib.metadata
import PIL,Xlib,jsonschema
code='WSLC_CHROMIUM_PREREQUISITE_57'
html='data:text/html,<title>'+code+'</title><p>'+code+'</p>'
p=subprocess.run(['chromium','--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-first-run','--no-default-browser-check','--disable-background-networking','--user-data-dir=/tmp/chromium-prerequisite','--dump-dom',html],capture_output=True,text=True,timeout=30)
print(json.dumps({'python':sys.executable,'versions':{k:importlib.metadata.version(k) for k in ['Pillow','python-xlib','jsonschema']},'chromium_exit':p.returncode,'expected_dom':code in p.stdout,'stdout':p.stdout,'stderr':p.stderr}))
raise SystemExit(0 if p.returncode==0 and code in p.stdout else 1)
