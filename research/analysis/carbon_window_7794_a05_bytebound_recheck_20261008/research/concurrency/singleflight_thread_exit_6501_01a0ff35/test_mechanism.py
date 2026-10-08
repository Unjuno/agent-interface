import unittest
from mechanism import run_case


class WorkerLifetimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_closing_rejoin_cannot_overlap_blocking_callable(self):
        row = await run_case('future_ack', 'early_rejoin')
        entries = [e for e in row['events'] if e['event'] == 'worker_enter']
        self.assertEqual(len(entries), 1)
        self.assertEqual(max(e['active_callables'] for e in entries), 1)
        self.assertEqual(sum(e['event'] == 'caller_yield' for e in row['events']), 1)

    async def test_unaffected_waiter_progress_survives_one_detach(self):
        row = await run_case('future_ack', 'one_detach')
        self.assertEqual(sum(e['event'] == 'worker_enter' for e in row['events']), 1)
        self.assertEqual(sum(e['event'] == 'caller_deliver' for e in row['events']), 2)

    async def test_post_exit_rejoin_starts_fresh_and_cleanup_is_complete(self):
        row = await run_case('future_ack', 'post_exit_rejoin')
        self.assertEqual(sum(e['event'] == 'worker_enter' for e in row['events']), 2)
        self.assertEqual(row['events'][-1], dict(sequence=len(row['events'])-1,
            event='cleanup', active_callables=0, wrappers_done=True, futures_done=True,
            registry_empty=True, executor_shutdown=True))


if __name__ == '__main__':
    unittest.main()
