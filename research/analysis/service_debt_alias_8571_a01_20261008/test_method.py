"""Inline construction checks; the frozen formal fixture is not read here."""
from __future__ import annotations

import copy
import unittest

import audit
import candidate


BASE = "5215aab506f43c8a02470d495b7352b1326a9580"


def _partitions(items):
    result = []
    def add(index, blocks):
        if index == len(items):
            result.append([list(block) for block in blocks])
            return
        for block in blocks:
            block.append(items[index])
            add(index + 1, blocks)
            block.pop()
        blocks.append([items[index]])
        add(index + 1, blocks)
        blocks.pop()
    add(0, [])
    return result


def _request(request_id, caller, ordinal, *, service=1, joint=True, revoked=None):
    return {
        "id": request_id, "caller_id": caller, "arrival": 0,
        "ordinal": ordinal, "service": service, "deadline": 20,
        "authority_current": True, "fresh": True, "joint_grant": joint,
        "conflict_free": True, "revoked_at": revoked,
    }


def construction_fixture():
    base_requests = []
    truth = {}
    for index in range(4):
        a_id, b_id = f"A{index}", f"B{index}"
        base_requests.extend((_request(a_id, "A", index * 2),
                              _request(b_id, "B", index * 2 + 1)))
        truth[a_id] = {"principal": "A", "verified_useful": index != 2}
        truth[b_id] = {"principal": "B", "verified_useful": index != 1}

    partitions = []
    for index, blocks in enumerate(_partitions(list(range(4))), 1):
        suffix = ["k1", "k2a", "k2b", "k2c", "k2d", "k2e", "k2f", "k2g",
                  "k3a", "k3b", "k3c", "k3d", "k3e", "k3f", "k4"][index - 1]
        partitions.append({"id": f"alias_p{index:02d}_{suffix}", "blocks": blocks})

    revoked_requests = [_request("C_RA", "CRA", 0, revoked=0)] + [
        _request(f"C_RB{index}", "CRB", index + 1) for index in range(4)
    ]
    truth["C_RA"] = {"principal": "A", "verified_useful": True}
    for index in range(4):
        truth[f"C_RB{index}"] = {"principal": "B", "verified_useful": True}

    false_requests = [
        _request("C_FA", "CFA", 0), _request("C_FB", "CFB", 1),
        _request("C_FA2", "CFA2", 2), _request("C_FB2", "CFB", 3),
    ]
    truth.update({
        "C_FA": {"principal": "A", "verified_useful": True},
        "C_FA2": {"principal": "A", "verified_useful": True},
        "C_FB": {"principal": "B", "verified_useful": True},
        "C_FB2": {"principal": "B", "verified_useful": True},
    })

    release_requests = [
        _request("C_MA0", "CMA", 0), _request("C_MB0", "CMB", 1),
        _request("C_MA1", "CMA", 2), _request("C_MB1", "CMB", 3),
    ]
    for request in release_requests:
        truth[request["id"]] = {"principal": "A" if request["caller_id"] == "CMA" else "B",
                                "verified_useful": True}

    return ({
        "schema": "service-debt-alias-trace-fixture-v1",
        "allocation_id": "SERVICE-DEBT-ALIAS-CONSTRUCTION",
        "base_revision": BASE,
        "horizon": 4,
        "policies": list(candidate.POLICIES),
        "base_requests": base_requests,
        "alias_partitions": partitions,
        "extra_cases": [
            {"id":"revoked_principal","requests":revoked_requests,
             "trusted_parents":{"CRA":"A","CRB":"B"},"parent_claims":{},"release_times":[]},
            {"id":"false_parent_claim","requests":false_requests,
             "trusted_parents":{"CFA":"A","CFA2":"A","CFB":"B"},
             "parent_claims":{"CFA":"B"},"release_times":[]},
            {"id":"mandatory_release","requests":release_requests,
             "trusted_parents":{"CMA":"A","CMB":"B"},"parent_claims":{},"release_times":[2]},
        ],
    }, {"schema":"service-debt-alias-outcome-oracle-v1","request_truth":truth})


