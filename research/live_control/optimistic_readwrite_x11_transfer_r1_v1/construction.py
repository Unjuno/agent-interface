from __future__ import annotations
import json
from run_case import run_case,SCENARIOS

def main():
    rows=[run_case('c'+str(i),s) for i,s in enumerate(SCENARIOS)]
    by={r['scenario']:r for r in rows}
    checks={
      'all_complete':all(r['pass_case'] and r['cleanup_workers_exited'] and r['cleanup_xvfb_exited'] for r in rows),
      'independent':by['INDEPENDENT']['decision']=='PARALLEL' and by['INDEPENDENT']['final_effects']=={'A':'LOCAL1','B':'LOCAL1'},
      'candidate_shared':by['SHARED_GLOBAL_CANDIDATE']['decision']=='SERIALIZE' and by['SHARED_GLOBAL_CANDIDATE']['b_receipt_stale_after_a'] and by['SHARED_GLOBAL_CANDIDATE']['b_reprepare_count']==1 and by['SHARED_GLOBAL_CANDIDATE']['final_receipts']['GLOBAL']==1 and by['SHARED_GLOBAL_CANDIDATE']['final_effects']['B']=='G1',
      'surface_only_discriminator':by['SHARED_GLOBAL_SURFACE_ONLY']['decision']=='PARALLEL_SURFACE_ONLY' and by['SHARED_GLOBAL_SURFACE_ONLY']['a_before_b_effect'] and by['SHARED_GLOBAL_SURFACE_ONLY']['final_receipts']['GLOBAL']==1 and by['SHARED_GLOBAL_SURFACE_ONLY']['final_effects']['B']=='G0',
      'external_stale':by['EXTERNAL_STALE']['decision']=='REVALIDATE' and by['EXTERNAL_STALE']['b_effect_command_count']==0 and by['EXTERNAL_STALE']['final_effects']['B']=='NONE',
    }
    out={'checks':checks,'rows':rows}
    print(json.dumps(out,sort_keys=True))
    assert all(checks.values())
if __name__=='__main__':main()
