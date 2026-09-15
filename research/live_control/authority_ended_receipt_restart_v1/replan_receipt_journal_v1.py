from __future__ import annotations
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys

UPSTREAM = Path(__file__).resolve().parent / 'upstream'
if str(UPSTREAM) not in sys.path:
    sys.path.insert(0, str(UPSTREAM))
from authority_ended_bridge_v1 import to_caller_execution_decision
from replan_receipt_ledger_v1 import ReplanToken, DuplicateAuthorityEndedReceipt, InvalidAuthorityEndIdentity

class ReceiptJournalCorrupt(ValueError):
    pass

@dataclass
class JournalBackedReplanReceiptLedger:
    journal_path: Path

    def __post_init__(self):
        self.journal_path = Path(self.journal_path)
        self.issued_ids = self._load()

    def _load(self) -> set[str]:
        if not self.journal_path.exists():
            return set()
        data = self.journal_path.read_text(encoding='utf-8')
        issued: set[str] = set()
        if not data:
            return issued
        lines = data.splitlines()
        if not data.endswith('\n'):
            raise ReceiptJournalCorrupt('journal missing terminal newline')
        for lineno, line in enumerate(lines, 1):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise ReceiptJournalCorrupt(f'invalid json at line {lineno}') from e
            if type(rec) is not dict or set(rec) != {'authority_end_id'}:
                raise ReceiptJournalCorrupt(f'invalid record shape at line {lineno}')
            rid = rec['authority_end_id']
            if type(rid) is not str or not rid:
                raise ReceiptJournalCorrupt(f'invalid authority_end_id at line {lineno}')
            if rid in issued:
                raise ReceiptJournalCorrupt(f'duplicate authority_end_id in journal at line {lineno}')
            issued.add(rid)
        return issued

    def _persist(self, rid: str) -> None:
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({'authority_end_id': rid}, separators=(',', ':'), sort_keys=True) + '\n'
        with self.journal_path.open('a', encoding='utf-8') as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())

    def issue(self, receipt):
        decision = to_caller_execution_decision(receipt)
        if decision != {'status':'safe_yield','reason':'authority_unavailable','completed_actions':receipt['steps_completed']}:
            raise ValueError('unexpected bridge decision')
        rid = receipt.get('authority_end_id')
        if type(rid) is not str or not rid:
            raise InvalidAuthorityEndIdentity('runtime authority_end_id required')
        if rid in self.issued_ids:
            raise DuplicateAuthorityEndedReceipt('authority_end_id already issued')
        self._persist(rid)
        self.issued_ids.add(rid)
        return ReplanToken(authority_end_id=rid, post_sequence=receipt['post_authority']['sequence'])
