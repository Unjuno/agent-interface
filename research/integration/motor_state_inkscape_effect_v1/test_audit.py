#!/usr/bin/env python3
import copy,json,sys
from pathlib import Path
import audit

def load(paths): return audit.load(paths)
def main():
    rows=load(sys.argv[1:]); assert not audit.check_rows(rows,True)
    muts=[]
    def test(name,fn):
        z=copy.deepcopy(rows);fn(z);muts.append({'name':name,'rejected':bool(audit.check_rows(z,True))})
    test('drop_row',lambda z:z.pop())
    test('duplicate_row',lambda z:z.append(copy.deepcopy(z[0])))
    test('authority',lambda z:z[0].__setitem__('authority','input'))
    test('wrong_sha',lambda z:z[0].__setitem__('after_svg_sha256','0'*64))
    test('false_effect',lambda z:z[0].__setitem__('intended_effect',False))
    test('neutral_false',lambda z:z[0].__setitem__('neutral',False))
    test('displaced_guard_dispatch',lambda z:next(r for r in z if r['condition']=='DISPLACED_OBSERVED_GUARD').__setitem__('input_dispatched',True))
    test('unknown_guard_dispatch',lambda z:next(r for r in z if r['condition']=='OBSERVER_UNAVAILABLE_GUARD').__setitem__('input_dispatched',True))
    test('missing_held',lambda z:next(r for r in z if r['input_dispatched']).__setitem__('held_observed',None))
    test('bad_process_receipt',lambda z:z[0].__setitem__('process_exits',{}))
    out={'controls':muts,'pass':all(x['rejected'] for x in muts)};print(json.dumps(out,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
