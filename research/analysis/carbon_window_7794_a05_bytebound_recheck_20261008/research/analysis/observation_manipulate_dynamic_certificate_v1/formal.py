from __future__ import annotations
from itertools import product
import argparse, hashlib, json
from pathlib import Path
from model import DOMS, PHASE_SUPPORT, decision, select_certificate, changed
TASK='OBSERVATION-GATING-O3-MANIPULATE-DYNAMIC-CERTIFICATE-20260919-001'
PHASES=('PREPARE','EFFECT_PENDING','TERMINAL')

def run(source_sha256):
    metrics={k:0 for k in ['current_states','transition_rows','certificate_validity_errors','minimality_errors','dynamic_false_suppressions','phase_union_false_suppressions','global_false_suppressions','dynamic_safe_suppressions','phase_union_safe_suppressions','dynamic_false_forwards','phase_union_false_forwards','global_false_forwards','strict_narrowing_states']}
    sizes={p:{} for p in PHASES}; selected={}; ledger=hashlib.sha256()
    for phase in PHASES:
      for state in product((0,1), repeat=4):
        cert,valid=select_certificate(phase,state)
        key=f'{phase}:{"".join(map(str,state))}'
        selected[key]=''.join(d for d in DOMS if d in cert) or '-'
        sizes[phase][str(len(cert))]=sizes[phase].get(str(len(cert)),0)+1
        metrics['current_states']+=1
        if cert not in valid: metrics['certificate_validity_errors']+=1
        if any(len(v)<len(cert) for v in valid): metrics['minimality_errors']+=1
        if cert < PHASE_SUPPORT[phase]: metrics['strict_narrowing_states']+=1
        for nxt in product((0,1), repeat=4):
          delta=changed(state,nxt); must=decision(phase,state)!=decision(phase,nxt)
          dyn=not bool(delta & cert)
          uni=not bool(delta & PHASE_SUPPORT[phase])
          glob=not bool(delta)
          metrics['transition_rows']+=1
          metrics['dynamic_false_suppressions']+=int(dyn and must)
          metrics['phase_union_false_suppressions']+=int(uni and must)
          metrics['global_false_suppressions']+=int(glob and must)
          metrics['dynamic_safe_suppressions']+=int(dyn and not must)
          metrics['phase_union_safe_suppressions']+=int(uni and not must)
          metrics['dynamic_false_forwards']+=int((not dyn) and (not must))
          metrics['phase_union_false_forwards']+=int((not uni) and (not must))
          metrics['global_false_forwards']+=int((not glob) and (not must))
          ledger.update(json.dumps([phase,state,nxt,sorted(cert),decision(phase,state),decision(phase,nxt),dyn,uni,glob],separators=(',',':')).encode())
    return {'task':TASK,'phase':'formal','formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,'source_sha256':source_sha256,'metrics':metrics,'certificate_size_distribution':sizes,'selected_certificates':selected,'ledger_sha256':ledger.hexdigest()}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-manifest',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    sm=json.loads(Path(a.source_manifest).read_text()); r=run(sm['sha256']); Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r['metrics'],sort_keys=True))
if __name__=='__main__':main()
