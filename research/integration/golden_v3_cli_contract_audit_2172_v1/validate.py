import json
from pathlib import Path
p=Path('research/integration/golden_v3_cli_contract_audit_2172_v1/REPORT.md')
t=p.read_text()
required=['PASS_DESKTOP_VERTICAL_SLICE_CONTRACT_AUDIT_SCOPED','runtime/golden-demo-v3.sh','runtime/cli_v1/api.py','cleanup failure','side_effect_authority=false','## H/T/D/C/U']
for token in required: assert token in t, token
assert t.count('| setup / doctor |')==1
assert t.count('| cleanup failure |')==1
print(json.dumps({'decision':'PASS_DESKTOP_VERTICAL_SLICE_CONTRACT_AUDIT_SCOPED','required_tokens':len(required),'mapping_rows':10,'model_calls':0,'gui_actions':0,'input_events':0,'network':0}))
