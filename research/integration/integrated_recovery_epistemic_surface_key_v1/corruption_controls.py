from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path
from audit import verify

def write(rows,p): p.write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in rows))
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--rows",required=True); ap.add_argument("--focus-archive",required=True); ap.add_argument("--modal-archive",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
 rows=[json.loads(x) for x in Path(a.rows).read_text().splitlines() if x]
 results={}
 with tempfile.TemporaryDirectory() as td:
  td=Path(td)
  x=json.loads(json.dumps(rows)); x[0]["classification"]="EXACT_MATCH"; p=td/'class.jsonl'; write(x,p); results['forged_classification_rejected']=not verify(p,a.focus_archive,a.modal_archive)['audit_pass']
  x=json.loads(json.dumps(rows)); target=next(r for r in x if r['cohort']=='855'); target['receipt']['identity']['transient_for']={"state":"KNOWN_NULL"}; p=td/'launder.jsonl'; write(x,p); results['unknown_to_null_rejected']=not verify(p,a.focus_archive,a.modal_archive)['audit_pass']
  x=json.loads(json.dumps(rows)); x[0]['task_input_granted']=True; p=td/'authority.jsonl'; write(x,p); results['authority_escalation_rejected']=not verify(p,a.focus_archive,a.modal_archive)['audit_pass']
 out={"controls":results,"pass":all(results.values())}; Path(a.out).write_text(json.dumps(out,sort_keys=True,indent=2)+"\n"); print(json.dumps(out,sort_keys=True))
if __name__=="__main__":main()
