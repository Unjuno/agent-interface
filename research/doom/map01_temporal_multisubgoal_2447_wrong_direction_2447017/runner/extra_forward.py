from pathlib import Path
import argparse,json
from common import Inputs,write

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--ctx',required=True);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=False);ctx=json.loads(Path(a.ctx).read_text());events=[];inp=Inputs(a.source,ctx,events)
 try:
  inp.press('w',.35,.02,'extra_forward');write(out/'result.json',{'extra_forward_issued':True});write(out/'owner-records.json',inp.owner.records);write(out/'events.json',events)
 finally:inp.close()
if __name__=='__main__':main()
