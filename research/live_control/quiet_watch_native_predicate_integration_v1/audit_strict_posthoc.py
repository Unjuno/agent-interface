#!/usr/bin/env python3
"""Posthoc tamper-evidence audit for the retained live integration allocation.

This does not replace or retroactively freeze the preregistered audit. It pins the
first raw result bytes observed immediately after the one formal run, verifies the
lossless zlib copy, then invokes the frozen independent semantic/safety/cost audit.
"""
import argparse
import hashlib
import importlib.util
import json
import zlib
from pathlib import Path

RAW_SHA256 = '07533a59ab969f3cbde6bb40a4f244d2146d79698c3af179424de3e6b87a0599'
RAW_ZLIB_SHA256 = 'cfcb335fd4a482ae6be31e6bcbe462cc6fc24f45b53b1415d468a24a70316868'
PREREG_SHA256 = '99c777e7bcda8b13a7b0ebf98e3a3accba53eb3872395b2746da5a78cae9d6e9'
FROZEN_AUDIT_RESULT_SHA256 = '656e27a49347b7fd1707229460590ffe81eb46ab96de2ecd25a0422539932d07'
FROZEN_AUDIT_SOURCE_SHA256 = 'b93a912818de0496564cb23189d73930cf1fcfcb1439afb841c5dd99fabdce5d'


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location('frozen_integration_audit', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', required=True)
    ap.add_argument('--zlib', required=True)
    ap.add_argument('--prereg', required=True)
    ap.add_argument('--audit-source', required=True)
    ap.add_argument('--frozen-audit-result', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    raw_path = Path(args.raw); z_path = Path(args.zlib); prereg_path = Path(args.prereg)
    audit_source = Path(args.audit_source); frozen_result_path = Path(args.frozen_audit_result)
    raw_b = raw_path.read_bytes(); z_b = z_path.read_bytes(); prereg_b = prereg_path.read_bytes()
    audit_b = audit_source.read_bytes(); frozen_b = frozen_result_path.read_bytes()

    checks = {
        'raw_sha256': sha256(raw_b) == RAW_SHA256,
        'raw_zlib_sha256': sha256(z_b) == RAW_ZLIB_SHA256,
        'zlib_decodes_exact_raw': False,
        'prereg_sha256': sha256(prereg_b) == PREREG_SHA256,
        'frozen_audit_source_sha256': sha256(audit_b) == FROZEN_AUDIT_SOURCE_SHA256,
        'frozen_audit_result_sha256': sha256(frozen_b) == FROZEN_AUDIT_RESULT_SHA256,
    }
    try:
        checks['zlib_decodes_exact_raw'] = zlib.decompress(z_b) == raw_b
    except Exception:
        checks['zlib_decodes_exact_raw'] = False

    rederived = None
    frozen = None
    if all(checks.values()):
        mod = load_module(audit_source)
        rederived = mod.audit(str(raw_path), str(prereg_path))
        frozen = json.loads(frozen_b)
        checks['rederived_audit_pass'] = bool(rederived.get('pass'))
        checks['rederived_decision_matches_frozen'] = rederived.get('decision') == frozen.get('decision')
        checks['rederived_summary_matches_frozen'] = rederived.get('summary') == frozen.get('summary')
        checks['rederived_checks_match_frozen'] = rederived.get('checks') == frozen.get('checks')
    else:
        checks.update({
            'rederived_audit_pass': False,
            'rederived_decision_matches_frozen': False,
            'rederived_summary_matches_frozen': False,
            'rederived_checks_match_frozen': False,
        })

    result = {
        'schema': 'quiet_watch_native_predicate_integration_v1_strict_posthoc_audit',
        'posthoc': True,
        'pins': {
            'raw_sha256': RAW_SHA256,
            'raw_zlib_sha256': RAW_ZLIB_SHA256,
            'prereg_sha256': PREREG_SHA256,
            'frozen_audit_source_sha256': FROZEN_AUDIT_SOURCE_SHA256,
            'frozen_audit_result_sha256': FROZEN_AUDIT_RESULT_SHA256,
        },
        'checks': checks,
        'pass': all(checks.values()),
        'decision': rederived.get('decision') if rederived else None,
    }
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result['pass']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