class ServiceDebtAliasConstructionTests(unittest.TestCase):
    def test_enumeration_contains_every_partition_of_four_requests(self):
        blocks = _partitions(list(range(4)))
        canonical = {tuple(sorted(tuple(sorted(block)) for block in item)) for item in blocks}
        self.assertEqual(len(blocks), 15)
        self.assertEqual(len(canonical), 15)

    def test_alias_labels_change_presented_debt_but_parent_grouping_restores_baseline(self):
        fixture, _ = construction_fixture()
        rows = candidate.run(fixture)["rows"]
        by_key = {(row["case_id"], row["policy"]): row for row in rows}
        baseline = by_key[("alias_p01_k1", "presented_service_debt")]
        baseline_share = sum(item["service"] for item in baseline["attempts"]
                             if item["request_id"].startswith("A"))
        self.assertEqual(baseline_share, 2)
        observed_advantages = 0
        advantages = []
        for partition in fixture["alias_partitions"][1:]:
            caller_row = by_key[(partition["id"], "presented_service_debt")]
            caller_share = sum(item["service"] for item in caller_row["attempts"]
                               if item["request_id"].startswith("A"))
            if caller_share > baseline_share:
                advantages.append(partition["id"])
            observed_advantages += caller_share > baseline_share
            parent_row = by_key[(partition["id"], "trusted_parent_service_debt")]
            self.assertEqual([x["request_id"] for x in parent_row["attempts"]],
                             [x["request_id"] for x in by_key[("alias_p01_k1", "trusted_parent_service_debt")]["attempts"]])
        self.assertEqual(observed_advantages, len(advantages))

    def test_fragmentation_with_equal_total_service_does_not_change_cost_debt_share(self):
        base = {"id":"base","trusted_parents":{"A":"A","B":"B"},
                "parent_claims":{},"release_times":[],"requests":[
                    _request("BA0","A",0,service=2),_request("BB0","B",1,service=2),
                    _request("BA1","A",2,service=2),_request("BB1","B",3,service=2)]}
        split = {"id":"split","trusted_parents":{"A":"A","B":"B"},
                 "parent_claims":{},"release_times":[],"requests":[
                    _request("SA0a","A",0),_request("SB0","B",1,service=2),
                    _request("SA0b","A",2),_request("SB1","B",3,service=2),
                    _request("SA1a","A",4),_request("SA1b","A",5)]}
        base_row = candidate.simulate(base, "trusted_parent_service_debt", 4)
        split_row = candidate.simulate(split, "trusted_parent_service_debt", 4)
        units = lambda row: {
            principal: sum(item["service"] for item in row["attempts"]
                           if item["caller_id"] == principal)
            for principal in ("A", "B")
        }
        self.assertEqual(units(base_row), {"A":2,"B":2})
        self.assertEqual(units(split_row), units(base_row))

    def test_hard_gates_and_independent_auditor_mutation_controls(self):
        fixture, oracle = construction_fixture()
        raw = candidate.run(fixture)
        result = audit.audit(fixture, oracle, raw)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["disposition"], "PASS_METHOD_SCOPED")

        denied_id = next(row for row in raw["rows"] if row["case_id"] == "revoked_principal"
                         and row["policy"] == "trusted_parent_service_debt")
        self.assertIn("C_RA", {item["request_id"] for item in denied_id["excluded"]})
        revoked_metrics = result["metrics"]["revoked_principal|trusted_parent_service_debt"]["service_units"]
        self.assertEqual(revoked_metrics.get("A", 0), 0)
        self.assertEqual(revoked_metrics["B"], 4)
        mutations = []

        changed = copy.deepcopy(raw)
        target = next(row for row in changed["rows"] if row["case_id"] == "revoked_principal"
                      and row["policy"] == "trusted_parent_service_debt")
        target["attempts"][0]["request_id"] = "C_RA"
        mutations.append(changed)

        changed = copy.deepcopy(raw)
        target = next(row for row in changed["rows"] if row["case_id"] == "mandatory_release"
                      and row["policy"] == "trusted_parent_service_debt")
        target["release_events"] = []
        mutations.append(changed)

        changed = copy.deepcopy(raw)
        target = next(row for row in changed["rows"] if row["case_id"] == "false_parent_claim"
                      and row["policy"] == "trusted_parent_service_debt")
        target["parent_claims"][0]["decision"] = "ACCEPTED"
        mutations.append(changed)

        changed = copy.deepcopy(raw)
        changed["rows"][0]["attempts"][0]["verified_useful"] = True
        mutations.append(changed)

        changed = copy.deepcopy(raw)
        changed["rows"][0]["attempts"][0]["end"] += 1
        mutations.append(changed)

        for corrupted in mutations:
            with self.subTest(mutation=len([x for x in mutations if x is corrupted])):
                self.assertTrue(audit.audit(fixture, oracle, corrupted)["errors"])


if __name__ == "__main__":
    unittest.main()

