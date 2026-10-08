"""Ordinary ownership primitive checks, excluded from the formal OS matrix."""
import threading
import unittest
from ownership import OnceOwner


class OwnershipConstruction(unittest.TestCase):
    def test_single_consumption_does_not_rebind_same_number(self):
        owner = OnceOwner(17)
        self.assertEqual(owner.take_for_close(), 17)
        self.assertIsNone(owner.take_for_close())
        replacement = OnceOwner(17)
        self.assertIsNone(owner.take_for_close())
        self.assertEqual(replacement.take_for_close(), 17)

    def test_concurrent_claims_have_exactly_one_owner(self):
        owner = OnceOwner(19)
        barrier = threading.Barrier(8)
        values = []
        lock = threading.Lock()
        def claim():
            barrier.wait(timeout=2)
            value = owner.take_for_close()
            with lock:
                values.append(value)
        workers = [threading.Thread(target=claim) for _ in range(8)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(2)
        self.assertFalse(any(worker.is_alive() for worker in workers))
        self.assertEqual(values.count(19), 1)
        self.assertEqual(values.count(None), 7)


if __name__ == '__main__':
    unittest.main()
