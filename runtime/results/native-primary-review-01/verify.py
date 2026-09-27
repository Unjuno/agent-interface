"""Read-only checks of retained primary review evidence; no GUI or model calls."""
from pathlib import Path
import hashlib
import json
import tarfile


def read_archive(here, archive_name, manifest_name):
    manifest = json.loads((here/manifest_name).read_text())
    with tarfile.open(here/archive_name, 'r:gz') as archive:
        members = archive.getmembers()
        assert len(members) == len(manifest)
        assert len({m.name for m in members}) == len(members)
        data = {}
        for member in members:
            assert member.isfile()
            raw = archive.extractfile(member).read()
            assert {'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()} == manifest[member.name]
            data[member.name] = raw
    return data


def main():
    here = Path(__file__).resolve().parent
    data = read_archive(here, 'evidence.tar.gz', 'manifest.json')
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
    data = read_archive(here, 'stop-control.tar.gz', 'stop-control-manifest.json')
    prefix = 'native-primary-review-stop-01/'
    rows = read('tasks.json')
    assert len(rows) == 1 and read('allocation.json')['route'] == 'direct'
    assert read('task-1-primary-review-result.json')['decision']['outcome'] == 'uncertain'
    assert 'no next task' in read('task-1-primary-review-result.json')['error']
    evaluation = read('evaluation-at-close.json')
    assert evaluation['success'] is False and evaluation['record_count'] == 1
    assert evaluation['missing'] == [f'task-{i}' for i in range(2, 7)]
    assert prefix+'task-2-navigation-program.json' not in data
    assert len(data[prefix+'submission-history.jsonl'].splitlines()) == 1
    assert all(p['returncode'] is not None for p in read('cleanup.json'))
    for result in (rows[0]['navigation']['result']['result'], rows[0]['direct']['result']):
        release = result['execution']['releases'][-1]
        assert result['status'] == 'completed'
        assert release['verified'] and not release['keys_down'] and not release['buttons_down']
    print(json.dumps({'control_files':len(data), 'control':'explicit uncertainty stopped after task 1',
                      'scope':'injected control, not spontaneous model uncertainty'}))


if __name__ == '__main__':
    main()
