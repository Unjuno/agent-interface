#!/usr/bin/env python3
import argparse,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--display-base',type=int,default=181);ap.add_argument('--pipe-prefix',default='aicasformal');a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);blocks=[]
 for i in range(4):
  d=out/f'block-{i+1:02d}';p=subprocess.run([sys.executable,str(HERE/'run_block.py'),'--out',str(d),'--display',f':{a.display_base+i}','--pipe',f'{a.pipe_prefix}{i}','--block',str(i+1)],text=True,capture_output=True);(out/f'block-{i+1:02d}.stdout').write_text(p.stdout);(out/f'block-{i+1:02d}.stderr').write_text(p.stderr);rep=json.loads((d/'report.json').read_text()) if (d/'report.json').exists() else None;blocks.append({'block':i+1,'exitcode':p.returncode,'report':rep})
 summary={'schema':'agent-interface/writer-uno-compare-replace-matrix-v1','blocks':blocks,'passed':len(blocks)==4 and all(b['exitcode']==0 and b['report'] and b['report']['passed'] for b in blocks)};(out/'aggregate.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary));return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
