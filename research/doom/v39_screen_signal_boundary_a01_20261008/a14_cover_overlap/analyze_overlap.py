import hashlib,json,sys
from pathlib import Path
if len(sys.argv)!=3: raise SystemExit('usage: python -B analyze_overlap.py <runtime/events.jsonl> <planner-protocol.jsonl>')
root=Path(__file__).resolve().parent
freeze=json.loads((root/'FREEZE.json').read_text(encoding='utf-8'))
def read(path,key):
 raw=Path(path).read_bytes(); pinned=freeze[key]
 if len(raw)!=pinned['bytes'] or hashlib.sha256(raw).hexdigest()!=pinned['sha256']: raise SystemExit(f'{key} SHA/size mismatch')
 return [json.loads(line) for line in raw.decode('utf-8').splitlines() if line]
runtime=read(sys.argv[1],'runtime_events'); protocol=read(sys.argv[2],'planner_protocol')
starts=[x for x in protocol if x.get('direction')=='sent' and x.get('message',{}).get('method')=='turn/start']
started=[x for x in protocol if x.get('direction')=='received' and x.get('message',{}).get('method')=='turn/started']
completed=[x for x in protocol if x.get('direction')=='received' and x.get('message',{}).get('method')=='turn/completed']
if not (len(starts)==len(started)==len(completed)==6): raise SystemExit('unexpected planner turn counts')
turns=[]
for i,(s,b,c) in enumerate(zip(starts,started,completed)):
 tid=b['message']['params']['turn']['id']
 if c['message']['params']['turn']['id']!=tid or not s['observed_ns']<b['observed_ns']<c['observed_ns']: raise SystemExit('planner turn identity/order mismatch')
 turns.append({'index':i,'turn_id':tid,'start_ns':s['observed_ns'],'started_ns':b['observed_ns'],'completed_ns':c['observed_ns'],'terminal_status':c['message']['params']['turn']['status']})
accepted={x['id']:x['emit_ns'] for x in runtime if x.get('event')=='accepted' and str(x.get('id','')).startswith('cover-')}
terminal={x['id']:x['emit_ns'] for x in runtime if x.get('event')=='terminal' and str(x.get('id','')).startswith('cover-')}
if set(accepted)!=set(terminal): raise SystemExit('cover accepted/terminal inventory mismatch')
covers=[{'id':cid,'start_ns':accepted[cid],'end_ns':terminal[cid]} for cid in sorted(accepted,key=accepted.get)]
obs=[{'id':x['id'],'sequence':x['sequence'],'emit_ns':x['emit_ns'],'frame_rgb_sha256':x['frame_rgb_sha256'],'health':x['signals']['health']['value'],'ammo':x['signals']['ammo']['value']} for x in runtime if x.get('event')=='typed_observation']
spans=[]
for turn in turns:
 for cover in covers:
  lo=max(turn['start_ns'],cover['start_ns']); hi=min(turn['completed_ns'],cover['end_ns'])
  if lo>=hi: continue
  indexed=[(i,o) for i,o in enumerate(obs) if lo<=o['emit_ns']<=hi]
  if not indexed: continue
  if any(j[0]!=i[0]+1 for i,j in zip(indexed,indexed[1:])): raise SystemExit('noncontiguous observations inside overlap')
  sample=[o for _,o in indexed]; pairs=list(zip(sample,sample[1:]))
  spans.append({'turn_index':turn['index'],'cover_id':cover['id'],'overlap_start_ns':lo,'overlap_end_ns':hi,'overlap_ms':(hi-lo)/1e6,'observation_ids':[o['id'] for o in sample],'observation_count':len(sample),'adjacent_pair_count':len(pairs),'frame_hash_changed_pairs':sum(a['frame_rgb_sha256']!=b['frame_rgb_sha256'] for a,b in pairs),'frame_changed_hud_stable_pairs':sum(a['frame_rgb_sha256']!=b['frame_rgb_sha256'] and a['health']==b['health'] and a['ammo']==b['ammo'] for a,b in pairs),'health_changed_pairs':sum(a['health']!=b['health'] for a,b in pairs),'ammo_changed_pairs':sum(a['ammo']!=b['ammo'] for a,b in pairs)})
reduced={'turns':turns,'covers':covers,'observations':obs,'spans':spans}
summary={'experiment':freeze['experiment'],'status':'POSTHOC_DESCRIPTIVE_ONLY','source_hashes':{'runtime_events':freeze['runtime_events']['sha256'],'planner_protocol':freeze['planner_protocol']['sha256']},'overlap_span_count':len(spans),'observations_in_overlaps':sum(s['observation_count'] for s in spans),'adjacent_pairs_in_overlaps':sum(s['adjacent_pair_count'] for s in spans),'frame_hash_changed_pairs':sum(s['frame_hash_changed_pairs'] for s in spans),'frame_changed_hud_stable_pairs':sum(s['frame_changed_hud_stable_pairs'] for s in spans),'spans':spans,'scope':'Uses emitted observation timestamps and covers overlapping planner turns; does not assign semantic meaning to screen changes.'}
(root/'reduced_trace.json').write_text(json.dumps(reduced,separators=(',',':'))+'\n',encoding='utf-8'); (root/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8'); print(json.dumps(summary,indent=2))