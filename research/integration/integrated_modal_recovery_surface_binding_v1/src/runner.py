import hashlib, json, sys
from pathlib import Path
from validator import app_class_only, surface_bound, RecoveryRejected

EXPECTED_ARCHIVE_SHA='5c7725f878028e620a4edf975fe890b0b2d8fda0071cd286a3c70163ca4d96d6'

def receipt(ctx, kind):
    return {
      'receipt_kind': kind,
      'app':ctx['app'], 'client_id':ctx['client_id'], 'focus_id':ctx['focus_id'],
      'surface_kind':ctx['surface_kind'], 'transient_for':ctx['transient_for'],
      'geometry':ctx['geometry'],
      'authority':'none','task_input_granted':False,'action_admission_eligible':False,
    }

def main(root, out):
    root=Path(root); out=Path(out)
    fixture=json.loads((root/'fixture.json').read_text())
    archive=root/'predecessor/evidence.tar.xz'
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=EXPECTED_ARCHIVE_SHA:
        raise SystemExit('archive_sha')
    validators={'app_class_only':app_class_only,'surface_bound':surface_bound}
    rows=[]
    for case in fixture['cases']:
        current=case['current']
        for kind,ctx in [('stale_main',case['source']),('fresh_modal',current)]:
            r=receipt(ctx,kind)
            for name,fn in validators.items():
                status='accepted'; reason=None
                try: fn(r,current)
                except RecoveryRejected as e: status='rejected'; reason=str(e)
                rows.append({
                  'case_id':case['case_id'],'case_sha256':case['case_sha256'],
                  'receipt_kind':kind,'validator':name,'status':status,'reason':reason,
                  'receipt':r,'current':current,
                })
    out.write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'rows':len(rows)}))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
