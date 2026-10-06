"""Independent raw-only oracle. No candidate/policy import; no native calls."""
import argparse,copy,hashlib,json
from pathlib import Path
def need(v,msg):
    if not v:raise ValueError(msg)
def verify(row):
    need(row['error']is None,'source error')
    context=row['context'];a,b=row['windows'];sub=row['subscription']
    need(type(sub['covered'])is bool and sub['covered']==(context!='unsubscribed_aba'),'typed coverage')
    need(sub['epoch']==row['epoch']and sub['windows']==[a,b]and sub['mask']==(1<<21 if sub['covered']else 0),'subscription join')
    need(row['viewable']==[[2,2],[2,2]],'viewable windows')
    def events_check(events,pattern):
        need(len(events)==len(pattern),'event count')
        for event,(kind,window)in zip(events,pattern):
            need(type(event['type'])is int and event['type']==kind and event['window']==window,'focus event semantics')
            need(event['send_event']is False and event['mode']==0,'genuine normal server events')
            need(type(event['sequence'])is int,'event serial')
    aba=[(10,a),(9,b),(10,b),(9,a)]
    events_check(row['qualification_events'],aba)
    hist=row['history'];need([h['label']for h in hist[:3]]==['setup_A','qualify_B','qualify_A'],'qualification history')
    for h in hist:
        need(h['request_ns']<=h['witness']['start_ns']<=h['witness']['end_ns'],'request/reply bracket')
    for x in ['A','F','B','source_before_F','post_B_barrier','qualification_barrier']:
        q=row[x];need(type(q['focus'])is int and q['start_ns']<=q['end_ns'],'typed native query')
    need(row['A']['focus']==a and row['qualification_barrier']['focus']==a,'source initial focus')
    need(row['qualification_barrier']['end_ns']<=row['A']['start_ns'],'exclude readiness before science')
    split=row['pre_frontier_history_start'];after=row['after_frontier_history_start']
    need(split==3,'science prefix index')
    pre=hist[split:after];post=hist[after:]
    pre_labels={'quiet':[],'aba':['before_F_B','before_F_A'],'persistent_change':['before_F_B'],
                'unsubscribed_aba':['before_F_B','before_F_A'],'change_after_frontier':[]}[context]
    need([h['label']for h in pre]==pre_labels,'complete pre frontier writes')
    need([h['label']for h in post]==(['after_F_B']if context=='change_after_frontier'else[]),'complete post frontier writes')
    expected_pre=[b,a]if context in('aba','unsubscribed_aba')else[b]if context=='persistent_change'else[]
    need([h['witness']['focus']for h in pre]==expected_pre,'direct transition witness')
    if pre:need(row['A']['end_ns']<=pre[0]['request_ns']and pre[-1]['witness']['end_ns']<=row['source_before_F']['start_ns'],'pre frontier order')
    need(row['A']['end_ns']<=row['source_before_F']['start_ns']<=row['source_before_F']['end_ns']<=row['F']['start_ns'],'explicit crossclient reply order')
    focus_F=b if context=='persistent_change'else a
    need(row['source_before_F']['focus']==focus_F and row['F']['focus']==focus_F,'query F joins source')
    expected_events=aba if context=='aba'else[(10,a),(9,b)]if context=='persistent_change'else[]
    events_check(row['events_through_F'],expected_events)
    if post:need(row['F']['end_ns']<=post[0]['request_ns']and post[0]['witness']['focus']==b and post[0]['witness']['end_ns']<=row['B']['start_ns'],'frontier to B gap')
    else:need(row['F']['end_ns']<=row['B']['start_ns'],'B order')
    focus_B=b if context in('persistent_change','change_after_frontier')else a
    need(row['B']['focus']==row['post_B_barrier']['focus']==focus_B,'current B query')
    need(row['B']['end_ns']<=row['post_B_barrier']['start_ns'],'B consumer ordering')
    events_check(row['events_after_F'],[(10,a),(9,b)]if context=='change_after_frontier'else[])
    expected_status='UNKNOWN_NO_COVERAGE'if not sub['covered']else'CHANGE_OBSERVED'if pre else'QUIET_AS_OF_FRONTIER'
    need(row['generation_result']=={'historical':expected_status,'authority':False}and row['generation_result']['authority']is False,'historical scoped/no authority')
    need(row['safe_to_act_at_B']is False and row['keyboard_pointer_emissions']==0,'no input authority/emissions')
    need(row['consumer_journal_at_A']==[]and row['naive_silence_quiet']is True,'explicit stale silence baseline')
    need(row['endpoint_equality_quiet']is(focus_F==a),'endpoint equality baseline')
    c=row['cleanup'];need(c['focus']['focus']==1 and c['keymap']=='00'*32 and c['observed_buttons123']==0,'owned display cleanup')
    need(c['windows_destroyed']is True and c['connections_closed']==3 and c['xvfb_exit']==0 and not c.get('errors')and not c.get('xvfb_killed_after_timeout'),'process cleanup')
    return {'pre_F_changed':bool(pre),'after_F_changed':bool(post),'status':expected_status}
