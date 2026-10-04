"""Aggregate the eight registered episodes without dropping interruptions."""
import hashlib
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan_path = HERE / 'recovery_comparison_plan_v1.json'
    plan = read(plan_path)
    assert sha(HERE / 'RECOVERY_COMPARISON.md') == plan['protocol_sha256']
    for path, digest in plan['sources'].items():
        assert sha(HERE.parent / path) == digest
    rows = []
    evidence = {}
    for cell in plan['schedule']:
        number = cell['pair']
        cohort = HERE / f'results/recovery-pair{number}-01'
        arms = {}
        sources = {}
        for arm in ('A', 'B'):
            root = cohort / arm
            metadata = read(root / 'initial/execution.json')
            assert all(metadata[key] == cell[key] for key in ('pair', 'domain', 'depth', 'seed'))
            assert metadata['arm'] == arm and metadata['plan_sha256'] == sha(plan_path)
            assert metadata['runner_sha256'] == sha(HERE / f'recovery_pair{number}_v1.py')
            runtime = root / 'runtime'
            manifest = runtime / ('sources.json' if number < 3 else 'manifest.json')
            sources[arm] = read(manifest)
            source_map = sources[arm] if number < 3 else sources[arm]['sources']
            for path, digest in source_map.items():
                assert sha(HERE.parent / path) == digest, path
            raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
            final = raw[-1]
            assert final['event'] == 'independent_evaluation' and final['success']
            observations = [e for e in raw if e['event'] == 'observation']
            recovery = sorted(p for p in root.glob('recover*') if p.is_dir())
            assert len(recovery) == (4 if arm == 'A' and cell['depth'] == 3 else 1)
            if arm == 'B':
                drain = read(recovery[0] / 'drain-report.json')
                reads = drain['reads']
                assert drain['state'] == 'own_clock_received_review_required'
            else:
                reads = [{'request': read(p / 'query-0-request.json'), 'reply': read(p / 'query-0-reply.json')} for p in recovery]
            assert len(reads) == (4 if cell['depth'] == 3 else 1)
            assert all('command' not in item['request'] for item in reads)
            for item in reads:
                assert item['reply']['records'] == raw[item['request']['after']:item['reply']['cursor']]
            terminals = [e for e in raw if e['event'] == 'terminal']
            arms[arm] = {
                'recovery_orchestration_calls': len(recovery), 'recovery_socket_reads': len(reads),
                'capture_to_evaluation_seconds': (final.get('known_ns', final.get('emitted_ns')) - observations[0]['capture_ns']) / 1e9,
                'final_success': True,
                'noncompleted_programs': [{'id': e['id'], 'status': e['status']} for e in terminals if e['status'] != 'completed'],
                'verified_model_id': metadata['verified_model_id'],
                'verified_model_configuration': metadata['verified_model_configuration'],
                'presentation': read(root / 'presentation.json') if (root / 'presentation.json').exists() else None,
            }
            for file in root.rglob('*'):
                if file.is_file():
                    evidence[str(file.relative_to(HERE))] = sha(file)
        assert sources['A'] == sources['B']
        assert (cohort / 'A/runtime/001.png').read_bytes() == (cohort / 'B/runtime/001.png').read_bytes()
        steps = ['move/move-save-steps.json'] if number < 3 else ['open/open-toolbar-steps.json', 'build/build-road-steps.json']
        for path in steps:
            assert read(cohort / 'A' / path) == read(cohort / 'B' / path)
        rows.append({
            **cell, 'arms': arms, 'initial_png_steps_runtime_sources_equal': True,
            'calls_delta_B_minus_A': arms['B']['recovery_orchestration_calls'] - arms['A']['recovery_orchestration_calls'],
            'reads_delta_B_minus_A': arms['B']['recovery_socket_reads'] - arms['A']['recovery_socket_reads'],
            'elapsed_delta_B_minus_A_seconds': arms['B']['capture_to_evaluation_seconds'] - arms['A']['capture_to_evaluation_seconds'],
        })
    stats = {}
    for key in ('calls_delta_B_minus_A', 'reads_delta_B_minus_A', 'elapsed_delta_B_minus_A_seconds'):
        values = [row[key] for row in rows]
        stats[key] = {'values': values, 'median': statistics.median(values), 'min': min(values), 'max': max(values)}
    result = {
        'aggregator_sha256': sha(Path(__file__)), 'plan_sha256': sha(plan_path),
        'episodes': 8, 'pairs': rows, 'statistics': stats,
        'structural_call_threshold_met': all(row['calls_delta_B_minus_A'] <= (-1 if row['depth'] == 3 else 0) for row in rows),
        'complete_primary_delivery_qualified': False,
        'delivery_limit': 'Pair 4 A final image delivery appeared black; prior identical image was used and one extra image-only call failed. Structural stage counts do not prove successful final image delivery.',
        'model_performance_qualified': False,
        'decision': 'Retain explicit read-only batching convenience. No latency/token promotion or research freeze. Stop this allocation; prioritize bounded evidence presentation and authoritative receipt/accounting.',
        'evidence_sha256': evidence,
    }
    out = HERE / 'results/recovery-aggregate-01'
    out.mkdir(exist_ok=True)
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('pairs', 'evidence_sha256')}, indent=2))


if __name__ == '__main__':
    main()
