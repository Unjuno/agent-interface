"""Independent recomputation of pending-observation metadata summary."""
import hashlib
import json
from pathlib import Path, PurePosixPath

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
ROOT=REPO/'research/doom/results/map01-astra-attempt-v1'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    freeze=json.loads((HERE/'STREAM_FREEZE.json').read_text())
    for section in ('inputs','code'):
        for relative, expected in freeze[section].items():
            if sha(REPO/relative)!=expected['sha256']:
                raise SystemExit(f'FAIL_HASH {relative}')
    report=json.loads((ROOT/'report.json').read_text())
    events=[json.loads(line) for line in (ROOT/'events.jsonl').read_text().splitlines()]
    manifest=json.loads((ROOT/'local-exact-frame-manifest.json').read_text())
    rows=sorted((x for x in events if x.get('event')=='observation'),key=lambda x:x['capture_ns'])
    byfile={PurePosixPath(x['file']).name:x for x in manifest['frames']}
    mismatches=[]
    seen=set()
    refs=set()
    for x in rows:
        name=PurePosixPath(x.get('image','')).name
        refs.add(name)
        if x.get('exact') is not True: mismatches.append({'kind':'not-exact','sequence':x.get('sequence')})
        if name not in byfile: mismatches.append({'kind':'unmapped','file':name})
        if x.get('sequence') in seen: mismatches.append({'kind':'duplicate-sequence','sequence':x.get('sequence')})
        seen.add(x.get('sequence'))
    waits=[]
    for i,d in enumerate(report['decisions']):
        start,end=d['controller_model_started_ns'],d['controller_model_ended_ns']
        inside=[x for x in rows if start<=x['capture_ns']<=end]
        before=[x for x in rows if x['capture_ns']<=start]
        prior=byfile[PurePosixPath(before[-1]['image']).name]['sha256'] if before else None
        first=next((x for x in inside if byfile[PurePosixPath(x['image']).name]['sha256']!=prior),None)
        gaps=[(b['capture_ns']-a['capture_ns'])/1e6 for a,b in zip(inside,inside[1:])]
        latest=inside[-1]['sequence'] if inside else None
        returned=d.get('fresh_sequence_at_plan')
        matches=returned is None or returned==latest
        if not inside: mismatches.append({'kind':'no-samples-in-wait','decision':i})
        if returned is not None and not matches: mismatches.append({'kind':'return-sequence-mismatch','decision':i})
        waits.append({
            'decision':i,
            'observation_count':len(inside),
            'first_sequence':inside[0]['sequence'] if inside else None,
            'latest_sequence':latest,
            'reported_fresh_sequence_at_plan':returned,
            'return_sequence_matches_latest_observation':matches,
            'first_observation_latency_ms':(inside[0]['capture_ns']-start)/1e6 if inside else None,
            'first_different_full_frame_hash_ms':(first['capture_ns']-start)/1e6 if first else None,
            'unique_full_frame_hashes':len({byfile[PurePosixPath(x['image']).name]['sha256'] for x in inside}),
            'max_capture_gap_ms':max(gaps) if gaps else None,
        })
    recorded=json.loads((HERE/'STREAM_RESULT.json').read_text())
    if recorded['waits']!=waits:
        for index,(actual,expected) in enumerate(zip(recorded['waits'],waits)):
            fields=[key for key in expected if key not in actual or actual[key]!=expected[key]]
            if fields: mismatches.append({'kind':'wait-result-mismatch','decision':index,'fields':fields})
    if recorded['observation_count']!=len(rows): mismatches.append({'kind':'observation-count-mismatch'})
    if recorded['unique_image_path_count']!=len(refs): mismatches.append({'kind':'path-count-mismatch'})
    if recorded['manifest_frame_count']!=len(byfile): mismatches.append({'kind':'manifest-count-mismatch'})
    if recorded['intermediate_image_bytes_present'] is not False: mismatches.append({'kind':'unexpected-frame-bytes'})
    audit={
        'schema':'map01-astra-pending-observation-stream-a01-audit',
        'disposition':'PASS_AUDITED_METADATA_ONLY' if not mismatches else 'FAIL_METADATA_AUDIT',
        'observation_rows_recomputed':len(rows),
        'manifest_frames_recomputed':len(byfile),
        'model_waits_recomputed':len(waits),
        'return_sequences_checked':sum(x['reported_fresh_sequence_at_plan'] is not None for x in waits),
        'return_sequences_matching':sum(x['reported_fresh_sequence_at_plan'] is not None and x['return_sequence_matches_latest_observation'] for x in waits),
        'mismatch_count':len(mismatches),
        'mismatches':mismatches,
        'limits':'independent metadata recomputation only; no intermediate image pixels or semantics are audited',
    }
    (HERE/'STREAM_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:audit[k] for k in ('disposition','observation_rows_recomputed','manifest_frames_recomputed','model_waits_recomputed','mismatch_count')}))
    if mismatches: raise SystemExit(1)

if __name__=='__main__': main()
