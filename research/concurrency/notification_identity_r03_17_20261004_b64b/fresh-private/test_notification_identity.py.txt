"""Constructor-free regressions for exact notification consumption."""
from collections import deque
import copy
import threading
import unittest
from codex_app_server_client_v2 import CodexAppServerClient, AppServerError


def client(*rows, closed=False):
    result = object.__new__(CodexAppServerClient)
    result._condition = threading.Condition()
    result._notifications = deque(rows)
    result._notification_consumptions = 0
    result._closed = closed
    return result


class NotificationIdentityTests(unittest.TestCase):
    def setUp(self):
        self.a = {'method': 'turn/completed', 'params': {'threadId': '日本語-é',
                  'turn': {'id': 'A', 'intent': ['retain', {'target': '☀' * 1000}]}}}
        self.b = copy.deepcopy(self.a)
        self.b['params']['turn']['id'] = 'B'

    def test_healthy_queued_match_has_priority_over_zero_timeout(self):
        c = client(self.a, self.b)
        self.assertIs(c.wait_notification(lambda x: x is self.a, timeout=0), self.a)
        self.assertIs(c.wait_notification(lambda x: True, timeout=0), self.b)

    def test_reentrant_true_cannot_return_already_consumed_object(self):
        c = client(self.a, self.b)
        seen = []
        def predicate(row):
            seen.append(row)
            if row is self.a:
                self.assertIs(c.wait_notification(lambda x: x is self.a, timeout=0), self.a)
                return True
            return False
        with self.assertRaises(TimeoutError):
            c.wait_notification(predicate, timeout=0)
        self.assertEqual(len(seen), 2)
        self.assertIs(c.wait_notification(lambda x: True, timeout=0), self.b)

    def test_reentrant_false_does_not_invalidate_iteration(self):
        c = client(self.a, self.b)
        def predicate(row):
            if row is self.a:
                self.assertIs(c.wait_notification(lambda x: x is self.a, timeout=0), self.a)
            return False
        with self.assertRaises(TimeoutError):
            c.wait_notification(predicate, timeout=0)
        self.assertIs(c.wait_notification(lambda x: True, timeout=0), self.b)

    def test_distinct_equal_objects_are_consumed_by_identity(self):
        equal = copy.deepcopy(self.a)
        c = client(self.a, equal)
        def predicate(row):
            if row is self.a:
                self.assertIs(c.wait_notification(lambda x: x is self.a, timeout=0), self.a)
            return True
        self.assertIs(c.wait_notification(predicate, timeout=0), equal)
        with self.assertRaises(TimeoutError):
            c.wait_notification(lambda x: True, timeout=0)

    def test_nested_consumption_of_later_row_does_not_visit_stale_row(self):
        c = client(self.a, self.b)
        seen = []
        def predicate(row):
            seen.append(row)
            self.assertIs(c.wait_notification(lambda x: x is self.b, timeout=0), self.b)
            return False
        with self.assertRaises(TimeoutError):
            c.wait_notification(predicate, timeout=0)
        self.assertEqual(len(seen), 1)
        self.assertIs(seen[0], self.a)
        self.assertIs(c.wait_notification(lambda x: True, timeout=0), self.a)

    def test_truth_conversion_can_reenter(self):
        c = client(self.a, self.b)
        outer = self
        class Result:
            def __bool__(self):
                outer.assertIs(c.wait_notification(lambda x: x is outer.a, timeout=0), outer.a)
                return True
        with self.assertRaises(TimeoutError):
            c.wait_notification(lambda x: Result() if x is self.a else False, timeout=0)
        self.assertIs(c.wait_notification(lambda x: True, timeout=0), self.b)

    def test_predicate_exception_propagates_without_consumption(self):
        c = client(self.a, self.b)
        error = ValueError('predicate error')
        def predicate(row):
            raise error
        with self.assertRaises(ValueError) as raised:
            c.wait_notification(predicate, timeout=0)
        self.assertIs(raised.exception, error)
        self.assertIs(c.wait_notification(lambda x: True, timeout=0), self.a)
        self.assertIs(c.wait_notification(lambda x: True, timeout=0), self.b)

    def test_closed_queue_match_precedes_eof(self):
        c = client(self.a, closed=True)
        self.assertIs(c.wait_notification(lambda x: True, timeout=1), self.a)
        with self.assertRaises(AppServerError):
            c.wait_notification(lambda x: True, timeout=1)

    def test_closed_queue_miss_retains_notification(self):
        c = client(self.a, closed=True)
        with self.assertRaises(AppServerError):
            c.wait_notification(lambda x: False, timeout=1)
        self.assertIs(c.wait_notification(lambda x: True, timeout=0), self.a)

    def test_wait_turn_completed_retains_rich_params(self):
        c = client(self.b, self.a)
        self.assertIs(c.wait_turn_completed('日本語-é', 'A', timeout=0), self.a['params'])
        self.assertIs(c.wait_notification(lambda x: True, timeout=0), self.b)


class CountingDeque(deque):
    def __init__(self, rows):
        super().__init__(rows)
        self.visits = 0
    def __iter__(self):
        for row in super().__iter__():
            self.visits += 1
            yield row


class PureScanCostTests(unittest.TestCase):
    def test_unchanged_pure_false_scan_visits_linear_number_of_queue_rows(self):
        for n in [16, 64, 256, 1024]:
            with self.subTest(n=n):
                rows = [{'method': 'usage', 'params': {'id': i}} for i in range(n)]
                c = client(*rows)
                counted = CountingDeque(rows)
                c._notifications = counted
                with self.assertRaises(TimeoutError):
                    c.wait_notification(lambda row: False, timeout=0)
                print('QUEUE_VISITS', n, counted.visits)
                self.assertLessEqual(counted.visits, 3 * n + 4)
                for row in rows:
                    self.assertIs(c.wait_notification(lambda x: x is row, timeout=0), row)


if __name__ == '__main__':
    unittest.main()
