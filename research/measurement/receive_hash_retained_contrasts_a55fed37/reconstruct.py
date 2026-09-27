"""Read-only extraction from the exact retained ZIP; executes no archive code."""
from __future__ import annotations
import argparse
import base64
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import zipfile

ARCHIVE_SHA256 = 'a55fed37ce2d65e132577aa9c1f754f8229524faf3ccf5eb4413000f368afa74'
PREFIX = 'research/live_control/x11_receive_hash_handoff_allocation04/'
FIELDS = ['block', 'load', 'mode', 'case_id', 'samples', 'received',
          'fresh_completions', 'median_age_twice_ns', 'cues',
          'source_cues', 'current_delivery_cues', 'bad_cues']
MODES = ('single_whole', 'single_chunked', 'batch_whole', 'batch_chunked')

def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def uint(value: object) -> bool:
    return type(value) is int and value >= 0

def packet(raw: bytes) -> tuple[dict, int]:
    require(len(raw) >= 4, 'short packet')
    length = int.from_bytes(raw[:4], 'big')
    require(length <= 1024 and len(raw) == 4 + length + 4096, 'packet extent')
    obj = json.loads(raw[4:4 + length])
    keys = {'case_id', 'seq', 'capture_start_ns', 'capture_end_ns',
            'python_return_ns', 'serialize_start_ns', 'pixel_sha256'}
    require(type(obj) is dict and set(obj) == keys, 'packet schema')
    require(all(uint(obj[k]) for k in keys - {'case_id', 'pixel_sha256'}), 'packet integer')
    require(type(obj['case_id']) is str, 'packet case type')
    times = [obj[k] for k in ('capture_start_ns', 'capture_end_ns',
                              'python_return_ns', 'serialize_start_ns')]
    require(times == sorted(times), 'packet time order')
    pixels = raw[4 + length:]
    require(sha(pixels) == obj['pixel_sha256'], 'pixel digest')
    rgb = [pixels[i:i + 3] for i in range(0, 4096, 4)]
    require(all(v in (b'\x10\x10\x10', b'\x32\x32\xdc') for v in rgb), 'pixel vocabulary')
    return obj, rgb.count(b'\x32\x32\xdc')

