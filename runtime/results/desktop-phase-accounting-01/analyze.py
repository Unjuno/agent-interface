"""Post-hoc accounting only; never launches GUI or changes frozen evidence."""
import json,re,subprocess,datetime,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
revision='3646d99f28f2ec391c2826445f2538d400d4d6d7'
base='runtime/results/desktop-phase-comparison-live-01/'
def read(path):return subprocess.check_output(['git','show',revision+':'+base+path],cwd=root,text=True)
records=[json.loads(s) for s in read('live-source-records.jsonl').splitlines()]
last=max(r['source_line'] for r in records);lines=['{}\n']*last
calls=[];outputs={}
for rec in records:
 lines[rec['source_line']-1]=rec['raw_line'];v=json.loads(rec['raw_line']);p=v.get('payload',{})
 if p.get('type')=='custom_tool_call':calls.append((rec['source_line'],v,p))
 if p.get('type')=='custom_tool_call_output':outputs[p['call_id']]=(rec['source_line'],v,p)
starts={};ends={}
for n,v,p in calls:
 s=p.get('input','')
 m=re.search(r'public-owner\.py .*?/(row-[^ \\"\n]+) (10021[0-9]{2}) (plain|compact|compiled) (acquisition|warm1|warm2|changed_dependency|subsequent_reuse)',s)
 if m:
  name=m.group(1)
  if name in starts:raise ValueError('Duplicate owner launch')
  starts[name]=(n,v,p)
 if 'row-summary.json' in s and 'commit' in s:
  m=re.search(r"(?:c|case)=p/'(row-[^']+)'",s)
  if m:
   if m.group(1) in ends:raise ValueError('Duplicate retained terminal audit')
   ends[m.group(1)]=(n,v,p)
if len(starts)!=15 or starts.keys()!=ends.keys():raise ValueError(('Missing owner boundaries',list(starts),list(ends)))
selection=[dict(name=name,begin_call_id=starts[name][2]['call_id'],end_call_id=ends[name][2]['call_id']) for name in sorted(starts)]
ns={'__name__':'projection_import'}
source=subprocess.check_output(['git','show',revision+':research/live_control/primary_usage_projection.py'],cwd=root,text=True)
exec(compile(source,'primary_usage_projection','exec'),ns)
projected=ns['project'](lines,selection)
def utc(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
rows=[];seen=set()
for w in projected['windows']:
 if w['status']!='recorded_usage':raise ValueError('Incomplete usage')
 v=json.loads(read(w['name']+'/row-summary.json'));owner=json.loads(read(w['name']+'/owner.json'))
 ids={u['response_id'] for u in w['usage_records']}
 if seen&ids:raise ValueError('Response usage overlaps owner windows')
 seen|=ids
 emissions=v.get('emissions',v.get('incremental_emissions'))
 r=dict(owner=w['name'],arm=v['arm'],phase=v.get('phase',v.get('phases')),phase_rows=v.get('rows',[v.get('row')]),seed=v['seed'],usage=w['totals'],response_ids=sorted(ids),commands=v['commands'],png_blocks=v['primary_selected_pngs'],emissions=emissions,call_issue_to_terminal_audit_output_ms=(utc(w['end']['timestamp'])-utc(w['begin']['timestamp'])).total_seconds()*1000,ready_owner_to_post_terminal_file_read_ms=(v['result_read_ns']-owner['started_ns'])/1e6,begin=w['begin'],end=w['end'],primary_semantic_completion_ms=None,model_first_useful_feedback_ms=None,billing=None)
 rows.append(r)
summary={}
for a in 'ABC':
 rr=[r for r in rows if r['arm']==a]
 summary[a]=dict(owners=len(rr),commands=sum(r['commands'] for r in rr),png_blocks=sum(r['png_blocks'] for r in rr),uncached_input_tokens=sum(r['usage']['uncached_input_tokens'] for r in rr),output_tokens=sum(r['usage']['output_tokens'] for r in rr),issue_to_terminal_audit_output_ms=sum(r['call_issue_to_terminal_audit_output_ms'] for r in rr))
for a in summary:summary[a]['uncached_plus_output_tokens']=summary[a]['uncached_input_tokens']+summary[a]['output_tokens']
joint=json.loads(read('live-primary-usage.json'))['windows'][0]['totals']
fields=['input_tokens','cached_input_tokens','uncached_input_tokens','output_tokens','reasoning_output_tokens','total_tokens']
remainder={k:joint[k]-sum(r['usage'][k] for r in rows) for k in fields}
if any(v<0 for v in remainder.values()):raise ValueError('Owner counts exceed joint counts')
report=dict(schema='posthoc-owner-accounting-v1',source_revision=revision,source_records_sha256=hashlib.sha256(read('live-source-records.jsonl').encode()).hexdigest(),rows=rows,arms=summary,joint_usage=joint,outside_owner_windows_inside_joint=remainder,disposition='HOLD',scope='Post-hoc disjoint execution windows, whole-context response usage. Not fair acquisition, causal route charges, primary ingestion/semantic completion, billing, held-out or human-speed evidence. Counts exclude planning before each launch and gaps; the joint remainder is retained separately, never free or assigned per arm.')
for name,value in [('selection.json',selection),('projection.json',projected),('report.json',report)]:
 (out/name).write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(dict(owners=len(rows),arms=summary,joint_remainder=remainder,disposition=report['disposition'])))
