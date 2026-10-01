from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from cases import FORMAL, case_arrays
from model import estimate_global, estimate_band_consensus

TASK="LOCAL-NCC-CONSENSUS-20260923-001"

def hbytes(a): return hashlib.sha256(a.astype('float32').tobytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); ns=ap.parse_args()
    out=Path(ns.out)
    if out.exists(): raise SystemExit("refuse existing output")
    out.mkdir(parents=True)
    rows=[]
    for row in FORMAL:
        cid,seed,bg,fg,kind=row; ref,cur=case_arrays(row)
        rows.append({"id":cid,"seed":seed,"kind":kind,"authored_background_shift":bg,"authored_foreground_shift":fg,
                     "ref_sha256":hbytes(ref),"cur_sha256":hbytes(cur),
                     "global":estimate_global(ref,cur),"candidate":estimate_band_consensus(ref,cur)})
    par=[x for x in rows if x['kind']=='parallax']
    ident=[x for x in rows if x['kind'] in ('rigid','parallax')]
    global_wrong=sum(x['global']['status']=='IDENTIFIED' and abs(x['global']['shift_px']-x['authored_background_shift'])>2 for x in par)
    candidate_errors=[x['id'] for x in ident if x['candidate']['status']!='IDENTIFIED' or abs(x['candidate']['shift_px']-x['authored_background_shift'])>2]
    controls=[x for x in rows if x['kind'] in ('unrelated','low_texture')]
    false_controls=[x['id'] for x in controls if x['candidate']['status']=='IDENTIFIED']
    rigid_nonworse=all(abs(x['candidate']['shift_px']-x['authored_background_shift']) <= abs(x['global']['shift_px']-x['authored_background_shift']) for x in rows if x['kind']=='rigid' and x['candidate']['status']=='IDENTIFIED' and x['global']['status']=='IDENTIFIED')
    if candidate_errors or false_controls:
        decision="FAIL_LOCAL_CONSENSUS"
    elif global_wrong < 2:
        decision="HOLD_NO_PARALLAX_DISCRIMINATOR"
    elif not rigid_nonworse:
        decision="FAIL_LOCAL_CONSENSUS"
    else:
        decision="PASS_LOCAL_NCC_CONSENSUS_SCOPED"
    result={"task":TASK,"formal_invocations":1,"formal_reruns":0,"decision":decision,
            "gates":{"global_parallax_wrong_count":global_wrong,"candidate_errors":candidate_errors,"false_control_accepts":false_controls,"rigid_nonworse":rigid_nonworse},"rows":rows}
    data=(json.dumps(result,indent=2,sort_keys=True)+"\n").encode()
    (out/"RESULT.json").write_bytes(data)
    (out/"RESULT.sha256").write_text(hashlib.sha256(data).hexdigest()+"  RESULT.json\n")
    print(decision)
if __name__=="__main__": main()