def reconstruct(path: Path) -> tuple[bytes, dict]:
    content = path.read_bytes()
    require(sha(content) == ARCHIVE_SHA256, 'archive identity')
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'duplicate archive member')
        manifest = json.loads(archive.read('MANIFEST.json'))
        require(set(names) == set(manifest['members']) | {'MANIFEST.json'}, 'archive inventory')
        require(manifest['member_count'] == len(manifest['members']) == 738, 'member denominator')
        for name, expected in manifest['members'].items():
            data = archive.read(name)
            require(len(data) == expected['bytes'] and sha(data) == expected['sha256'], 'member:' + name)
        def raw(name: str) -> bytes:
            return archive.read(PREFIX + name)
        def obj(name: str):
            data = raw(name)
            if name.endswith('.gz'):
                with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
                    data = stream.read(16_000_001)
                require(len(data) <= 16_000_000, 'expanded member limit')
            return json.loads(data)
        freeze = obj('FREEZE.json')
        for name, expected in freeze['sha256'].items():
            require(sha(raw(name)) == expected, 'frozen source:' + name)
        original = obj('AUDIT.json')
        require(original['decision'] == 'HOLD_CUE_INTEGRITY' and original['errors'] == [], 'original disposition')
        run = obj('formal-04/run.json')
        require(run['status'] == 'COMPLETE' and len(run['cases']) == 32, 'execution denominator')
        schedule = []
        for block in range(4):
            for load in (('idle', 'busy') if block % 2 == 0 else ('busy', 'idle')):
                for mode in MODES[block:] + MODES[:block]:
                    schedule.append(dict(block=block, load=load, mode=mode,
                                         case_id=f'b{block:02d}-{load}-{mode}'))
        require(run['schedule'] == freeze['schedule'] == schedule, 'source schedule')
        rows, violations = [], []
        for index, expected in enumerate(schedule):
            cid = expected['case_id']
            execution = run['cases'][index]
            require(all(execution[k] == v for k, v in expected.items()), 'case identity')
            require(type(execution['exit']) is int and execution['exit'] == 0, 'case exit')
            leaf = f'formal-04/batches/{index:02d}/{cid}/'
            observer, consumer, fixture = (obj(leaf + name) for name in
                ('observer.json.gz', 'consumer.json.gz', 'fixture.json'))
            cues = fixture['cues']
            require(len(cues) == 12, 'cue denominator')
            bad = 0
            for number, cue in enumerate(cues, 1):
                stamps = [cue['due_ns'], *cue['on'], *cue['off']]
                require(cue['cue'] == number and all(uint(t) for t in stamps)
                        and stamps == sorted(stamps), 'cue identity/time')
                width = cue['off'][0] - cue['on'][1]
                if not 4_000_000 <= width <= 8_000_000:
                    violations.append(dict(case_id=cid, cue=number, width_ns=width))
                    bad += 1
            sent, candidates, source_seen = {}, {}, set()
            for number, sample in enumerate(observer['rows'], 1):
                require(type(sample['seq']) is int and sample['seq'] == number, 'sample sequence')
                encoded = base64.b64decode(sample['packet_b64'], validate=True)
                metadata, red = packet(encoded)
                require(metadata['case_id'] == cid and metadata['seq'] == number, 'sample binding')
                clocks = sample['clocks']
                require(len(clocks) == 6 and all(uint(t) for t in clocks)
                        and clocks == sorted(clocks), 'native clock order')
                require([metadata[k] for k in ('capture_start_ns', 'capture_end_ns', 'python_return_ns')]
                        == [clocks[2], clocks[3], clocks[5]], 'native packet clock binding')
                overlap = [cue for cue in cues if metadata['capture_start_ns'] <= cue['off'][1]
                           and metadata['capture_end_ns'] >= cue['on'][0]] if red >= 512 else []
                require(red < 512 or len(overlap) > 0, 'positive without cue support')
                candidates[number] = overlap
                if len(overlap) == 1:
                    source_seen.add(overlap[0]['cue'])
                require(sample['send_status'] in ('sent', 'backpressure'), 'send status')
                expected_bytes = len(encoded) if sample['send_status'] == 'sent' else 0
                require(type(sample['send_bytes']) is int and sample['send_bytes'] == expected_bytes, 'send count')
                if sample['send_status'] == 'sent':
                    sent[number] = encoded
            ages, seen, current = [], set(), set()
            previous = 0
            for receipt in consumer['rows']:
                encoded = base64.b64decode(receipt['packet_b64'], validate=True)
                metadata, _ = packet(encoded)
                seq = metadata['seq']
                require(seq > previous and seq not in seen and sent.get(seq) == encoded, 'delivery identity/order')
                previous = seq
                seen.add(seq)
                received, completed = receipt['received_ns'], receipt['parsed_ns']
                require(uint(received) and uint(completed) and
                        metadata['serialize_start_ns'] <= received <= completed, 'receipt clock order')
                receipt_age = received - metadata['capture_start_ns']
                require(receipt['decision'] == ('FRAME_FRESH' if receipt_age <= 20_000_000 else 'YIELD_STALE'), 'receipt decision')
                ages.append(completed - metadata['capture_start_ns'])
                overlap = candidates[seq]
                if len(overlap) == 1 and overlap[0]['on'][1] <= received <= overlap[0]['off'][0]:
                    current.add(overlap[0]['cue'])
            require(seen == set(sent) and len(ages) > 0, 'delivered denominator')
            ages.sort()
            n = len(ages)
            median2 = ages[(n - 1) // 2] + ages[n // 2]
            row = dict(expected, samples=len(observer['rows']), received=n,
                       fresh_completions=sum(a <= 20_000_000 for a in ages),
                       median_age_twice_ns=median2, cues=12, source_cues=len(source_seen),
                       current_delivery_cues=len(current), bad_cues=bad)
            old = original['cases'][index]
            for key in set(row) - {'median_age_twice_ns', 'bad_cues'}:
                require(row[key] == old[key], 'independent vs original:' + key)
            require(median2 / 2_000_000 == old['capture_start_to_validation_complete']['median_ms'], 'original median')
            rows.append(row)
        require(violations == original['cue_integrity_errors'], 'original cue violations')
        buf = io.StringIO(newline='')
        writer = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
        csv_bytes = buf.getvalue().encode()
        verification = dict(status='POSTHOC_RECONSTRUCTION_VERIFIED', archive_sha256=ARCHIVE_SHA256,
            manifest_members_verified=738, frozen_sources_verified=len(freeze['sha256']),
            original_audit_sha256=sha(raw('AUDIT.json')), original_freeze_sha256=sha(raw('FREEZE.json')),
            original_decision=original['decision'], cue_violations=violations, cases=len(rows),
            captures=sum(r['samples'] for r in rows), received=sum(r['received'] for r in rows),
            csv_sha256=sha(csv_bytes), live_experiment_reruns=0,
            scope='Independent packet/count/time reconstruction; full lifecycle re-audit is a separate recorded check')
        return csv_bytes, verification

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path, help='new output directory; never overwritten')
    args = parser.parse_args()
    require(not args.output.exists(), 'output already exists')
    data, verification = reconstruct(args.archive)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'cases.csv').write_bytes(data)
    (args.output / 'RECONSTRUCTION.json').write_text(json.dumps(verification, sort_keys=True, indent=2) + '\n')
    print(json.dumps(verification, sort_keys=True))

if __name__ == '__main__':
    main()
