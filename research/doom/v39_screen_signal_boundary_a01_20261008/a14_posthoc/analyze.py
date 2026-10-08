import hashlib,json
from pathlib import Path
source=Path(r"C:\Users\user\Documents\Codex\2026-10-08\work\issue59-main-576d\research\doom\v39_live_recovery_exploratory_a14_20261008\raw\runtime\events.jsonl")
raw=source.read_bytes(); freeze=json.loads((Path(__file__).resolve().parent/'FREEZE.json').read_text(encoding='utf-8'))
assert len(raw)==freeze['source_bytes'] and hashlib.sha256(raw).hexdigest()==freeze['source_sha256']
all_rows=[json.loads(line) for line in raw.decode('utf-8').splitlines() if line]
rows=[]
for row in all_rows:
    if row.get('event')=='typed_observation':
        rows.append({'id':row['id'],'sequence':row['sequence'],'capture_ns':row['capture_ns'],'frame_rgb_sha256':row['frame_rgb_sha256'],'health':row['signals']['health']['value'],'ammo':row['signals']['ammo']['value']})
pairs=list(zip(rows,rows[1:]))
result={'experiment':freeze['experiment'],'status':'POSTHOC_DESCRIPTIVE_ONLY','source_sha256':hashlib.sha256(raw).hexdigest(),'typed_observation_count':len(rows),'adjacent_pair_count':len(pairs),'frame_hash_changed_pairs':sum(a['frame_rgb_sha256']!=b['frame_rgb_sha256'] for a,b in pairs),'frame_changed_and_both_hud_stable_pairs':sum(a['frame_rgb_sha256']!=b['frame_rgb_sha256'] and a['health']==b['health'] and a['ammo']==b['ammo'] for a,b in pairs),'health_changed_pairs':sum(a['health']!=b['health'] for a,b in pairs),'ammo_changed_pairs':sum(a['ammo']!=b['ammo'] for a,b in pairs),'scope':'Does not correlate observations with pending model or active-cover intervals.'}
(Path(__file__).resolve().parent/'reduced_trace.json').write_text(json.dumps(rows,separators=(',',':'))+'\n',encoding='utf-8')
(Path(__file__).resolve().parent/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))