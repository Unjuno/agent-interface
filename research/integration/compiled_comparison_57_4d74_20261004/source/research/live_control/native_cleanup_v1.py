"""Close one private allocation before publishing its terminal reply."""
import shutil
import time

from native_exchange_v1 import encoded, publish


def finish_allocation(out, workloads, bridge, session, reply):
    """Attempt every cleanup stage; report only tracked process termination.

    This does not prove owner-process exit, descendant exit, or input release.
    A failed task and a failed cleanup are independent outcomes.
    """
    report = {'schema': 'agent-interface/native-cleanup-v1',
              'started_ns': time.monotonic_ns(), 'errors': [], 'processes': [],
              'scope': 'artifact_copy_connections_and_tracked_processes',
              'owner_exit_verified': False, 'descendants_verified': False}

    def attempt(label, operation):
        try:
            return operation()
        except Exception as error:
            report['errors'].append({'stage': label, 'type': type(error).__name__,
                                     'message': str(error)})

    for app, data in workloads.items():
        # A missing expected artifact is also a failed preservation attempt.
        attempt('copy:' + app, lambda data=data: shutil.copyfile(
            data['output'], out / data['output'].name))
    if bridge is not None:
        attempt('bridge.close', bridge.close)
    if session is not None:
        attempt('session.close', session.close)
        for process in session.procs:
            code = attempt('process.poll:' + str(process.pid), process.poll)
            report['processes'].append({'pid': process.pid, 'returncode': code})
    report['tracked_processes_terminal'] = all(
        item['returncode'] is not None for item in report['processes'])
    # Keep the existing artifact format for independent historical readers.
    attempt('cleanup.json', lambda: (out / 'cleanup.json').write_bytes(
        encoded(report['processes'])))
    report['status'] = ('completed' if not report['errors'] and
                        report['tracked_processes_terminal'] else 'needs_review')
    report['ended_ns'] = time.monotonic_ns()
    attempt('cleanup-report.json', lambda: (out / 'cleanup-report.json').write_bytes(
        encoded(report)))
    if report['errors']:
        report['status'] = 'needs_review'
    if reply is not None:
        final = dict(reply, cleanup=report)
        if report['status'] != 'completed':
            final.update(status='needs_review', task_success=None)
        # The immutable reply is the final publication, after all attempts.
        publish(out / f"reply-{reply['stage']}.json", encoded(final))
    return report
