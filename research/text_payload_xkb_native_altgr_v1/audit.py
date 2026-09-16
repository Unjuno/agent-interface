from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from Xlib import XK
HERE=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def parse(text):
 codes={m.group(1):int(m.group(2)) for m in re.finditer(r'<([^>]+)>\s*=\s*(\d+)\s*;',text)};table={};raw={};shift=level3=0
 for m in re.finditer(r'key\s+<([^>]+)>\s*\{(.*?)\};',text,re.S):
  name,body=m.group(1),m.group(2);code=codes.get(name);sm=re.search(r'symbols\[Group1\]\s*=\s*\[(.*?)\]',body,re.S) or re.search(r'\[(.*?)\]',body,re.S)
  if code is None or not sm:continue
  vals=[]
  for tok in [x.strip() for x in sm.group(1).split(',')][:4]:
   if tok in ('','NoSymbol','VoidSymbol'):vals.append(0);continue
   k=XK.string_to_keysym(tok);vals.append(int(k if k or len(tok)!=1 else ord(tok)))
  while len(vals)<4:vals.append(0)
  raw[code]=vals
  if vals[0]==XK.string_to_keysym('Shift_L'):shift=code
  if vals[0]==XK.string_to_keysym('ISO_Level3_Shift'):level3=code
  for lev,k in enumerate(vals):
   if not 32<=k<=126:continue
   cand={'code':code,'level':lev,'shift':lev in (1,3),'level3':lev in (2,3)};rank=(int(cand['level3'])+int(cand['shift']),int(cand['level3']),int(cand['shift']),code,lev);old=table.get(chr(k))
   if old is None or rank<old[0]:table[chr(k)]=(rank,cand)
 return table,shift,level3,raw
def req(x,m):
 if not x:raise AssertionError(m)
def main(root):
 sched_b=(HERE/'schedule.json').read_bytes();sched=json.loads(sched_b);pre=json.loads((HERE/'prereg.json').read_text());req(sha(sched_b)==pre['schedule_sha256'],'schedule drift')
 for n,h in pre['source_sha256'].items():req(sha((HERE/n).read_bytes())==h,f'source drift {n}')
 all_trials=[];summ=[]
 for rep in range(3):
  d=root/f'rep-{rep}';r=json.loads((d/'report.json').read_text());req(r['decision']=='PASS_XDUMMY_NATIVE_ALTGR_DELIVERY_SCOPED',f'arm decision {rep}');req(r['resolved_sha256']==pre['resolved_sha256'],f'resolved receipt {rep}');live=(d/'live.server.xkb').read_bytes();req(sha(live)==r['live_xkb_sha256'],f'live hash {rep}');table,shift,l3,raw=parse(live.decode());req(shift and l3,'modifier keycodes unavailable');mods=r['initial_modifier_mapping'];req(shift in mods[0],'shift not modifier');req(l3 in mods[7],'level3 not Mod5')
  direct=set(sched['expected_candidate_direct_recovered_single_chars']);req(all(c in table and table[c][1]['level'] in (2,3) for c in direct),'recovery set not direct level3');req(all(c not in table for c in sched['expected_candidate_dead_key_refusals_single_chars']),'dead key became direct')
  req(r['final']['xkb']==r['live_xkb_sha256'],'final xkb drift');req(r['final']['core']==r['initial_core_sha256'],'final core drift');req(r['final']['modifier']==r['initial_modifier_sha256'],'final mod drift');req(not r['final']['physical']['keys'] and r['final']['physical']['mask']==0,'final physical')
  req(len(r['trials'])==16,'trial count');em_total=0
  for tr in r['trials']:
   text=tr['payload'];exp=all(ch in table for ch in text);rec=tr['candidate'];req(tr['expected_accept']==exp,'runner classification');req(rec['accepted']==exp,'accept mismatch');req(tr['xkb_after_sha256']==r['live_xkb_sha256'],'trial xkb drift');req(tr['core_after_sha256']==r['initial_core_sha256'],'trial core drift');req(tr['modifier_after_sha256']==r['initial_modifier_sha256'],'trial mod drift');req(rec.get('release_verified') is True,'release');req(not tr['physical_after']['keys'] and tr['physical_after']['mask']==0,'trial physical')
   if exp:
    req(tr['actual']==text,'wrong text');req(len(rec['strokes'])==len(text),'stroke count');expected_em=0
    for ch,st in zip(text,rec['strokes']):
     want=table[ch][1];req(int(st['code'])==want['code'] and int(st['level'])==want['level'],'stroke identity');req(bool(st['shift'])==want['shift'] and bool(st['level3'])==want['level3'],'stroke flags');expected_em+=2+2*int(want['shift'])+2*int(want['level3'])
    req(rec['emissions']==expected_em,'emissions');em_total+=expected_em
   else:
    req(tr['actual']=='' and rec['emissions']==0,'reject side effect');req(rec.get('preflight_rejected') is True,'reject not preflight')
   req(tr['gate'] is True,'gate false');all_trials.append((rep,text,exp))
  req(r['input_operations']==em_total,'arm emission total');summ.append({'rep':rep,'emissions':em_total,'live_xkb_sha256':r['live_xkb_sha256']})
 req(len(all_trials)==48,'formal total');out={'status':'PASS_INDEPENDENT_AUDIT','decision':'PASS_XDUMMY_NATIVE_ALTGR_DELIVERY_SCOPED','formal_trials':48,'eligible':sum(x[2] for x in all_trials),'refused':sum(not x[2] for x in all_trials),'arms':summ};(root/'audit_summary.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out));return 0
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);raise SystemExit(main(p.parse_args().root))
