"""Dependency-scoped scheduling advice. This module grants no input authority."""
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Effects:
    reads: frozenset[str] | None
    writes: frozenset[str] | None

    def __post_init__(self):
        for names in (self.reads, self.writes):
            if names is not None and (not isinstance(names, frozenset) or
                    any(not isinstance(x, str) or not x for x in names)):
                raise ValueError('effects must be frozensets of nonempty names, or unknown')


class Frontier:
    def __init__(self, epoch: str, catalogue_version: int, aliases: Mapping[str, str]):
        if not isinstance(epoch, str) or not epoch:
            raise ValueError('nonempty epoch required')
        if type(catalogue_version) is not int or catalogue_version < 0:
            raise ValueError('nonnegative catalogue version required')
        if any(not isinstance(x, str) or not x for pair in aliases.items() for x in pair):
            raise ValueError('canonical identities must be nonempty strings')
        self.epoch, self.version, self.aliases = epoch, catalogue_version, dict(aliases)

    def _resolve(self, names, raw_names):
        if names is None:
            raise ValueError('unknown footprint')
        if raw_names:
            return names
        try:
            return frozenset(self.aliases[x] for x in names)
        except KeyError as exc:
            raise ValueError('unresolved resource identity') from exc

    def advise(self, candidate: Effects, pending: Mapping[str, Effects], *,
               epoch: str, catalogue_version: int, physical_empty: bool,
               raw_names: bool = False) -> dict:
        reason = 'INDEPENDENT'
        if epoch != self.epoch or type(catalogue_version) is not int or catalogue_version != self.version:
            reason = 'CONTEXT_CHANGED'
        elif physical_empty is not True:
            reason = 'INPUT_NOT_RELEASED'
        elif pending:
            try:
                cr, cw = self._resolve(candidate.reads, raw_names), self._resolve(candidate.writes, raw_names)
                for other in pending.values():
                    pr, pw = self._resolve(other.reads, raw_names), self._resolve(other.writes, raw_names)
                    if (pw & (cr | cw)) or (cw & (pr | pw)):
                        reason = 'DEPENDENT'
                        break
            except ValueError:
                reason = 'UNKNOWN_FOOTPRINT'
        else:
            reason = 'NO_PENDING_EFFECT'
        return {'eligible': reason in ('INDEPENDENT', 'NO_PENDING_EFFECT'),
                'reason': reason, 'grants_input_authority': False}


def matching_commit(row: dict, *, epoch: str, operation: str, payload_hash: str,
                    issued_ns: int, observed_ns: int) -> bool:
    """Validate a trusted application commit receipt, never infer from absence."""
    return bool(
        isinstance(row, dict) and row.get('epoch') == epoch and
        row.get('operation') == operation and row.get('payload_sha256') == payload_hash and
        row.get('kind') in ('ack', 'lookup') and row.get('status') == 'COMMITTED' and
        type(row.get('durable_ns')) is int and type(row.get('published_ns')) is int and
        issued_ns <= row['durable_ns'] <= row['published_ns'] <= observed_ns and
        type(row.get('effect_rowid')) is int and row['effect_rowid'] > 0
    )
