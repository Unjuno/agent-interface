"""Finite positive justification maintenance; no I/O or action capability.

This research module requires complete, unchanged rules and a deletion-only
change to evidence roots. Grounding means finite derivability from those
roots, not factual truth, source authenticity, or permission to act.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Graph:
    root_count: int
    node_count: int
    rules: tuple[tuple[int, frozenset[int]], ...]

    @classmethod
    def parse(cls, value: dict[str, Any]) -> Graph:
        if type(value) is not dict:
            raise ValueError('graph must be an object')
        b, n, rules = value.get('root_count'), value.get('node_count'), value.get('rules')
        if type(b) is not int or type(n) is not int or not 0 <= b < n <= 64:
            raise ValueError('require 0 <= root_count < node_count <= 64')
        if type(rules) is not list or len(rules) > 512:
            raise ValueError('rules must be a list of at most 512 entries')
        parsed = []
        for row in rules:
            if type(row) is not list or len(row) != 2:
                raise ValueError('rule must be [head, body]')
            h, body = row
            if type(h) is not int or not b <= h < n:
                raise ValueError('head must identify a derived claim')
            if type(body) is not list or not 1 <= len(body) <= 64:
                raise ValueError('body must be nonempty and bounded')
            if any(type(x) is not int or not 0 <= x < n for x in body):
                raise ValueError('invalid antecedent')
            if len(set(body)) != len(body):
                raise ValueError('repeated antecedent')
            parsed.append((h, frozenset(body)))
        if len(set(parsed)) != len(parsed):
            raise ValueError('duplicate rule')
        return cls(b, n, tuple(parsed))

    @property
    def claims(self) -> frozenset[int]:
        return frozenset(range(self.root_count, self.node_count))

    def roots(self, values: list[int]) -> frozenset[int]:
        if type(values) is not list or any(type(x) is not int or not 0 <= x < self.root_count for x in values):
            raise ValueError('invalid evidence roots')
        if len(set(values)) != len(values):
            raise ValueError('duplicate evidence root')
        return frozenset(values)


def derive(graph: Graph, seed: frozenset[int], eligible: frozenset[int]) -> tuple[frozenset[int], list[list[int]], int]:
    """Synchronous ascending closure. An empty final round is not recorded."""
    known, waves, checks = seed, [], 0
    while True:
        added: set[int] = set()
        for head, body in graph.rules:
            if head in eligible and head not in known:
                checks += 1
                if body <= known:
                    added.add(head)
        if not added:
            return known, waves, checks
        waves.append(sorted(added))
        known = known | added


def affected_cone(graph: Graph, removed: frozenset[int]) -> frozenset[int]:
    """Syntactic dependency reachability; conjunctive bodies add each edge."""
    reached = removed
    while True:
        following = reached | {h for h, body in graph.rules if body & reached}
        if following == reached:
            return reached & graph.claims
        reached = following


def local_prune(graph: Graph, old: frozenset[int], roots_after: frozenset[int]) -> frozenset[int]:
    """Comparator: remove claims lacking a currently satisfied justification.

    Self-supporting cycles can survive this descending computation.
    """
    known = (old & graph.claims) | roots_after
    while True:
        retained = roots_after | {h for h, body in graph.rules if h in known and body <= known}
        if retained == known:
            return known
        known = retained


def evaluate(case: dict[str, Any]) -> dict[str, Any]:
    graph = Graph.parse(case['graph'])
    before, after = graph.roots(case['before']), graph.roots(case['after'])
    if not after <= before:
        raise ValueError('only evidence deletion is supported')
    old, old_waves, _ = derive(graph, before, graph.claims)
    affected = affected_cone(graph, before - after)
    unaffected = (old & graph.claims) - affected
    candidate, waves, checks = derive(graph, after | unaffected, affected)
    full, _, full_checks = derive(graph, after, graph.claims)
    prune = local_prune(graph, old, after)
    return {
        'before_grounded': sorted(old & graph.claims),
        'affected': sorted(affected),
        'retained_outside': sorted(unaffected),
        'candidate': sorted(candidate & graph.claims),
        'full_rebuild': sorted(full & graph.claims),
        'local_prune': sorted(prune & graph.claims),
        'blind_drop': sorted(unaffected),
        'before_waves': old_waves,
        'rederivation_waves': waves,
        'candidate_rule_checks': checks,
        'full_rule_checks': full_checks,
        'action_authority': False,
        'task_success': None,
        'semantics': 'finite_positive_derivability_only',
    }
