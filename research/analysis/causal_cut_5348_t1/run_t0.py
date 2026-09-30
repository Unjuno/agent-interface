"""One-shot exhaustive prefix-cut replay for Issue #5348 T1."""
import json,platform,sys
from causal_core import build_raw
CORE_GIT_BLOB_SHA="302595c32bdfffc88b54c78c3fc4f54ac4e5c03e"
def main():
 raw=build_raw();raw["source_identity"]["core_git_blob_sha"]=CORE_GIT_BLOB_SHA
 raw["runtime"]={"python":platform.python_version(),"platform":sys.platform,"container":False,"output_file_written":False};raw["disposition"]="PASS_CAUSAL_CUT_CONSTRUCTION_SCOPED"
 print(json.dumps(raw,sort_keys=True,separators=(",",":")));return 0
if __name__=="__main__":raise SystemExit(main())
