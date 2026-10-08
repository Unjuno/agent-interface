"""Exercise exact bytes and local output failures, including an actual pipe."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from presentation_emission_v1 import emit


class Partial(io.BytesIO):
    def write(self, data):
        return super().write(data[:3])


class Failing(Partial):
    def write(self, data):
        if self.tell() >= 3:
            raise BrokenPipeError('injected after three accepted bytes')
        return super().write(data)


class FlushFail(io.BytesIO):
    def flush(self):
        raise OSError('injected flush failure')


def main(root):
    root.mkdir(exist_ok=False, parents=True)
    value = {'attention': ['未確認', 'focus changed'], 'success': False}
    outcomes = []
    for name, stream, expected in [
            ('full', io.BytesIO(), 'locally_flushed'),
            ('short-writes', Partial(), 'locally_flushed'),
            ('broken-pipe', Failing(), 'failed'),
            ('flush-failure', FlushFail(), 'failed')]:
        directory = root / name
        try:
            emit(value, stream, directory)
        except OSError:
            assert expected == 'failed'
        receipt = json.loads((directory / 'receipt.json').read_text())
        payload = (directory / 'payload.bin').read_bytes()
        assert receipt['status'] == expected
        assert stream.getvalue() == payload[:receipt['accepted_bytes']]
        assert json.loads(payload) == value
        assert receipt['model_input_tokens'] is None
        assert receipt['model_received_ns'] is None
        assert ('flush_finished_ns' in receipt) == (expected == 'locally_flushed')
        outcomes.append(dict(case=name, **receipt))
    try:
        emit(value, io.BytesIO(), root / 'full')
    except FileExistsError:
        pass
    else:
        raise AssertionError('attempt overwritten')
    source = root / 'source.json'
    source.write_text(json.dumps(value), encoding='utf-8')
    process = subprocess.run([sys.executable, str(Path(__file__).with_name(
        'presentation_emission_v1.py')), str(source), str(root / 'pipe')],
        capture_output=True, check=True)
    assert process.stdout == (root / 'pipe' / 'payload.bin').read_bytes()
    assert not process.stderr
    (root / 'received.bin').write_bytes(process.stdout)
    report = dict(cases=outcomes, real_pipe_exact=True, overwrite_rejected=True,
                  received_sha256=hashlib.sha256(process.stdout).hexdigest(),
                  source_hashes={name: hashlib.sha256(Path(__file__).with_name(name).
                      read_bytes()).hexdigest() for name in
                      ['presentation_emission_v1.py', Path(__file__).name]},
                  scope='transport controls; no GUI or model token measurement')
    (root / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=len(outcomes), real_pipe_exact=True,
                          overwrite_rejected=True)))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
