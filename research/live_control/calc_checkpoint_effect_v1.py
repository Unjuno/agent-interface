"""Map a closed, post-terminal Calc checkpoint archive to a caller effect.

The caller supplies trusted task binding and same-clock terminal/checkpoint
metadata. This cannot prove that the preceding input caused the saved bytes.
"""
import re
from pathlib import Path
from research.live_control.calc_workbook_effect_v1 import score_workbook


def score_checkpoint(*, archive_dir, evidence, task_id, terminal_ns, sheet_name, expected_values):
    unavailable = {'status': 'unavailable'}
    if (type(evidence) is not dict or type(task_id) is not str or not task_id or
            type(terminal_ns) is not int or terminal_ns < 0 or
            evidence.get('task_id') != task_id or evidence.get('status') != 'VERIFIED' or
            evidence.get('observation_closed') is not True or
            type(evidence.get('sampled_ns')) is not int or
            type(evidence.get('source_sampled_ns')) is not int or
            type(evidence.get('archive_started_ns')) is not int or
            evidence['archive_started_ns'] <= terminal_ns or
            evidence['source_sampled_ns'] < evidence['archive_started_ns'] or
            evidence['sampled_ns'] < evidence['source_sampled_ns']):
        return unavailable
    digest = evidence.get('artifact_sha256')
    if type(digest) is not str or not re.fullmatch(r'[0-9a-f]{64}', digest):
        return unavailable
    try:
        root = Path(archive_dir).resolve(strict=True)
        artifact = (root / (digest + '.bin')).resolve(strict=True)
        if not root.is_dir() or artifact.parent != root or not artifact.is_file():
            return unavailable
        with artifact.open('rb') as stream:
            data = stream.read(8 * 1024 * 1024 + 1)
        if len(data) > 8 * 1024 * 1024:
            return unavailable
    except (OSError, RuntimeError, TypeError, ValueError):
        return unavailable
    return score_workbook(data, expected_digest=digest, sheet_name=sheet_name,
                          expected_values=expected_values,
                          evidence_ref='sha256:' + digest)