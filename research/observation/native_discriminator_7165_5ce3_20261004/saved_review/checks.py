"""Post-run saved structural checks, not an authenticated native provenance certificate."""
def check_rows(rows):
    assert len(rows) == 21
    for row in rows:
        cursor = row['sequence_started_ns']
        stages = [('acquisition', row['acquisition'], ['title', 'parent', 'anchor'], False)]
        for arm in ('FULL_REACQUIRE', 'SIMILARITY_FIRST', 'MEMORY_CUE', 'FRESH_CUE'):
            fields = ['title', 'parent', 'anchor'] if arm == 'FULL_REACQUIRE' else ([] if arm == 'SIMILARITY_FIRST' else [row['hint']['field']])
            stages.append((arm, row['arms'][arm], fields, arm in ('FULL_REACQUIRE', 'SIMILARITY_FIRST')))
        for name, stage, fields, pixels in stages:
            if name == 'FULL_REACQUIRE' and 'fixture_mutation_started_ns' in row:
                assert cursor <= row['fixture_mutation_started_ns'] <= row['fixture_mutation_finished_ns']
                cursor = row['fixture_mutation_finished_ns']
            expected = []
            for record in stage['packet']['records']:
                w = record['id']; assert type(w) is int and w > 1
                # Compatible with the frozen renderer's consecutive pane/child/anchor
                # XIDs. This is source-structure consistency, NOT a retained QueryTree
                # reply or independent native identity/authentication certificate.
                parent, sibling = w-1, w+1
                for field in fields:
                    if field == 'title': expected.append(('GetProperty:WM_NAME', w))
                    elif field == 'parent': expected.extend([('QueryTree', w), ('GetProperty:parent.WM_NAME', parent)])
                    elif field == 'anchor': expected.extend([('QueryTree', w), ('QueryTree:parent', parent), ('GetProperty:sibling.WM_NAME', sibling)])
                    else: raise AssertionError('unknown field')
                if pixels: expected.append(('GetImage', w))
            calls = stage['calls']; assert len(calls) == len(expected) and calls
            first = calls[0]['start_ns']
            for call, (op, w) in zip(calls, expected):
                assert call['op'] == op and type(call['window']) is int and call['window'] == w
                assert type(call['start_ns']) is int and type(call['end_ns']) is int
                assert cursor <= call['start_ns'] <= call['end_ns'] <= row['sequence_finished_ns']
                cursor = call['end_ns']
            assert type(stage['elapsed_ns']) is int and stage['elapsed_ns'] >= calls[-1]['end_ns']-first
    return True
