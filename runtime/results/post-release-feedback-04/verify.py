import base64,hashlib,json,tarfile,tempfile
from pathlib import Path,PurePosixPath
from analyze import analyze,need,load,meta,sha

def verify(dest):
 manifest=load(dest/'manifest.json');data=(dest/'raw.tar.gz').read_bytes();need(len(data)==manifest['archive']['bytes'] and sha(data)==manifest['archive']['sha256'],'archive hash')
 expected={x['path']:x for x in manifest['files']};need(len(expected)==len(manifest['files']),'duplicate manifest')
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);seen=set()
  with tarfile.open(dest/'raw.tar.gz','r:gz') as t:
   for member in t.getmembers():
    path=PurePosixPath(member.name);need(member.isfile() and not path.is_absolute() and '..' not in path.parts and member.name in expected and member.name not in seen,'unsafe/unknown/duplicate member');seen.add(member.name)
    content=t.extractfile(member).read();row=expected[member.name];need(len(content)==row['bytes'] and sha(content)==row['sha256'],'file hash '+member.name)
    file=root/member.name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(content)
  need(seen==set(expected),'missing member')
  p=root/'post-release-feedback-04';actual=analyze(p);need(actual==load(p/'analysis.json'),'analysis mismatch')
  stop=root/'post-release-feedback-03/candidate-post';finish=load(stop/'session/finish.json');need(finish['status']=='STOP_PRESENTATION_COMPOSITION' and finish['submittedTasks']==0 and finish['inputReplay']==0 and finish['transportExit']['code']==0,'03 retained STOP')
  need(load(stop/'session/evaluation-at-close.json')['success'] is False,'03 not success')
  projection=load(p/'same-report-full-projection.json');need(projection['source']==actual['source'],'projection source')
  for route,arm in projection['arms'].items():
   need(len(arm['calls'])==12,'projection 12 calls')
   for row in arm['calls']:
    i=row['attempt'];b=(p/route/'same-report-full'/f'full-{i}.json').read_bytes();v=json.loads(b);reply=load(p/route/'host'/f'reply-{i}.json');original=meta(reply);text=next(x['text'] for x in reply['result']['content'] if x['type']=='text').encode()
    need(len(b)==row['same_report_full_text_bytes'] and sha(b)==row['same_report_full_sha256'] and len(text)==row['actual_summary_text_bytes'],'projection bytes')
    raw=(p/route/'session/server'/v['call_id']/'report.json').read_bytes();need(sha(raw)==v['receipt']['source']['sha256']==original['receipt']['source']['sha256'] and v['receipt']['source']['raw_report']==json.loads(raw),'full report source')
    need(v['image_reference']==original['image_reference'] and v['outcome_summary']==original['outcome_summary'] and row['image_reference_identical'] is True and row['outcome_identical'] is True,'full image/outcome unchanged')
   need(arm['full_bytes']==sum(x['same_report_full_text_bytes'] for x in arm['calls']) and arm['summary_bytes']==sum(x['actual_summary_text_bytes'] for x in arm['calls']),'projection totals')
  usage=load(p/'model-usage-projection.json');need(usage['dollars'] is None and len(usage['calls'])>=30 and all(x['local_context']['model']=='gpt-6.1-sol' and x['local_context']['effort']=='medium' for x in usage['calls'] if x['local_context']),'usage labels')
  return {'status':'PASS_RETAINED_PUBLIC_SIX_TASK_PAIR','files':len(seen),'source':actual['source'],'candidate_extra_observations':0,'baseline_extra_observations':6,'integration_spine':actual['integration_spine'],'human_tempo':actual['human_tempo'],'scope':'Byte consistency; frozen public six-task effect, release/capture/wait/image identity and primary review attribution. No authentication, independent semantic clock, guarded/recovery spine or dollar benefit proof.'}
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,default=Path(__file__).resolve().parent);a=parser.parse_args();print(json.dumps(verify(a.directory)))
