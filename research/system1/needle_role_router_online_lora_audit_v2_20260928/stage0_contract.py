"""Independent zero-fit raw-contract mutation checks for Issue #5172.

This module deliberately does not import the predecessor runner/auditor. It tests
the evidence contract on tiny synthetic JSON fixtures and never trains a model.
"""
import hashlib
import json
import unittest

ALLOCATION = "needle-role-router-online-lora-audit-v2-20260928"
SEEDS = (8100203, 8100307, 8100419)  # fixture labels only; not formal seeds
ARMS = ("SHARED_B_ONLY", "SHARED_A_REPLAY",
        "ROUTED_SHARED_ADAPTER", "ROUTED_SEPARATE_SKILLS")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def schedule_for(seed, arm):
    # Deterministic fixture-only index list, intentionally not a training schedule.
    return [((seed % 97) + i * (ARMS.index(arm) + 1)) % 257 for i in range(16)]


def make_fixture(seed, arm):
    indices = schedule_for(seed, arm)
    digests = {
        "base_row_indices": sha(canonical(indices)),
        "support_rows": sha(canonical({"seed": seed, "arm": arm, "kind": "support"})),
    }
    return {
        "schema": "role-skill-stage0-fixture-v1",
        "allocation": ALLOCATION,
        "seed": seed,
        "arm": arm,
        "source_sha256": "a" * 64,
        "base_row_indices": indices,
        "dataset_sha256": digests,
    }


def parse_no_duplicates(raw):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError("duplicate_json_key")
            obj[key] = value
        return obj
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(
                          ValueError("non_finite_json_number")))


def audit_raw(raw):
    try:
        obj = parse_no_duplicates(raw)
        if set(obj) != {"schema", "allocation", "seed", "arm",
                        "source_sha256", "base_row_indices", "dataset_sha256"}:
            return False, "schema_or_extra_field"
        seed, arm = obj["seed"], obj["arm"]
        if isinstance(seed, bool) or seed not in SEEDS or arm not in ARMS:
            return False, "identity"
        if obj["schema"] != "role-skill-stage0-fixture-v1" or obj["allocation"] != ALLOCATION:
            return False, "identity"
        if obj["source_sha256"] != "a" * 64:
            return False, "source_identity"
        expected_indices = schedule_for(seed, arm)
        indices = obj["base_row_indices"]
        if indices != expected_indices:
            return False, "schedule"
        expected_keys = {"base_row_indices", "support_rows"}
        if set(obj["dataset_sha256"]) != expected_keys:
            return False, "digest_key_set"
        # Independently recanonicalize observed schedule and fixture inputs.
        if obj["dataset_sha256"]["base_row_indices"] != sha(canonical(indices)):
            return False, "schedule_digest"
        support = {"seed": seed, "arm": arm, "kind": "support"}
        if obj["dataset_sha256"]["support_rows"] != sha(canonical(support)):
            return False, "support_digest"
        return True, "ACCEPT"
    except (ValueError, TypeError, KeyError, AttributeError):
        return False, "malformed"


def raw(obj):
    return canonical(obj)


class RawContractMutationTests(unittest.TestCase):
    def test_valid_grid_accepts_all_12_seed_arm_fixtures(self):
        for seed in SEEDS:
            for arm in ARMS:
                with self.subTest(seed=seed, arm=arm):
                    self.assertEqual(audit_raw(raw(make_fixture(seed, arm))),
                                     (True, "ACCEPT"))

    def test_missing_schedule_and_missing_digest_reject(self):
        for key in ("base_row_indices",):
            obj = make_fixture(SEEDS[0], ARMS[0])
            del obj[key]
            self.assertFalse(audit_raw(raw(obj))[0])
        obj = make_fixture(SEEDS[0], ARMS[0])
        del obj["dataset_sha256"]["base_row_indices"]
        self.assertFalse(audit_raw(raw(obj))[0])

    def test_extra_digest_key_rejects(self):
        obj = make_fixture(SEEDS[0], ARMS[0])
        obj["dataset_sha256"]["unexpected"] = "0" * 64
        self.assertFalse(audit_raw(raw(obj))[0])

    def test_reorder_duplicate_and_index_mutation_reject(self):
        for mutate in (
            lambda xs: list(reversed(xs)),
            lambda xs: xs.__setitem__(1, xs[0]),
            lambda xs: xs.__setitem__(0, (xs[0] + 1) % 257),
        ):
            obj = make_fixture(SEEDS[0], ARMS[0])
            mutate(obj["base_row_indices"])
            self.assertFalse(audit_raw(raw(obj))[0])

    def test_digest_mutation_rejects(self):
        obj = make_fixture(SEEDS[0], ARMS[0])
        obj["dataset_sha256"]["base_row_indices"] = "0" * 64
        self.assertFalse(audit_raw(raw(obj))[0])

    def test_duplicate_keys_and_nonfinite_numbers_reject(self):
        valid = raw(make_fixture(SEEDS[0], ARMS[0])).decode()
        self.assertFalse(audit_raw(valid.replace('"seed":', '"seed":1,"seed":', 1))[0])
        self.assertFalse(audit_raw(valid.replace('"seed":8100203', '"seed":NaN', 1))[0])

    def test_wrong_identity_schema_and_bool_seed_reject(self):
        for key, value in (("allocation", "wrong"), ("arm", "UNKNOWN"),
                           ("seed", True), ("schema", "wrong"),
                           ("source_sha256", "b" * 64)):
            obj = make_fixture(SEEDS[0], ARMS[0])
            obj[key] = value
            self.assertFalse(audit_raw(raw(obj))[0], key)

    def test_no_training_code_or_optimizer_entrypoint_exists(self):
        # This fixture-only checker has no torch import, runner, optimizer, or fit API.
        forbidden = ("torch", "run_seed", "optimizer", "fit_model")
        import pathlib
        source = pathlib.Path(__file__).read_text(encoding="utf-8")
        for token in forbidden:
            self.assertNotIn(token, source.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
