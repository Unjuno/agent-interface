#!/usr/bin/env python3
"""Fresh-seed fixture wrapper with the A09 auditor's required truth-list root."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).parent.resolve()
BASE_PACKAGE=ROOT.parent/"looming_yield_5905_boundary_jitter_a02_20261005"
spec=importlib.util.spec_from_file_location("boundary_jitter_base_generator",BASE_PACKAGE/"generate.py")
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
base.ROOT=ROOT;base.SEED=20261013
SEED=base.SEED;TIMES=base.TIMES;CONTACT=base.CONTACT

def generate():
    d=base.generate()
    return {"manifest":d["manifest"],"truth":d["truth"]["cases"]}

def write():
    d=generate();obs=ROOT/"bundle/observations";truth=ROOT/"bundle/truth"
    obs.mkdir(parents=True,exist_ok=True);truth.mkdir(parents=True,exist_ok=True)
    (obs/"manifest.json").write_text(json.dumps(d["manifest"],sort_keys=True,indent=2)+"\n")
    (truth/"sealed_truth.json").write_text(json.dumps(d["truth"],sort_keys=True,indent=2)+"\n")
    return d

if __name__=="__main__":
    d=write();print({"seed":SEED,"cases":len(d["manifest"]["cases"]),"truth_root_type":type(d["truth"]).__name__})
