import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from candidate import run_fixture
from history_candidate import IncompleteHistory, build_runs_url, collect_pages


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((HERE / "fixtures/full-history.json").read_text(encoding="utf-8"))

    def test_cross_event_historical_owner_denies_current_dispatch(self):
        result = run_fixture(self.fixture)
        self.assertEqual(result["owner"]["result_class"], "FAIL_ALLOCATION_ALREADY_OWNED")
        self.assertEqual(result["owner"]["owner_run_id"], 91001)
        self.assertFalse(result["event_filter_present"])

    def test_url_has_no_event_filter_and_has_page(self):
        url = build_runs_url("https://api.github.com", "Unjuno/agent-interface", "live-04.yml", page=2)
        self.assertIn("per_page=100", url)
        self.assertIn("page=2", url)
        self.assertNotIn("event=", url)

    def test_empty_history(self):
        self.assertEqual(collect_pages([{"total_count": 0, "workflow_runs": []}], max_pages=1, page_size=2)["workflow_runs"], [])

    def test_duplicate_id_fails_closed(self):
        pages = [{"total_count": 3, "workflow_runs": [{"id": 1}, {"id": 2}]}, {"total_count": 3, "workflow_runs": [{"id": 2}]}]
        with self.assertRaises(IncompleteHistory): collect_pages(pages, max_pages=2, page_size=2)

    def test_short_page_fails_closed(self):
        pages = [{"total_count": 3, "workflow_runs": [{"id": 1}]}]
        with self.assertRaises(IncompleteHistory): collect_pages(pages, max_pages=2, page_size=2)

    def test_total_change_fails_closed(self):
        pages = [{"total_count": 3, "workflow_runs": [{"id": 1}, {"id": 2}]}, {"total_count": 4, "workflow_runs": [{"id": 3}, {"id": 4}]}]
        with self.assertRaises(IncompleteHistory): collect_pages(pages, max_pages=2, page_size=2)

    def test_page_cap_fails_closed(self):
        pages = [{"total_count": 5, "workflow_runs": [{"id": 1}, {"id": 2}]}, {"total_count": 5, "workflow_runs": [{"id": 3}, {"id": 4}]}]
        with self.assertRaises(IncompleteHistory): collect_pages(pages, max_pages=2, page_size=2)


if __name__ == "__main__":
    unittest.main()
