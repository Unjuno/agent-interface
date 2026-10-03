import unittest

from audit import recorded_health_transitions
from experiment import PSMS, SCALES, exact_counts, normalize_digits, selected_health_transitions


def typed(sequence, health):
    return {
        "event": "typed_observation",
        "sequence": sequence,
        "signals": {"health": {"value": health}},
    }


class HealthTransitionTests(unittest.TestCase):
    def test_selects_only_health_changes(self):
        rows = [typed(1, 97), typed(2, 97), typed(3, 91), typed(4, 91), typed(5, 85)]
        self.assertEqual([row["sequence"] for row in selected_health_transitions(rows)], [3, 5])
        self.assertEqual(
            [(row["sequence"], row["signals"]["health"]["value"]) for row in recorded_health_transitions(rows)],
            [(3, 91), (5, 85)],
        )

    def test_empty_and_initial_only_have_no_transition(self):
        self.assertEqual(selected_health_transitions([]), [])
        self.assertEqual(selected_health_transitions([typed(1, 97)]), [])


class OCRNormalizationTests(unittest.TestCase):
    def test_only_ascii_digits_are_compared(self):
        self.assertEqual(normalize_digits(" 7 2%\n"), "72")
        self.assertEqual(normalize_digits(""), "")

    def test_exact_counts_are_per_fixed_configuration(self):
        empty_matrix = {
            f"{scale}/psm{psm}": {"normalized_digits": ""}
            for scale in SCALES
            for psm in PSMS
        }
        first_matrix = {key: value.copy() for key, value in empty_matrix.items()}
        first_matrix["gray/psm7"]["normalized_digits"] = "72"
        rows = [
            {"typed_health": 72, "ocr": first_matrix},
            {"typed_health": 65, "ocr": empty_matrix},
        ]
        counts = exact_counts(rows)
        self.assertEqual(counts["gray/psm7"], {"exact_matches": 1, "n": 2})
        self.assertEqual(counts["threshold_150/psm8"], {"exact_matches": 0, "n": 2})


if __name__ == "__main__":
    unittest.main()