def analyze(rows):
    need(len(rows)==15 and [(r['repeat'],r['context'])for r in rows]==[(i,c)for i in range(3)for c in ['quiet','aba','persistent_change','unsubscribed_aba','change_after_frontier']],'exact matrix')
    need([r['index']for r in rows]==list(range(15))and len({r['epoch']for r in rows})==15,'unique row epoch')
    outcomes=[verify(r)for r in rows]
    false_silence=sum(o['pre_F_changed']and r['naive_silence_quiet']for r,o in zip(rows,outcomes))
    false_endpoint=sum(o['pre_F_changed']and r['endpoint_equality_quiet']for r,o in zip(rows,outcomes))
    false_cert=sum(o['pre_F_changed']and o['status']=='QUIET_AS_OF_FRONTIER'for o in outcomes)
    return {'status':'SUPPORTED_NATIVE_FOCUS_FRONTIER_SCOPED','cells':15,'naive_stale_journal_false_quiet':false_silence,
            'endpoint_equality_false_quiet':false_endpoint,'qualified_false_quiet':false_cert,
            'qualified_change':sum(o['status']=='CHANGE_OBSERVED'for o in outcomes),
            'qualified_quiet':sum(o['status']=='QUIET_AS_OF_FRONTIER'for o in outcomes),
            'unknown_missing_subscription':sum(o['status']=='UNKNOWN_NO_COVERAGE'for o in outcomes),
            'quiet_F_changed_before_B':sum(o['after_F_changed']for o in outcomes),'authority_grants':0,
            'keyboard_pointer_emissions':0,'model_invocations':0,'new_mechanism_needed':False}
def controls(rows):
    tests={
        'swallowed_ABA':lambda x:x[1].__setitem__('events_through_F',[]),
        'forged_subscription':lambda x:x[3]['subscription'].__setitem__('covered',True),
        'quiet_to_authority':lambda x:x[4].__setitem__('safe_to_act_at_B',True),
        'missing_direct_transition':lambda x:x[1]['history'][3]['witness'].__setitem__('focus',x[1]['windows'][0]),
        'crossclient_order':lambda x:x[1]['F'].__setitem__('start_ns',0),
        'forged_event':lambda x:x[1]['events_through_F'][0].__setitem__('send_event',True),
        'bool_coverage':lambda x:x[0]['subscription'].__setitem__('covered',1),
        'wrong_epoch':lambda x:x[0]['subscription'].__setitem__('epoch','foreign'),
    };checks=[]
    for name,change in tests.items():
        changed=copy.deepcopy(rows);change(changed);need(changed!=rows,'effective control')
        try:analyze(changed);rejected=False
        except (ValueError,KeyError,TypeError):rejected=True
        checks.append({'name':name,'rejected':rejected})
    need(all(x['rejected']for x in checks),'copied controls refused')
    return checks
def main():
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('output');a=p.parse_args()
    raw=Path(a.raw).read_bytes();rows=[json.loads(x)for x in raw.splitlines()]
    try:r=analyze(rows);r['controls']=controls(rows);r['raw_sha256']=hashlib.sha256(raw).hexdigest();code=0
    except Exception as e:r={'status':'STOP_INVALID_NATIVE_EVIDENCE','error':repr(e),'raw_sha256':hashlib.sha256(raw).hexdigest()};code=1
    with Path(a.output).open('x')as f:json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps(r));raise SystemExit(code)
if __name__=='__main__':main()
