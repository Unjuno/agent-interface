"""Offline evidence linkage. Never infers model perception or physical causality."""
import hashlib
import json
from pathlib import Path


def build(events):
    nodes = []
    edges = []
    observations = {}
    commands = {}
    accepted = {}
    terminals = {}
    gaps = []

    def link(source, relation, target):
        edges.append(dict(source=source, relation=relation, target=target))

    for line, row in enumerate(events, 1):
        ref = f'event:{line}'
        kind = row['event']
        nodes.append(dict(id=ref, source_line=line, kind=kind))
        pid = row.get('id')
        if kind == 'observation':
            seq = row['sequence']
            if seq in observations:
                raise ValueError('duplicate observation')
            observations[seq] = (ref, row)
            nodes[-1].update(sequence=seq, image=Path(row['image']).name)
        elif kind == 'command' and row['command']['op'] == 'submit':
            command = row['command']
            pid = command['id']
            if pid in commands:
                raise ValueError('duplicate program')
            seq = command['expected_sequence']
            if seq not in observations or seq != max(observations):
                raise ValueError('missing or stale declared observation')
            commands[pid] = (ref, row)
            link(observations[seq][0], 'declared_expected_observation_for', ref)
            for step in command['steps']:
                if 'source_sequence' in step:
                    if step['source_sequence'] != seq:
                        raise ValueError('source/expected observation mismatch')
                    link(observations[seq][0], 'declared_controller_source_for', ref)
            if terminals:
                previous_id = next(reversed(terminals))
                previous_ref, previous = terminals[previous_id]
                link(previous_ref, 'observed_before', ref)
                gaps.append(dict(previous=previous_id, next=pid,
                                 terminal_to_command_ms=(row['received_ns']-previous['terminal_ns'])/1e6))
        elif kind == 'accepted':
            if pid not in commands or pid in accepted:
                raise ValueError('unbound or duplicate acceptance')
            command_ref, command_row = commands[pid]
            if row['valid_until_ns'] != command_row['command']['valid_until_ns']:
                raise ValueError('authority deadline mismatch')
            accepted[pid] = (ref, row)
            link(command_ref, 'accepted_as', ref)
        elif kind == 'pointer_admission':
            if pid not in accepted:
                raise ValueError('input without recorded acceptance')
            authority_ref, authority = accepted[pid]
            if row['valid_until_ns'] != authority['valid_until_ns']:
                raise ValueError('input authority mismatch')
            if not authority['accepted_ns'] <= row['admitted_ns'] < row['valid_until_ns']:
                raise ValueError('input outside recorded authority interval')
            link(authority_ref, 'recorded_admission_for', ref)
        elif kind == 'servo_feedback':
            seq = row['observation']
            if seq not in observations or observations[seq][1]['id'] != pid:
                raise ValueError('feedback observation misattributed')
            link(observations[seq][0], 'explicit_feedback_input_for', ref)
            nodes[-1].update(producer='patch_servo', reason=row['reason'])
        elif kind == 'terminal':
            if pid not in accepted or pid in terminals:
                raise ValueError('unbound or duplicate terminal')
            terminals[pid] = (ref, row)
            link(accepted[pid][0], 'program_terminal', ref)
        elif kind == 'independent_evaluation':
            nodes[-1].update(success=row['success'], actual=row.get('actual'))
            for terminal_ref, _ in terminals.values():
                link(terminal_ref, 'observed_before_evaluation', ref)
    ids = {n['id'] for n in nodes}
    if any(e['source'] not in ids or e['target'] not in ids for e in edges):
        raise ValueError('dangling edge')
    return dict(schema='offline-evidence-lineage-v1', nodes=nodes, edges=edges,
                gaps=gaps, unresolved=[
                    'Expected sequence does not prove which image the model viewed.',
                    'No model decision IDs, delivery completion or reply computation endpoints.',
                    'Pointer admission links are not complete key/release action lineage.',
                    'Historical authority IDs are represented by acceptance references only.',
                    'Feedback command is a proposal; execution causality needs explicit reply IDs.',
                    'Final evaluation follows programs; individual action effect causality is unknown.',
                    'No token measurement, live tracing overhead measurement or held-out claim.'])


def export(root, out):
    events = [json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
    graph = build(events)
    paths = [Path(__file__), root/'events.jsonl', root/'delivered.jsonl',
             root/'owner-events.json', root/'shape.svg', root/'sources.json']
    paths += sorted(root.glob('*.png')) + sorted(root.glob('*.ait'))
    base = Path(__file__).resolve().parent
    graph['artifacts'] = {str(p.resolve().relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    graph['evaluation_artifact'] = str((root/'shape.svg').relative_to(base))
    out.write_text(json.dumps(graph, indent=2)+'\n')
    return graph
