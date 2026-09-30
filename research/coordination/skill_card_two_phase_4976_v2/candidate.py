from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class BoundaryError(ValueError):
    pass


@dataclass
class Session:
    session_id: str
    case_id: str
    context: dict[str, Any]
    loader: Any
    candidates: dict[str, dict[str, Any]] = field(default_factory=dict)
    trace: list[dict[str, Any]] = field(default_factory=list)
    selected_key: str | None = None
    selected_status: str | None = None
    revalidation_receipt: dict[str, Any] | None = None
    detail: dict[str, Any] | None = None

    def record(self, event_type: str, **fields: Any) -> dict[str, Any]:
        event = {"seq": len(self.trace) + 1, "type": event_type,
                 "session_id": self.session_id, "case_id": self.case_id, **fields}
        self.trace.append(event)
        return event


def present_candidates(case: dict[str, Any], model: Any, session_id: str) -> Session:
    """Filter and expose one bounded candidate; never load its implementation detail."""
    if not session_id or case.get("case_id") != case.get("context", {}).get("case_id"):
        raise BoundaryError("invalid_session_or_case")
    session = Session(session_id, case["case_id"], case["context"], model.DetailLoader())
    order = sorted(case["scores"], key=lambda key: (-case["scores"][key], key))
    filter_log = []
    for key in order:
        skill = model.REGISTRY[key]
        applicable, reason, status = model.hard_check(skill, case["context"])
        filter_log.append({"key": key, "applicable": applicable, "reason": reason, "status": status})
        if applicable:
            session.candidates[key] = {
                "candidate_key": key,
                "card": skill.card(),
                "status": status,
                "reason": reason,
            }
            break
    session.record("PRESENT_CANDIDATES", semantic_order=order, filter_log=filter_log,
                   candidate_keys=list(session.candidates), detail_loaded=list(session.loader.loaded))
    return session


def select_candidate(session: Session, event: dict[str, Any]) -> str:
    if not isinstance(event, dict) or event.get("type") != "SELECT_CANDIDATE":
        raise BoundaryError("explicit_selection_event_required")
    if event.get("session_id") != session.session_id or event.get("case_id") != session.case_id:
        raise BoundaryError("selection_scope_mismatch")
    key = event.get("candidate_key")
    if key not in session.candidates:
        raise BoundaryError("candidate_not_presented")
    if session.selected_key is not None:
        raise BoundaryError("selection_already_recorded")
    session.selected_key = key
    session.selected_status = session.candidates[key]["status"]
    session.record("SELECT_CANDIDATE", candidate_key=key)
    return session.selected_status


def revalidate_current(session: Session, event: dict[str, Any], model: Any) -> dict[str, Any]:
    if not isinstance(event, dict) or event.get("type") != "REVALIDATE_CURRENT":
        raise BoundaryError("explicit_revalidation_event_required")
    if event.get("session_id") != session.session_id or event.get("case_id") != session.case_id:
        raise BoundaryError("revalidation_scope_mismatch")
    if session.selected_key is None or session.selected_status != "REVALIDATION_REQUIRED":
        raise BoundaryError("selected_hint_required")
    if not session.context.get("current_revalidation_available", False):
        raise BoundaryError("current_revalidation_unavailable")
    skill = model.REGISTRY[session.selected_key]
    if skill.evidence_role != "HINT" or not skill.requires_revalidation:
        raise BoundaryError("source_not_revalidation_hint")
    # The source function is called only after explicit caller revalidation and
    # explicit checks above; the original #759 HINT record remains immutable.
    base = model.explicit_revalidate(session.selected_key, session.context)
    receipt = {
        **base,
        "candidate_key": session.selected_key,
        "case_id": session.case_id,
        "session_id": session.session_id,
        "event_seq": len(session.trace) + 1,
    }
    session.record("REVALIDATE_CURRENT", candidate_key=session.selected_key,
                   receipt_id=receipt["receipt_id"])
    session.revalidation_receipt = receipt
    return receipt


def load_selected_detail(session: Session, event: dict[str, Any], model: Any,
                         receipt: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(event, dict) or event.get("type") != "LOAD_SELECTED_DETAIL":
        raise BoundaryError("explicit_detail_load_event_required")
    if event.get("session_id") != session.session_id or event.get("case_id") != session.case_id:
        raise BoundaryError("detail_load_scope_mismatch")
    if session.selected_key is None or session.selected_status is None:
        raise BoundaryError("explicit_selection_required")
    if session.detail is not None:
        raise BoundaryError("detail_already_loaded")
    skill = model.REGISTRY[session.selected_key]
    if skill.evidence_role == "HINT":
        expected = session.revalidation_receipt
        if session.selected_status != "REVALIDATION_REQUIRED" or not isinstance(receipt, dict) or expected is None:
            raise BoundaryError("current_revalidation_receipt_required")
        exact = (
            receipt == expected
            and receipt.get("candidate_key") == session.selected_key
            and receipt.get("case_id") == session.case_id
            and receipt.get("session_id") == session.session_id
            and receipt.get("source_role") == "HINT"
            and receipt.get("output_role") == "ADMISSION_DEPENDENCY"
            and receipt.get("freshness") == "CURRENT"
            and receipt.get("source_skill_version") == skill.version
            and receipt.get("source_provenance") == skill.provenance
        )
        if not exact:
            raise BoundaryError("revalidation_receipt_mismatch")
        final_status = "EXECUTABLE_AFTER_REVALIDATION"
    else:
        if receipt is not None:
            raise BoundaryError("unexpected_revalidation_receipt")
        final_status = session.selected_status
    session.record("LOAD_SELECTED_DETAIL", candidate_key=session.selected_key)
    session.detail = session.loader.load(session.selected_key)
    return {"status": final_status, "detail": session.detail,
            "detail_loaded": list(session.loader.loaded), "trace": list(session.trace)}
