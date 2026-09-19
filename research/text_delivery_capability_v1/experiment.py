#!/usr/bin/env python3
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path
from model import CapabilityState, Request, Route, SideEffect, TextCoverage, choose_route, x11_evidence_profile

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    profile=x11_evidence_profile(); evidence_cases=[]
    cases=[
      ("ascii_transparent",Request(TextCoverage.ASCII,frozenset()),"direct_keys"),
      ("unicode_transparent",Request(TextCoverage.UNICODE,frozenset()),None),
      ("unicode_clipboard_declared",Request(TextCoverage.UNICODE,frozenset({SideEffect.CLIPBOARD_CONTENT,SideEffect.CLIPBOARD_OWNER,SideEffect.CLIPBOARD_TARGETS})),"clipboard_utf8"),
      ("unicode_global_mutation_only",Request(TextCoverage.UNICODE,frozenset({SideEffect.GLOBAL_KEYMAP})),None),
    ]
    for name,req,expected in cases:
        d=choose_route(profile,req); evidence_cases.append({"name":name,"selected":d.selected,"expected":expected,"passed":d.selected==expected,"rejected":d.rejected})
    states=list(CapabilityState); effects=list(SideEffect)
    budgets=[frozenset(e for e,b in zip(effects,bits) if b) for bits in itertools.product((False,True),repeat=len(effects))]
    checked=0; violations=[]
    for state_tuple in itertools.product(states, repeat=3):
        base=list(profile)
        base[2]=Route("keymap_remap",state_tuple[0],base[2].coverage,base[2].side_effects,False)
        base[3]=Route("accessibility_set_value",state_tuple[1],base[3].coverage,base[3].side_effects,state_tuple[1] is CapabilityState.SUPPORTED)
        base[4]=Route("native_ime",state_tuple[2],base[4].coverage,base[4].side_effects,state_tuple[2] is CapabilityState.SUPPORTED)
        for budget in budgets:
            d=choose_route(base,Request(TextCoverage.UNICODE,budget)); checked+=1
            if d.selected:
                r=next(r for r in base if r.name==d.selected)
                if not r.side_effects <= budget or r.state is not CapabilityState.SUPPORTED or not r.exact_semantics_observed:
                    violations.append({"states":[x.value for x in state_tuple],"budget":[x.value for x in budget],"selected":d.selected})
    result={"schema":"agent-interface/text-delivery-capability-model-v1","evidence_cases":evidence_cases,"exhaustive_cases_checked":checked,"safety_violations":violations,"passed":all(x["passed"] for x in evidence_cases) and not violations,"scope":"offline candidate capability negotiation only; no shared contract/runtime/native support claim"}
    (a.out/'report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); print(json.dumps(result,indent=2,ensure_ascii=False)); return 0 if result['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
