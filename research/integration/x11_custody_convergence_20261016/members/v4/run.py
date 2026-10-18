import datetime, hashlib, json, os, pathlib, subprocess, sys

P = pathlib.Path(__file__).resolve().parent
label, arm, route = sys.argv[1:4]
dest = P/label
dest.mkdir(exist_ok=False)
sha = lambda b: hashlib.sha256(b).hexdigest()
utc = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
files = list((P/'sources'/arm).rglob('*')) + [P/'check.py', P/'run.py']
files += list((P.parent/'x11-package-import-01a0ff2c/dependencies').glob('*.whl'))
pins = {str(f.resolve()):sha(f.read_bytes()) for f in files if f.is_file()}
argv = [sys.executable,'-X','utf8','-B']+(['-O'] if label.endswith('-O') else [])+[str(P/'check.py'),arm,route]
start = utc()
child = subprocess.Popen(argv, cwd=P, env=dict(os.environ,PYTHONIOENCODING='utf8'),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
receipt = {'argv':argv,'pid':child.pid,'supervisor_pid':os.getpid(),'start':start,'pins':pins,'arm':arm,'route':route}
(dest/'START.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
try:
    out,err = child.communicate(timeout=30)
    timeout = False
except subprocess.TimeoutExpired:
    child.kill()
    out,err = child.communicate()
    timeout = True
(dest/'stdout.txt').write_bytes(out)
(dest/'stderr.txt').write_bytes(err)
receipt.update(end=utc(),exit=child.returncode,timeout=timeout,pins_unchanged=all(sha(pathlib.Path(f).read_bytes())==v for f,v in pins.items()),streams={name:{'bytes':len(raw),'sha256':sha(raw)} for name,raw in [('stdout.txt',out),('stderr.txt',err)]})
(dest/'RESULT.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
print(json.dumps({k:v for k,v in receipt.items() if k!='pins'}))
print(err.decode('utf8'))
sys.exit(child.returncode)
