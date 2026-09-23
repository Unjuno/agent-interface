from pathlib import Path
import subprocess,os
r=Path('/home/taka/agent-interface-bench-feasibility')
for p in (r/'packages').glob('*.deb'):
 subprocess.run(['dpkg-deb','-x',str(p),str(r/'root')],check=True)
s=r/'root/usr/share/minetest'
if not s.exists(): s.symlink_to('games/minetest')
e=dict(os.environ,LD_LIBRARY_PATH=str(r/'root/usr/lib/x86_64-linux-gnu'))
for app in ['openttd','minetest']:
 p=subprocess.run(['ldd',str(r/'root/usr/games'/app)],env=e,capture_output=True,text=True)
 print(app,[s for s in p.stdout.splitlines() if 'not found' in s])
 p=subprocess.run([str(r/'root/usr/games'/app),'--help'],env=e,capture_output=True,text=True)
 (r/(app+'-help.txt')).write_text(p.stdout+p.stderr)
 print((p.stdout+p.stderr)[:3500])
