"""Join independent expiry sampling and pending resolver evidence safely.

The sampler observes key state around the serialized lease deadline. The
resolver samples key state while polling one public call. These sources have
different timing and custody meaning and must never be conflated.
"""
from __future__ import annotations

import json
from pathlib import Path


def join_w_input_samples(resolver_report, expiry_report):
    """Return a provenance-labeled view without promoting missing data.

    If resolver samples exist, they remain authoritative for resolver-specific
    fields. Expiry samples are exposed separately and are never synthesized
    into resolver rows. Missing either report is represented explicitly.
    """
    resolver = resolver_report if type(resolver_report) is dict else None
    expiry = expiry_report if type(expiry_report) is dict else None
    resolver_samples = resolver.get("samples") if resolver else None
    expiry_samples = expiry.get("samples") if expiry else None
    if type(resolver_samples) is not list:
        resolver_samples = None
    if type(expiry_samples) is not list:
        expiry_samples = None
    return {
        "resolver": {
            "present": resolver is not None,
            "samples": resolver_samples,
            "sample_count": len(resolver_samples) if resolver_samples is not None else None,
            "observed_w_down_before_terminal": (
                resolver.get("observed_w_down_before_terminal") if resolver else None
            ),
            "terminal_w_down": resolver.get("terminal_w_down") if resolver else None,
            "claim": resolver.get("claim") if resolver else None,
        },
        "expiry_sampler": {
            "present": expiry is not None,
            "samples": expiry_samples,
            "sample_count": len(expiry_samples) if expiry_samples is not None else None,
            "boundary_status": expiry.get("status") if expiry else None,
            "lease_deadline_ns": expiry.get("lease_deadline_ns") if expiry else None,
        },
        "classification": (
            "BOTH_PRESENT" if resolver is not None and expiry is not None
            else "BOTH_MISSING" if resolver is None and expiry is None
            else "RESOLVER_MISSING" if resolver is None
            else "EXPIRY_SAMPLER_MISSING" if expiry is None
            else "UNCLASSIFIED"
        ),
    }


def load_held_input_evidence(trial_directory):
    """Load resolver-held samples, with explicitly labeled expiry-only fallback.

    `expiry-boundary-key-samples.json` is not a resolver poll receipt. When it
    supplies fallback rows, each row is marked `not_sampled_by_resolver` and
    resolver-only terminal/down-before-terminal fields stay unknown. Missing
    or malformed files return a conservative empty/unknown view instead of
    raising a `FileNotFoundError` during terminal adjudication.
    """
    trial = Path(trial_directory)
    resolver_path = trial / "expiry-held-w-samples.json"
    expiry_path = trial / "expiry-boundary-key-samples.json"

    def read_report(path):
        if not path.is_file():
            return None, "missing"
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            return None, type(error).__name__
        if type(value) is not dict or type(value.get("samples")) is not list:
            return None, "invalid_schema"
        return value, None

    resolver, resolver_error = read_report(resolver_path)
    expiry, expiry_error = read_report(expiry_path)
    resolver_samples = resolver.get("samples") if resolver is not None else None
    expiry_samples = expiry.get("samples") if expiry is not None else None

    if resolver_error not in (None, "missing"):
        held = {
            "samples": [], "observed_w_down_before_terminal": None,
            "terminal_w_down": None, "status": "unknown",
            "claim": "invalid resolver artifact; no samples promoted",
        }
        source = "invalid-resolver-artifact"
        classification = "RESOLVER_ARTIFACT_INVALID"
    elif resolver_samples:
        held = resolver
        source = "pending-resolver-poll-samples"
        classification = "RESOLVER_SAMPLES_PRESENT"
    elif expiry_samples is not None:
        if any(type(row) is not dict or type(row.get("after_ns")) is not int
               or type(row.get("w_key_down")) is not bool for row in expiry_samples):
            held = {
                "samples": [], "observed_w_down_before_terminal": None,
                "terminal_w_down": None, "status": "unknown",
                "claim": "invalid expiry sampler rows; no resolver inference",
            }
            source = "invalid-expiry-sampler"
            classification = "EXPIRY_SAMPLER_INVALID"
        else:
            held = {
                "samples": [
                    {"observed_monotonic_ns": row["after_ns"],
                     "action_status": "not_sampled_by_resolver",
                     "w_key_down": row["w_key_down"]}
                    for row in expiry_samples
                ],
                "observed_w_down_before_terminal": None,
                "terminal_w_down": None,
                "status": "resolver_samples_missing" if resolver is None else "resolver_samples_empty",
                "claim": "independent expiry samples only; resolver status not inferred",
            }
            source = "independent-expiry-sampler"
            classification = (
                "MISSING_RESOLVER_SAMPLES" if resolver is None
                else "EMPTY_RESOLVER_SAMPLES"
            )
    else:
        held = resolver if resolver is not None else {
            "samples": [], "observed_w_down_before_terminal": None,
            "terminal_w_down": None, "status": "missing",
            "claim": "no resolver or expiry samples retained",
        }
        source = "pending-resolver-poll-samples" if resolver is not None else "missing"
        classification = (
            "RESOLVER_ARTIFACT_INVALID" if resolver_error not in (None, "missing")
            else "EXPIRY_SAMPLER_ARTIFACT_INVALID"
            if expiry_error not in (None, "missing")
            else "MISSING_RESOLVER_SAMPLES"
        )

    join = {
        "source": source,
        "classification": classification,
        "resolver_file_present": resolver_path.is_file(),
        "expiry_sampler_file_present": expiry_path.is_file(),
        "resolver_error": resolver_error,
        "expiry_sampler_error": expiry_error,
        "sample_count": len(held.get("samples", [])),
        "observed_w_down_before_terminal": held.get("observed_w_down_before_terminal"),
        "terminal_w_down": held.get("terminal_w_down"),
    }
    return held, join
