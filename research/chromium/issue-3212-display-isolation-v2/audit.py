import json,sys
from pathlib import Path

REQUIRED={'control','display','profile','old_generation','generation','old_process_start_ns','process_start_ns','cdp_browser','cdp_target','chromium_pid','x11_windows','dispatch','dom_effect'}
CONTROLS={'stale_xid','old_process','positive_p2_effect'}

def main(path):
 rows=[json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]; errors=[]; seen=set()
 for r in rows:
  c=r.get('control'); seen.add(c); miss=sorted(REQUIRED-r.keys())
  if miss: errors.append(f'{c}: missing={miss}'); continue
  corr=(r['cdp_browser'].get('pid')==r['chromium_pid'] and r['cdp_target'].get('display')==r['display'] and r['cdp_target'].get('profile')==r['profile'] and any(w.get('pid')==r['chromium_pid'] and w.get('display')==r['display'] for w in r['x11_windows']))
  if c!='positive_p2_effect' and r['dispatch']: errors.append(f'{c}: forbidden dispatch')
  if r['dispatch'] and not corr: errors.append(f'{c}: identity correlation')
  if c=='positive_p2_effect' and not (r['dispatch'] and r['dom_effect'] and corr and r['generation']>r['old_generation'] and r['process_start_ns']>r['old_process_start_ns']): errors.append(f'{c}: generation/start ordering')
 if seen!=CONTROLS: errors.extend(f'missing control={x}' for x in sorted(CONTROLS-seen))
 status='PASS_AUDIT_V2' if rows and not errors else 'HOLD_AUDIT_V2'; print(f'{status} rows={len(rows)} controls={len(seen)} errors={len(errors)}'); [print('ERROR '+e) for e in errors]; return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main(sys.argv[1]))
