import subprocess,sys,json
from pathlib import Path
p=subprocess.run(['/usr/bin/python3','/workspace/research/integration/mixed_app_long_session_2499/formal_session.py'],text=True,capture_output=True)
Path('/out/result.json').write_text(p.stdout)
Path('/out/stderr.log').write_text(p.stderr)
Path('/out/exit.txt').write_text(str(p.returncode)+'\n')
print(p.stdout)
sys.exit(p.returncode)

