#!/usr/bin/env python3
from __future__ import annotations
import json, tempfile
from pathlib import Path
from materialize import materialize, digest

R=Path(__file__).resolve().parent

def read(n): return json.loads((R/n).read_text())
def dump(n,v): (R/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')

def changed_same_size(text: str) -> str:
    if not text: raise ValueError('empty test content')
    first='X' if text[0] != 'X' else 'Y'
    return first + text[1:]

def clean_failure(parent: Path, out: Path) -> dict:
    leftovers=sorted(p.name for p in parent.glob('.'+out.name+'.stage-*'))
    return {'final_absent':not out.exists(),'stage_leftovers':leftovers,'clean':(not out.exists() and not leftovers)}

def attempt_case(ids, kind):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td); j=p/'jar-src'; s=p/'save-src'; out=p/'ready'
        j.write_text(ids['jar']['content_utf8']); s.write_text(ids['save']['content_utf8'])
        sentinel=None
        if kind=='wrong_jar': j.write_text(changed_same_size(ids['jar']['content_utf8']))
        elif kind=='wrong_save': s.write_text(changed_same_size(ids['save']['content_utf8']))
        elif kind=='symlink_jar':
            real=p/'jar-real'; real.write_text(ids['jar']['content_utf8']); j.unlink(); j.symlink_to(real)
        elif kind=='preexisting_output':
            out.mkdir(); sentinel=out/'sentinel'; sentinel.write_text('keep\n')
        else: raise ValueError(kind)
        error=None
        try: materialize(j,s,out,ids)
        except Exception as exc: error={'type':type(exc).__name__,'message':str(exc)}
        cleanup=clean_failure(p,out) if kind!='preexisting_output' else {
            'final_absent':False,
            'stage_leftovers':sorted(q.name for q in p.glob('.'+out.name+'.stage-*')),
            'clean': out.is_dir() and sentinel is not None and sentinel.read_text()=='keep\n'
        }
        return {'error':error,'cleanup':cleanup}

def main():
    marker=R/'.formal-invoked'
    if marker.exists() or (R/'RESULT.json').exists(): raise SystemExit('formal already invoked')
    marker.write_text('1\n')
    f=read('fixture.json'); ids=f['test']
    with tempfile.TemporaryDirectory() as td:
        p=Path(td); j=p/'jar-src'; s=p/'save-src'; out=p/'ready'
        j.write_text(ids['jar']['content_utf8']); s.write_text(ids['save']['content_utf8'])
        manifest=materialize(j,s,out,ids)
        good={
          'manifest':manifest,
          'manifest_file':json.loads((out/'MANIFEST.json').read_text()),
          'jar':{'bytes':digest(out/ids['jar']['name'])[0],'sha256':digest(out/ids['jar']['name'])[1]},
          'save':{'bytes':digest(out/ids['save']['name'])[0],'sha256':digest(out/ids['save']['name'])[1]},
          'published_files':sorted(x.name for x in out.iterdir()),
        }
    controls={k:attempt_case(ids,k) for k in ('wrong_jar','wrong_save','symlink_jar','preexisting_output')}
    gates={
      'good_status':good['manifest'].get('status')=='ASSETS_READY',
      'manifest_exact':good['manifest']==good['manifest_file'],
      'jar_exact':good['jar']=={'bytes':ids['jar']['bytes'],'sha256':ids['jar']['sha256']},
      'save_exact':good['save']=={'bytes':ids['save']['bytes'],'sha256':ids['save']['sha256']},
      'published_files':good['published_files']==['MANIFEST.json',ids['save']['name'],ids['jar']['name']],
      'wrong_jar_rejected_clean':controls['wrong_jar']['error'] is not None and controls['wrong_jar']['cleanup']['clean'],
      'wrong_save_rejected_clean':controls['wrong_save']['error'] is not None and controls['wrong_save']['cleanup']['clean'],
      'symlink_rejected_clean':controls['symlink_jar']['error'] is not None and controls['symlink_jar']['cleanup']['clean'],
      'preexisting_refused_unchanged':controls['preexisting_output']['error'] is not None and controls['preexisting_output']['cleanup']['clean'],
    }
    decision='PASS_MINDUSTRY_ASSET_MATERIALIZER_MECHANICS_SCOPED' if all(gates.values()) else 'FAIL_MINDUSTRY_ASSET_MATERIALIZER_MECHANICS'
    out={
      'schema':'mindustry_asset_materializer_result_v1',
      'task':f['task'],
      'formal_invocation':1,'formal_reruns':0,
      'decision':decision,'gates':gates,'good':good,'controls':controls,
      'production_identities':f['production'],
      'scope':'offline materialization mechanics only; no real Mindustry asset, GUI, model, or live result'
    }
    dump('RESULT.json',out)
    print(json.dumps({'decision':decision,'gates':gates},sort_keys=True))
    raise SystemExit(0 if all(gates.values()) else 1)
if __name__=='__main__': main()
