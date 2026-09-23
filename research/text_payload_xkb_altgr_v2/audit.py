from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from Xlib import XK
HERE=Path(__file__).resolve().parent
MODE_SWITCH=XK.string_to_keysym('Mode_switch')
def sha(b): return hashlib.sha256(b).hexdigest()
def map_hash(m): return hashlib.sha256(json.dumps(m,separators=(',',':')).encode()).hexdigest()
def parse_direct(xkb_text):
    codes={m.group(1):int(m.group(2)) for m in re.finditer(r'<([^>]+)>\s*=\s*(\d+)\s*;',xkb_text)}; direct={}; by_code={}
    for m in re.finditer(r'key\s+<([^>]+)>\s*\{(.*?)\};',xkb_text,re.S):
        name,body=m.group(1),m.group(2); sm=re.search(r'symbols\[Group1\]\s*=\s*\[(.*?)\]',body,re.S)
        if sm is None: sm=re.search(r'\[(.*?)\]',body,re.S)
        code=codes.get(name)
        if not sm or code is None: continue
        vals=[]
        for token in [x.strip() for x in sm.group(1).split(',')][:4]:
            if token in ('','NoSymbol','VoidSymbol'): vals.append(0); continue
            ks=XK.string_to_keysym(token)
            if ks==0 and len(token)==1: ks=ord(token)
            vals.append(int(ks))
        while len(vals)<4: vals.append(0)
        by_code[code]=vals
        for level,ks in enumerate(vals):
            if 32<=ks<=126: direct.setdefault(chr(ks),[]).append((code,level,name))
    return codes,direct,by_code
def require(cond,msg):
    if not cond: raise AssertionError(msg)
def main(out):
    prereg=json.loads((HERE/'prereg.json').read_text()); sched_bytes=(HERE/'schedule.json').read_bytes(); schedule=json.loads(sched_bytes)
    require(sha(sched_bytes)==prereg['schedule_sha256'],'schedule hash drift')
    for name,digest in prereg['source_sha256'].items(): require(sha((HERE/name).read_bytes())==digest,f'source drift {name}')
    summaries=[]; all_trials=[]; recovered=set(); two_rejects=set()
    for rep in range(schedule['repetitions']):
        d=out/f'rep-{rep}'; report=json.loads((d/'report.json').read_text()); resolved=(d/'layout.resolved.xkb').read_bytes(); require(sha(resolved)==prereg['resolved_xkb_sha256'],f'resolved XKB drift rep{rep}')
        codes,direct,by_code=parse_direct(resolved.decode()); mapping=json.loads((d/'applied_mapping.json').read_text()); mods=json.loads((d/'modifier_mapping.json').read_text()); first=prereg['min_keycode']
        require(map_hash(mapping)==report['applied_map_hash'],'applied map hash mismatch'); require(map_hash(mods)==report['applied_modifier_hash'],'modifier hash mismatch')
        ralt=report['ralt_keycode']; require(ralt==codes['RALT'],'RALT keycode mismatch'); require(mapping[ralt-first][0]==MODE_SWITCH,'RALT not Mode_switch'); require(ralt in mods[7],'Mode_switch not Mod5')
        hist=set(schedule['historical_two_level_rejected_single_chars']); got_two={c for c in hist if not any(level<2 for _,level,_ in direct.get(c,[]))}; require(got_two==hist,'historical two-level classification not reproduced by resolved XKB')
        got_recovered={c for c in hist if any(level in (2,3) for _,level,_ in direct.get(c,[]))}; require(got_recovered==set(schedule['expected_candidate_direct_recovered_single_chars']),'recovery set drift')
        for c in schedule['expected_candidate_dead_key_refusals_single_chars']: require(c not in direct,f'dead-key control became direct: {c!r}')
        two_rejects|=got_two; recovered|=got_recovered
        require(report['final_map_hash']==report['applied_map_hash'],'final map drift'); require(report['final_modifier_hash']==report['applied_modifier_hash'],'final modifier drift'); require(not report['final_physical']['keys'] and report['final_physical']['mask']==0,'final physical nonempty')
        require(len(report['trials'])==len(schedule['payloads']),'trial count')
        for tr in report['trials']:
            text=tr['payload']; exp=all(ch in direct for ch in text); rec=tr['candidate']; require(tr['expected_accept']==exp,'runner expected classification drift'); require(rec['accepted']==exp,'candidate acceptance mismatch'); require(tr['map_before']==tr['map_after']==report['applied_map_hash'],'trial map drift'); require(tr['modifier_before']==tr['modifier_after']==report['applied_modifier_hash'],'trial modifier drift'); require(rec.get('release_verified') is True,'release unverified'); require(not tr['physical_after_trial']['keys'] and tr['physical_after_trial']['mask']==0,'trial physical nonempty')
            if exp:
                require(tr['actual']==text,'wrong receiver text'); strokes=rec['strokes']; require(len(strokes)==len(text),'stroke count'); emissions=0
                for ch,st in zip(text,strokes):
                    code=int(st['code']); level=int(st['level']); require(0<=level<=3,'bad level'); require(mapping[code-first][level]==ord(ch),f'stroke symbol mismatch {ch!r}'); require(bool(st['shift'])==(level in (1,3)),'shift flag mismatch'); require(bool(st['mode_switch'])==(level in (2,3)),'mode flag mismatch'); emissions+=2+2*int(st['shift'])+2*int(st['mode_switch'])
                require(rec['emissions']==emissions,'emission count mismatch')
            else:
                require(tr['actual']=='' and rec['emissions']==0,'rejection side effect'); require(rec.get('preflight_rejected') is True and rec.get('interrupted') is False,'not preflight refusal')
            require(tr['gate'] is True,'runner gate false'); all_trials.append((rep,text,exp))
        summaries.append({'rep':rep,'resolved_sha256':sha(resolved),'passed':report['passed']})
    require(len(all_trials)==prereg['formal_trials'],'formal trial total'); require(all(x['passed'] for x in summaries),'arm pass false')
    result={'status':'PASS_INDEPENDENT_AUDIT','decision':'RETAIN_ALTGR_DIRECT_PREFLIGHT_SCOPED','formal_trials':len(all_trials),'repetitions':schedule['repetitions'],'historical_two_level_rejects':sorted(two_rejects),'recovered_level2_or_3':sorted(recovered),'dead_key_refusals':schedule['expected_candidate_dead_key_refusals_single_chars'],'arms':summaries}
    (out/'audit_summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+'\n'); print(json.dumps(result,sort_keys=True)); return 0
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('out',type=Path); raise SystemExit(main(ap.parse_args().out.resolve()))
