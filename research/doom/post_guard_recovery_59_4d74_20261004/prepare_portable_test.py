from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent;original=r/'planner-source-02/research/live_control/test_persistent_planner_adapter_v2.py';data=original.read_text();old='{"type": "localImage", "path": "C:\\\\frame.png"}';assert data.count(old)==1
out=r/'planner-portable-tests';out.mkdir(exist_ok=False);new='from pathlib import Path\n'+data.replace(old,'{"type": "localImage", "path": str(Path("C:/frame.png"))}');(out/'test_planner_portable.py').write_text(new)
(r/'planner-test-delta.json').write_text(json.dumps({'scope':'post-failure test portability correction only; production/frozen original unchanged','original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'delta':'expected localImage path uses str(Path(input)) rather than Windows-only spelling','tests_added':0,'original_first_fail_retained':True},indent=2)+'\n')
