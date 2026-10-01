import json
from decimal import Decimal
from pathlib import Path
p=Path(__file__).parent
f=json.loads((p/'fixture.json').read_text())
assert f['schema']=='integrated_efficiency_phase_ledger_fixture_v1'
assert set(f['arms'])=={'plain','ephemeral','persistent'}
assert all(len(v['tasks'])==6 for v in f['arms'].values())
assert all(len(x)==40 for x in f['source_git_blobs'].values())
assert not (p/'RESULT.json').exists()
assert sum(t['cached_input_tokens'] for a in f['arms'].values() for t in a['tasks'])==4864
assert sum(Decimal(str(t['elapsed_ms'])) for t in f['arms']['persistent']['tasks'])==Decimal('44131.281228')
print('PASS mechanics: 3 arms, 18 tasks, frozen extraction sanity, RESULT absent')
