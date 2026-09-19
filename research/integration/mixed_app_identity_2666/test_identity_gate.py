import unittest
from .identity_gate import EXPECTED_APPS, evaluate_identities

def row(n, app, display=":141"):
    return {"window_id": n, "pid": 1000+n, "display": display,
            "title": app + " window", "wm_class": app}

class IdentityGateTests(unittest.TestCase):
    def setUp(self):
        self.selected = {app: row(i+1, app) for i, app in enumerate(EXPECTED_APPS)}
        self.repeated = {app: dict(value) for app, value in self.selected.items()}

    def test_admits_stable_typed_same_display_identities(self):
        decision = evaluate_identities(self.selected, self.repeated, display=":141")
        self.assertEqual((decision.admitted, decision.reason), (True, "admitted"))

    def test_none_and_missing_are_rejected(self):
        selected = dict(self.selected); selected["inkscape"] = None
        self.assertEqual(evaluate_identities(selected, self.repeated, display=":141").reason, "identity")
        repeated = dict(self.repeated); del repeated["chromium"]
        self.assertEqual(evaluate_identities(self.selected, repeated, display=":141").reason, "app_set")

    def test_ambiguous_duplicate_and_wrong_display_are_rejected(self):
        ambiguous = dict(self.selected); ambiguous["chromium"] = [self.selected["chromium"]]
        self.assertEqual(evaluate_identities(ambiguous, self.repeated, display=":141").reason, "ambiguous")
        duplicate = dict(self.selected); duplicate["chromium"] = dict(duplicate["inkscape"])
        self.assertEqual(evaluate_identities(duplicate, self.repeated, display=":141").reason, "duplicate")
        wrong = dict(self.selected); wrong["calc"] = wrong.pop("libreoffice")
        self.assertEqual(evaluate_identities(wrong, self.repeated, display=":141").reason, "app_set")

    def test_unstable_or_wrong_display_or_bad_types_yield(self):
        unstable = dict(self.selected); unstable["inkscape"] = dict(unstable["inkscape"], window_id=99)
        self.assertEqual(evaluate_identities(unstable, self.repeated, display=":141").reason, "unstable")
        wrong = dict(self.selected); wrong["inkscape"] = dict(wrong["inkscape"], display=":140")
        self.assertEqual(evaluate_identities(wrong, self.repeated, display=":141").reason, "identity")
        bad = dict(self.selected); bad["inkscape"] = dict(bad["inkscape"], window_id=True)
        self.assertEqual(evaluate_identities(bad, self.repeated, display=":141").reason, "identity")

if __name__ == "__main__":
    unittest.main()
