from __future__ import annotations

def normalize(post_release, *, release_sequence, lifecycle_deadline_ns, snapshot_finished_ns):
    seqs=list((post_release or {}).get('sequences') or [])
    selected=seqs[-1] if seqs else None
    return {
      'captures': (post_release or {}).get('captures',0),
      'sequences': seqs,
      'sequence': selected,
      'selection_rule': 'latest',
      'error': (post_release or {}).get('error'),
      'grants_input_authority': False,
      'tail_program_steps_resumed': 0,
      'sequence_advanced': type(selected) is int and selected > release_sequence,
      'snapshot_finished_ns': snapshot_finished_ns,
      'lifecycle_deadline_ns': lifecycle_deadline_ns,
      'within_lifecycle_deadline': snapshot_finished_ns <= lifecycle_deadline_ns,
      'source': 'unchanged post_release_observation_v2 collection; actual capture cardinality retained'
    }
