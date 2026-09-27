"""Verify retained notices, images, effects, release and descriptive timing only."""
import hashlib
import json
from pathlib import Path
import runpy
import statistics


def main():
    here = Path(__file__).resolve().parent
    read_archive = runpy.run_path(str(here.parent/'native-primary-review-01/verify.py'))['read_archive']
    data = read_archive(here, 'evidence.tar.gz', 'manifest.json')
    baseline = read_archive(here.parent/'native-primary-review-01', 'evidence.tar.gz', 'manifest.json')
    def read(name):
        return json.loads(data['native-review-notice-01/'+name])
    rows, goals = read('tasks.json'), read('goal.json')['tasks']
    history = [json.loads(line) for line in data['native-review-notice-01/submission-history.jsonl'].splitlines()]
    notices = []
    events = read('transport-events.json')['events']
    for event in events:
        for line in event['response']['output'].splitlines():
            if line.startswith('{"needs_primary_review"'):
                notices.append(json.loads(line))
    assert len(rows) == len(history) == len(notices) == len(goals) == 6
    assert events[-1]['response']['exit_code'] == 0
    previous_review = 0
    releases_checked = 0
    for row, submitted, notice, goal in zip(rows, history, notices, goals):
        task = row['task_id']
        assert task == submitted['task_id'] == notice['needs_primary_review'] == goal['task_id']
        assert submitted['submitted_values'] == [goal['token']]
        request = read(task+'-primary-review-request.json')
        result = read(task+'-primary-review-result.json')
        assert result == row['primary_review']
        assert result['decision'] == read(task+'-primary-review.json')
        assert result['decision']['source_sequence'] == notice['source_sequence'] == request['source_sequence']
        assert result['decision']['outcome'] == 'complete'
        assert row['navigation']['result']['result']['execution']['started_ns'] > previous_review
        previous_review = result['review_received_ns']
        assert row['action_started_ns'] < row['feedback_received_ns'] < result['review_requested_ns'] <= previous_review
        assert abs(result['feedback_to_review_ms']-(previous_review-row['feedback_received_ns'])/1e6) < 1e-6
        artifact = request['source']['native']['artifact']
        assert notice['image'] == artifact['path']
        assert hashlib.sha256(data[artifact['path'].split('/results-local/',1)[1]]).hexdigest() == artifact['sha256']
        summary = notice['receipt_summary']
        assert summary['task_success'] is None and summary['authority'] == 'none'
        assert summary['feedback']['status'] == row['feedback']['status'] == 'matched'
        for name in ('navigation', 'entered', 'repaired_enter', 'saved'):
            if name not in row:
                continue
            raw, shown = row[name], summary['operations'][name]
            if name == 'navigation':
                raw = raw['result']['result']
            assert raw['status'] == shown['status']
            assert raw.get('error') == shown.get('error')
            assert raw.get('input_dispatched') == shown.get('input_dispatched')
            if raw['status'] == 'completed':
                assert shown['execution']['releases'] == raw['execution']['releases']
                release = raw['execution']['releases'][-1]
                assert release['verified'] and not release['keys_down'] and not release['buttons_down']
                releases_checked += 1
    assert releases_checked == 18
    assert rows[3]['refusal_emissions'] == notices[3]['receipt_summary']['refusal_emissions'] == 0
    assert read('evaluation-at-close.json')['success'] is True
    assert all(p['returncode'] is not None for p in read('cleanup.json'))
    comparison = read('comparison.json')
    assert comparison == json.loads((here/'comparison.json').read_text())
    old = json.loads(baseline['native-primary-review-01/tasks.json'])
    for arm, records in [('baseline',old), ('candidate',rows)]:
        values = [r['primary_review']['feedback_to_review_ms'] for r in records]
        assert comparison[arm+'_median_feedback_to_review_ms'] == statistics.median(values)
        for saved, row in zip(comparison['rows'], records):
            assert saved[arm+'_feedback_ms'] == row['through_feedback_ms']
            assert saved[arm+'_feedback_to_review_ms'] == row['primary_review']['feedback_to_review_ms']
    repair = read('repair-notice-readonly-replay.json')['notice']
    assert repair['receipt_summary']['operations']['entered']['status'] == 'refused'
    assert repair['receipt_summary']['refusal_emissions'] == 0
    assert json.loads(data['native-review-notice-ci-01/result.json'])['status'] == 'PASS'
    print(json.dumps({'files':len(data), 'exact_tasks':6, 'notices_checked':6,
                      'baseline_review_median_ms':comparison['baseline_median_feedback_to_review_ms'],
                      'candidate_review_median_ms':comparison['candidate_median_feedback_to_review_ms'],
                      'scope':'descriptive sequential observations; no causal speed or token claim'}))


if __name__ == '__main__':
    main()
