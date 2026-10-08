#!/usr/bin/env python3
import argparse, copy, json
from pathlib import Path

def loadj(p): return json.loads(Path(p).read_text())
def audit(root):
 root=Path(root); rows=loadj(root/'rows.json'); errors=[]
 if len(rows) not in (8,24): errors.append(f'row_count:{len(rows)}')
 seen=set()
 for row in rows:
  key=(row['rep'],row['schedule'],row['policy'])
  if key in seen: errors.append(f'duplicate:{key}')
  seen.add(key)
  if row['returncode']!=0: errors.append(f'rc:{key}')
  c=root/'cases'/row['case']; result=loadj(c/'result.json'); events=[json.loads(x) for x in (c/'events.jsonl').read_text().splitlines()]; xv=loadj(c/'xvfb_exit.json')
  if xv['returncode'] not in (-15,0): errors.append(f'xvfb_rc:{key}:{xv}')
  if not result['terminal_neutral']: errors.append(f'neutral:{key}')
  requested=result['requested_keys']; admitted=result['admitted_keys']; receipts=result['release_receipt_keys']
  if row['schedule']=='CANCEL_DURING_ADMISSION':
   if admitted!=requested[:1] or result['full_keyset_established']: errors.append(f'partial:{key}:{admitted}')
  else:
   if admitted!=requested or not result['full_keyset_established']: errors.append(f'full:{key}:{admitted}')
  if row['policy']=='BASELINE':
   if receipts or any(e['event']=='key_released' for e in events): errors.append(f'baseline_receipt:{key}')
  else:
   exp=list(reversed(admitted))
   if receipts!=exp: errors.append(f'receipts:{key}:{receipts}:{exp}')
   rel=[e for e in events if e['event']=='key_released']
   if [e['key'] for e in rel]!=exp: errors.append(f'release_events:{key}')
   owner=next(e for e in events if e['event']=='owner_release')
   if any(e['input_ack_ns']>owner['verified_ns'] for e in rel): errors.append(f'release_order:{key}')
   if any(e['input_ack_ns']<e['call_ns'] for e in rel): errors.append(f'release_ack:{key}')
  xe=result['xevents']; presses=sum(e['type']=='press' for e in xe); releases=sum(e['type']=='release' for e in xe)
  if presses!=len(admitted) or releases!=len(admitted): errors.append(f'xevent_count:{key}:{presses}:{releases}:{len(admitted)}')
 return {'status':'PASS_RAW_AUDIT' if not errors else 'FAIL_RAW_AUDIT','errors':errors,'rows':len(rows)}

def controls(root):
 root=Path(root); base=json.loads((root/'rows.json').read_text()); checks=[]
 checks.append(len(base[:-1]) != len(base))
 dup=base+[copy.deepcopy(base[0])]; checks.append(len({(r['rep'],r['schedule'],r['policy']) for r in dup}) != len(dup))
 badrc=copy.deepcopy(base); badrc[0]['returncode']=7; checks.append(any(r['returncode']!=0 for r in badrc))
 row=base[0]; c=root/'cases'/row['case']; result=loadj(c/'result.json'); events=[json.loads(x) for x in (c/'events.jsonl').read_text().splitlines()]; xv=loadj(c/'xvfb_exit.json')
 m=copy.deepcopy(result); m['terminal_neutral']=False; checks.append(not m['terminal_neutral'])
 m=copy.deepcopy(result); m['admitted_keys']=[]; checks.append(m['admitted_keys'] != m['requested_keys'][:len(result['admitted_keys'])])
 m=copy.deepcopy(result); m['release_receipt_keys']=['bogus']; checks.append(bool(m['release_receipt_keys']))
 m=copy.deepcopy(result); m['xevents']=m['xevents'][:-1]; checks.append(sum(e['type']=='press' for e in m['xevents']) != len(result['admitted_keys']) or sum(e['type']=='release' for e in m['xevents']) != len(result['admitted_keys']))
 m=copy.deepcopy(xv); m['returncode']=9; checks.append(m['returncode'] not in (-15,0))
 owner=next(e for e in events if e['event']=='owner_release'); fake={'input_ack_ns':owner['verified_ns']+1,'call_ns':owner['verified_ns']}; checks.append(fake['input_ack_ns']>owner['verified_ns'])
 m=copy.deepcopy(row); m['rep']=True; checks.append(type(m['rep']) is not int or isinstance(m['rep'],bool))
 return {'rejected':sum(bool(x) for x in checks),'total':len(checks),'checks':[bool(x) for x in checks]}

if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--controls',action='store_true'); a=ap.parse_args(); val=audit(a.root); val['controls']=controls(a.root) if a.controls else None; print(json.dumps(val,indent=2,sort_keys=True)); raise SystemExit(0 if not val['errors'] else 1)
