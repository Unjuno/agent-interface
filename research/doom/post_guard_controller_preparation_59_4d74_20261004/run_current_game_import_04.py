from pathlib import Path
import subprocess,json,time
root=Path(__file__).resolve().parent;out=root/'current-game-import-04';out.mkdir(exist_ok=False)
args=['C:/Program Files/WSL/wslc.exe','run','--name','current-game-import-59-4d74-04','--pull','never','--cpus','1','--memory','512M','--network','none','--user','65534','--env','HOME=/tmp','--mount',f'type=bind,source={root},target=/study,readonly','--mount',f'type=bind,source={out},target=/out',(root/'image-02/image.id').read_text().strip(),'/usr/local/bin/python3','/study/qualify_current_game_import_04.py']
(out/'argv.json').write_text(json.dumps(args,indent=2));start=time.monotonic()
with (out/'stdout.txt').open('wb') as so,(out/'stderr.txt').open('wb') as se:
 p=subprocess.run(args,stdout=so,stderr=se,timeout=45)
(out/'HOST.json').write_text(json.dumps({'exit':p.returncode,'elapsed_s':time.monotonic()-start,'scope':'no game/model/input starts'},indent=2));print((out/'stdout.txt').read_text());print((out/'stderr.txt').read_text());raise SystemExit(p.returncode)
