"""Finite reversible-preparation simulator. Never reads scorer truth."""
import argparse,json,pathlib
POLICIES=('IMMEDIATE','WAIT_THEN_PREPARE','STAGE_THEN_CORRECT')
def simulate(case,policy):
    events=[]; now=0; target=case['proposal']; signal=case['signal_ms']
    if policy=='WAIT_THEN_PREPARE':
        now=signal
        events.append({'at_ms':now,'event':'observe','value':case['signal']})
        if case['signal']!='UNKNOWN': target=case['signal']
    events.append({'at_ms':now,'event':'prepare_start','target':target})
    now+=case['prep_ms']
    events.append({'at_ms':now,'event':'prepare_done','target':target})
    if policy=='STAGE_THEN_CORRECT':
        events.append({'at_ms':signal,'event':'observe','value':case['signal']})
        now=max(now,signal)
        if case['signal'] not in ('UNKNOWN',target) and case['correction_route']:
            events.append({'at_ms':now,'event':'edit_start','target':case['signal']})
            now+=case['edit_ms'];target=case['signal']
            events.append({'at_ms':now,'event':'edit_done','target':target})
    now+=1
    admitted=now<=case['deadline_ms']
    events.append({'at_ms':now if admitted else case['deadline_ms'],'event':'commit' if admitted else 'deadline_refusal','target':target})
    events=sorted(events,key=lambda e:e['at_ms'])
    return {'id':case['id'],'policy':policy,'ready_ms':now,'target':target,'committed':admitted,'events':events}
def main():
    a=argparse.ArgumentParser();a.add_argument('fixtures');a.add_argument('output');args=a.parse_args()
    cases=json.loads(pathlib.Path(args.fixtures).read_text())
    with pathlib.Path(args.output).open('x') as out:
        for case in cases:
            for policy in POLICIES:out.write(json.dumps(simulate(case,policy),sort_keys=True,separators=(',',':'))+'\n')
    print(f'CANDIDATE_COMPLETE cases={len(cases)} rows={len(cases)*len(POLICIES)}')
if __name__=='__main__':main()
