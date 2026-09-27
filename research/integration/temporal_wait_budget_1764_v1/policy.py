"""A caller wait budget is not a source-event-time watermark. No input authority."""
from monitor import Monitor

FIELDS = {'session', 'producer_pid', 'sequence', 'source_ns', 'clock', 'kind', 'labels'}


class BoundedAB:
    def __init__(self, session: str, producer_pid: int, delta_ns: int, budget_ns: int):
        if not isinstance(session, str) or not session or len(session) > 128:
            raise ValueError('session')
        if any(type(v) is not int or v <= 0 for v in (producer_pid, delta_ns, budget_ns)):
            raise ValueError('integer parameters required')
        self.session, self.pid = session, producer_pid
        self.monitor = Monitor('AB', delta_ns)
        self.budget = budget_ns
        self.deadline = None
        self.expected = 1
        self.last_source_ns = None
        self.result = None
        self.returned_ns = None

    def finish(self, result: str, now: int):
        if self.result is None:
            self.result, self.returned_ns = result, now
        return self.result

    def timeout(self, now: int):
        if self.deadline is not None and now >= self.deadline:
            self.finish('TIMEOUT_UNRESOLVED', now)
        return self.result

    def feed(self, record: dict, now: int):
        # The one-shot caller result is never reopened by a late notification.
        if self.result is not None:
            return self.result
        self.timeout(now)
        if self.result is not None:
            return self.result
        if (type(now) is not int or now < 0 or type(record) is not dict
                or set(record) != FIELDS
                or record['session'] != self.session
                or type(record['producer_pid']) is not int or record['producer_pid'] != self.pid
                or record['clock'] != 'same-kernel-monotonic-ns'
                or type(record['sequence']) is not int or record['sequence'] < 1
                or type(record['source_ns']) is not int or not 0 <= record['source_ns'] <= now
                or (self.last_source_ns is not None and record['source_ns'] < self.last_source_ns)
                or type(record['labels']) is not list
                or record['kind'] not in ('event', 'watermark')
                or (record['kind'] == 'event' and record['labels'] not in (['A'], ['B']))
                or (record['kind'] == 'watermark' and record['labels'] != [])):
            return self.finish('UNKNOWN_INVALID_EVIDENCE', now)
        if record['sequence'] != self.expected:
            return self.finish('UNKNOWN_INCOMPLETE_PREFIX', now)
        if self.expected == 1 and record['labels'] != ['A']:
            return self.finish('UNKNOWN_INVALID_EVIDENCE', now)
        self.expected += 1
        self.last_source_ns = record['source_ns']
        if self.deadline is None:
            self.deadline = now + self.budget
        status = self.monitor.feed(record['source_ns'], record['labels'])
        if status != 'PENDING':
            self.finish(status, now)
        return self.result

    def view(self):
        return {'result': self.result, 'returned_ns': self.returned_ns,
                'deadline_ns': self.deadline, 'source_monitor_status': self.monitor.status,
                'next_sequence': self.expected, 'authority': 'none',
                'input_dispatched': False, 'task_success': None,
                'acknowledged': False, 'synthetic_source_ticks': 0}
