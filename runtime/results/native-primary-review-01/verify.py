"""Read-only checks of retained primary review evidence; no GUI or model calls."""
from pathlib import Path
import hashlib
import json
import tarfile


def main():
    here = Path(__file__).resolve().parent
    manifest = json.loads((here/'manifest.json').read_text())
    with tarfile.open(here/'evidence.tar.gz', 'r:gz') as archive:
        members = archive.getmembers()
        assert len(members) == len(manifest)
        assert len({m.name for m in members}) == len(members)
        data = {}
        for member in members:
            assert member.isfile()
            raw = archive.extractfile(member).read()
            assert {'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()} == manifest[member.name]
            data[member.name] = raw
    prefix = 'native-primary-review-01/'
    def read(name):
        return json.loads(data[prefix+name])
    rows = read('tasks.json')
    goal = read('goal.json')
    history = [json.loads(line) for line in data[prefix+'submission-history.jsonl'].splitlines()]
    assert len(rows) == len(history) == len(goal['tasks']) == 6
    assert read('evaluation-at-close.json')['success'] is True
    releases = 0
    last_review = 0
    for row, task, submitted in zip(rows, goal['tasks'], history):
        task_id = task['task_id']
        assert row['task_id'] == submitted['task_id'] == task_id
        assert submitted['submitted_values'] == [task['token']]
        review = read(task_id+'-primary-review-result.json')
        request = read(task_id+'-primary-review-request.json')
        decision = read(task_id+'-primary-review.json')
        assert review == row['primary_review']
        assert decision == review['decision']
        assert decision['outcome'] == 'complete'
        assert decision['task_id'] == task_id
        assert decision['source_sequence'] == request['source_sequence']
        assert row['action_started_ns'] < row['feedback_received_ns'] <= review['review_requested_ns'] <= review['review_received_ns']
        assert abs(review['action_to_review_ms']-(review['review_received_ns']-row['action_started_ns'])/1e6) < 1e-6
        assert abs(review['feedback_to_review_ms']-(review['review_received_ns']-row['feedback_received_ns'])/1e6) < 1e-6
        assert row['navigation']['result']['result']['execution']['started_ns'] > last_review
        last_review = review['review_received_ns']
        artifact = request['source']['native']['artifact']
        relative = artifact['path'].split('/results-local/', 1)[1]
        assert hashlib.sha256(data[relative]).hexdigest() == artifact['sha256']
        entered = row.get('repaired_enter', row['entered'])
        for result in (row['navigation']['result']['result'], entered, row['saved']):
            assert result['status'] == 'completed'
            release = result['execution']['releases'][-1]
            assert release['verified'] is True and not release['keys_down'] and not release['buttons_down']
            releases += 1
    assert rows[3]['entered']['status'] == 'refused' and rows[3]['refusal_emissions'] == 0
    assert all(p['returncode'] is not None for p in read('cleanup.json'))
    assert json.loads(data['native-primary-review-ci-01/result.json'])['status'] == 'PASS'
    print(json.dumps({'files':len(data), 'exact_tasks':6, 'primary_reviews':6,
                      'verified_releases':releases, 'scope':'retained mechanics, not model identity or speed benefit'}))


if __name__ == '__main__':
    main()
