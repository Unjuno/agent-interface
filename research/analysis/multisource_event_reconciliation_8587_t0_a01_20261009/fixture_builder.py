#!/usr/bin/env python3
"""Build the frozen, authored finite multi-source event fixture and hidden oracle."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
STAGES=("client","toolkit","os")
KINDS={"client":"dispatch","toolkit":"callback","os":"delivery"}

def ev(stage,seq,token,window="w-main",generation=1,interval=(0,1),kind=None):
    prefix={"client":"C","toolkit":"T","os":"O"}[stage]
    return {"source_id":f"{prefix}{seq}","sequence":seq,"correlation_token":token,
            "window":window,"generation":generation,"clock_domain":"fixture-mono",
            "interval_ms":list(interval),"kind":kind or KINDS[stage]}

def standard(case_id, fault=None, two=False):
    actions=[{"token":"a1","depends_on":[]}]
    if two: actions=[{"token":"a1","depends_on":[]},{"token":"a2","depends_on":[]}]
    logs={s:[] for s in STAGES}
    for i,action in enumerate(actions,1):
        token=action["token"]
        logs["client"].append(ev("client",i,token,interval=(0,2) if two else (0,1)))
        logs["toolkit"].append(ev("toolkit",i,token,interval=(1,3) if two else (1,2)))
        logs["os"].append(ev("os",i,token,interval=(2,4) if two else (2,3)))
    coverage={s:{"complete":True,"frontier_sequence":10,"source_instance":f"{s}-source-v1"} for s in STAGES}
    case={"case_id":case_id,"max_delivery_delay_ms":5,"declared_actions":actions,
          "coverage":coverage,"logs":logs,
          "final_state_by_source":{"client":{"screen":"done"},"toolkit":{"screen":"done"},"os":{"screen":"done"}}}
    if fault=="client_duplicate": logs["client"].append(ev("client",2,"a1",interval=(0,1)))
    elif fault=="toolkit_drop": logs["toolkit"]=[]
    elif fault=="toolkit_duplicate": logs["toolkit"].append(ev("toolkit",2,"a1",interval=(1,2)))
    elif fault=="os_duplicate": logs["os"].append(ev("os",2,"a1",interval=(2,3)))
    elif fault=="os_drop": logs["os"]=[]
    elif fault=="os_delay": logs["os"][0]["interval_ms"]=[20,21]
    elif fault=="wrong_window": logs["toolkit"][0]["window"]="w-other"
    elif fault=="generation_reset": logs["toolkit"][0]["generation"]=2
    elif fault=="missing_correlation": logs["toolkit"][0]["correlation_token"]=None
    elif fault=="truncated_os":
        coverage["os"]["complete"]=False
        coverage["os"]["frontier_sequence"]=0
    elif fault=="coalesced_redraw":
        logs["toolkit"].append(ev("toolkit",2,None,kind="redraw"))
        coverage["toolkit"]["coalesces_kinds"]=["redraw"]
    elif fault=="concurrent_reorder":
        # Invert the toolkit observation sequence. There is no explicit dependency between a1/a2.
        logs["client"]=[ev("client",1,"a1",interval=(0,4)),ev("client",2,"a2",interval=(0,4))]
        logs["toolkit"]=[ev("toolkit",1,"a2",interval=(1,4)),ev("toolkit",2,"a1",interval=(1,4))]
        logs["os"]=[ev("os",1,"a1",interval=(1,4)),ev("os",2,"a2",interval=(1,4))]
    elif fault=="independent_os_event":
        logs["os"].append(ev("os",2,"ambient-1",interval=(1,4),kind="independent"))
    elif fault=="irrelevant_redraw":
        logs["os"].append(ev("os",2,None,interval=(2,3),kind="redraw"))
    return case

CASES=[
    ("clean",None,"CONSISTENT",None),
    ("client_duplicate","client_duplicate","FAULT","CLIENT"),
    ("toolkit_drop","toolkit_drop","FAULT","CLIENT_TO_TOOLKIT"),
    ("toolkit_duplicate","toolkit_duplicate","FAULT","TOOLKIT"),
    ("os_duplicate","os_duplicate","FAULT","OS"),
    ("os_drop","os_drop","FAULT","TOOLKIT_TO_OS"),
    ("os_delay","os_delay","FAULT","OS"),
    ("wrong_window","wrong_window","FAULT","TOOLKIT"),
    ("generation_reset","generation_reset","FAULT","TOOLKIT"),
    ("missing_correlation","missing_correlation","UNKNOWN_CORRELATION",None),
    ("os_truncated","truncated_os","UNKNOWN_SOURCE_COVERAGE",None),
    ("benign_coalescing","coalesced_redraw","CONSISTENT",None),
    ("concurrent_reorder","concurrent_reorder","CONSISTENT",None),
    ("independent_os_event","independent_os_event","CONSISTENT",None),
    ("irrelevant_redraw","irrelevant_redraw","CONSISTENT",None),
]
model={"schema":"multisource-event-fixture-v1","stages":list(STAGES),"cases":[]}
oracle={"schema":"multisource-event-oracle-v1","cases":[]}
for cid,fault,expected,boundary in CASES:
    two=fault=="concurrent_reorder"
    model["cases"].append(standard(cid,fault,two=two))
    oracle["cases"].append({"case_id":cid,"injected_fault":fault,"expected_classification":expected,
                            "expected_boundary":boundary,"benign":expected=="CONSISTENT"})
(ROOT/"model.json").write_text(json.dumps(model,sort_keys=True,indent=2)+"\n")
(ROOT/"oracle.json").write_text(json.dumps(oracle,sort_keys=True,indent=2)+"\n")
