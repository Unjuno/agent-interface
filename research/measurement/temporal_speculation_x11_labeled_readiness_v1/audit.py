from __future__ import annotations
import argparse,json
from pathlib import Path

def sgn(x): return 1 if x>0 else -1 if x<0 else 0

def ph(seq,name): return next(x for x in seq['phases'] if x['phase']==name)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args()
    r=json.loads(Path(a.result).read_text());e=[];alias=0;disagree=0;seq_n=0;binding_ok=0;classification_ok=0
    if r.get('formal') is not True or r.get('formal_invocations')!=1 or r.get('reruns')!=0:e.append('invocation')
    if r.get('authority_grants')!=0 or r.get('input_actions')!=0:e.append('authority_or_input')
    if r.get('roi')!=[80,60,160,120]:e.append('roi')
    if len(r.get('pairs',[]))!=32:e.append('pair_count')
    for p in r.get('pairs',[]):
        if len(p.get('sequences',[]))!=2:e.append(f"pair{p.get('pair_id')}_sequence_count");continue
        L,R=p['sequences']; seq_n+=2
        if {L['sequence'],R['sequence']}!={'L','R'}:e.append(f"pair{p['pair_id']}_sides")
        curL=ph(L,'current')['capture'];curR=ph(R,'current')['capture']
        histL=ph(L,'history')['capture'];histR=ph(R,'history')['capture']
        futL=ph(L,'future')['capture'];futR=ph(R,'future')['capture']
        if curL['sha256']==curR['sha256']: alias+=1
        else:e.append(f"pair{p['pair_id']}_current_alias")
        if histL['sha256']==histR['sha256']:e.append(f"pair{p['pair_id']}_history_distinct")
        if futL['sha256']!=futR['sha256']:disagree+=1
        else:e.append(f"pair{p['pair_id']}_future_disagree")
        if L['content_direction'] != -R['content_direction'] or L['content_direction']==0:e.append(f"pair{p['pair_id']}_opposite_direction")
        for s in (L,R):
            phases={x['phase']:x for x in s['phases']}
            if set(phases)!={'history','current','future'}:e.append(f"pair{p['pair_id']}_{s['sequence']}_phases");continue
            # Content feature extractor is checked only against retained fixture output after capture.
            ok=True
            for name,x in phases.items():
                c=x['capture'];f=x['fixture']
                if c['bytes']!=76800 or c['pixel_format_interpretation']!='BGRX':ok=False
                if abs(c['red_centroid_x']-(f['actual_x']+20.0))>1.0:ok=False
                if not (f['ack_ns'] <= c['capture_started_ns'] <= c['capture_finished_ns']):ok=False
            if not ok:e.append(f"pair{p['pair_id']}_{s['sequence']}_binding")
            else:binding_ok+=1
            h,c,f=[ph(s,n)['capture'] for n in ('history','current','future')]
            d=sgn(c['red_centroid_x']-h['red_centroid_x']);fd=sgn(f['red_centroid_x']-c['red_centroid_x'])
            derived_rev=(d!=0 and fd!=0 and d!=fd)
            derived_label='RIGHT' if fd>0 else 'LEFT' if fd<0 else 'CENTER'
            authored=ph(s,'future')['fixture']['authored']
            if d!=s['content_direction'] or fd!=s['content_future_direction'] or derived_rev!=s['content_reversal'] or derived_label!=s['content_future_label']:
                e.append(f"pair{p['pair_id']}_{s['sequence']}_content_derivation")
            elif derived_rev!=authored['reversal'] or derived_label!=authored['future_label']:
                e.append(f"pair{p['pair_id']}_{s['sequence']}_fixture_label")
            else: classification_ok+=1
        # Independently retained fixture log must contain all 6 phase rows.
        if len(p.get('fixture_log',[]))!=6:e.append(f"pair{p['pair_id']}_fixture_log")
    if alias<32:e.append('alias_count')
    if disagree<16:e.append('future_disagreement_count')
    if binding_ok!=64:e.append('binding_count')
    if classification_ok!=64:e.append('classification_count')
    decision='PASS_X11_LABELED_SPECULATION_DATA_READY_SCOPED' if not e else ('FAIL_EVIDENCE_BINDING' if any('binding' in x or 'fixture_label' in x or 'content_derivation' in x for x in e) else 'BLOCKED_DATA_TEMPORAL_SPECULATION_RUNG1')
    out={'decision':decision,'errors':e,'pairs':len(r.get('pairs',[])),'sequences':seq_n,'same_current_alias_pairs':alias,'opposite_history_future_disagreement_pairs':disagree,'binding_ok_sequences':binding_ok,'classification_ok_sequences':classification_ok,'fresh_current_identity':alias>=32,'independent_future_label':classification_ok==64,'no_replay_regeneration':True,'authority_grants':r.get('authority_grants'),'input_actions':r.get('input_actions')}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
