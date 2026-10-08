"""Emit actual observations, without assigning expected verdicts."""
import hashlib
import json
from pathlib import Path
import platform
import sys
from candidate import BeginBoundLifecycle
from fixtures import begun, receipt
from frozen_kernel import ContractError, RequestLifecycle


def main():
    root = Path(__file__).resolve().parent
    rows = []
    for arm, cls in [('baseline', RequestLifecycle), ('candidate', BeginBoundLifecycle)]:
        for begin in range(1, 5):
            for start in range(6):
                for end in range(start, 7):
                    for matching in (False, True):
                        flow = begun(cls, begin)
                        original_request = flow.request
                        accepted, error = True, None
                        try:
                            flow.record_execution(receipt(start, end, matching))
                        except ContractError:
                            accepted, error = False, 'ContractError'
                        rows.append(dict(arm=arm, begin_ns=begin, started_ns=start, ended_ns=end,
                            manifest_matches=matching, accepted=accepted, exception=error,
                            stage_after=flow.stage.value, execution_present=flow.execution is not None,
                            request_preserved=flow.request is original_request))
    freeze = (root / 'FREEZE.json').read_bytes()
    data = {'schema': 'begin-causality-v1', 'freeze_sha256': hashlib.sha256(freeze).hexdigest(),
        'source_commit': json.loads(freeze)['source_commit'], 'python': platform.python_version(),
        'platform': platform.platform(), 'rows': rows}
    with Path(sys.argv[1]).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    print(json.dumps({'rows': len(rows), 'output': sys.argv[1]}))


if __name__ == '__main__':
    main()
