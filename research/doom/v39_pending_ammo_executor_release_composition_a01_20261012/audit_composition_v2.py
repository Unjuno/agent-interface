from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
freeze=json.loads((ROOT/'FREEZE.json').read_text(encoding='utf-8'))
def need(ok,msg):
    if not ok: raise SystemExit('AUDIT_V2_FAIL: '+msg)
def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git_blob(p):
    b=p.read_bytes(); return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
for name,item in freeze['sources'].items():
    p=ROOT/item['local_path']; need(p.is_file(),f'missing frozen source {name}')
    need(len(p.read_bytes())==item['bytes'],f'source size mismatch {name}')
    need(sha256(p)==item['sha256'] and git_blob(p)==item['git_blob'],f'frozen source mismatch {name}')
for name in ('test_composition.py','fake_x.py','audit_composition.py'):
    need(sha256(ROOT/name)==freeze['artifacts'][name]['sha256'],f'frozen artifact mismatch {name}')
manifest={}
for line in (ROOT/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    digest,name=line.split('  ',1);manifest[name]=digest
need('FREEZE.json' in manifest,'freeze missing from SHA manifest')
for name,digest in manifest.items():need(sha256(ROOT/name)==digest,f'SHA256SUMS mismatch {name}')
stdout=(ROOT/'results/wslc.stdout.txt').read_text(encoding='utf-8')
stderr=(ROOT/'results/wslc.stderr.txt').read_text(encoding='utf-8')
need((ROOT/'results/exit.txt').read_text(encoding='ascii').strip()=='0','candidate exit nonzero')
need('Ran 1 test' in stderr and '\nOK\n' in stderr,'candidate unittest result missing across captured streams')
rows=[line.split('=',1)[1] for line in stdout.splitlines() if line.startswith('COMPOSITION_RESULT=')]
need(len(rows)==1,'expected one structured candidate result')
r=json.loads(rows[0]);need(json.loads((ROOT/'results/result.json').read_text(encoding='utf-8'))['result']==r,'structured result does not match raw stdout')
s=r['soft'];h=r['hard']
need(s['ammo']==4 and s['monitor_invalidation'] is None and s['soft_event_count']==1,'soft boundary mismatch')
need(s['ammo']<s['immediate_action_minimum_ammo'] and s['executor_active_during_pending_turn'] and s['fire_key_down_during_pending_turn'],'soft active-fire trace missing')
need(s['pending_answer_eligible'] and s['eventual_cleanup_verified'],'soft answer/cleanup mismatch')
need(h['ammo']==0 and h['monitor_reason']=='ammo:below_hard_minimum','hard monitor boundary mismatch')
need(h['executor_terminal_status']=='cancelled' and h['owner_release_verified'] and not h['pending_answer_eligible'],'hard cancel/release/answer mismatch')
need(h['executor_cancel_precedes_planner_interrupt'] and h['remaining_fake_x_keys']==[] and h['input_authority_admitted'] is False,'hard ordering/authority mismatch')
need('fake X' in r['scope'] and 'no OS input' in r['scope'],'claim boundary missing')
need((ROOT/'results/audit_v1.exit.txt').read_text(encoding='ascii').strip()=='1','audit-v1 HOLD not preserved')
print('AUDIT_V2_OK: frozen main blobs, candidate/auditor hashes, raw stdout+stderr, paired boundary outcomes, cancel/release ordering, and authority limits verified')
