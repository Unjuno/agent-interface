#!/usr/bin/env python3
"""Fail-closed model-boundary codecs for the portable runtime contract.

C0 is canonical minified JSON. C1 is a fixed textual grammar. C2 is a persistent
exact-workflow dictionary with an epoch + digest. All decode to the same v0 AST.
UTF-8 bytes/characters are serialization proxies, not provider token counts.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

from contract import ContractError, SCHEMA_PROGRAM, validate_program

SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class CodecError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def encode_c0(program: dict[str, Any]) -> str:
    validate_program(program)
    return canonical_json(program)


def decode_c0(payload: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise CodecError(f"invalid json: {error.msg}") from error
    try:
        return validate_program(value)
    except ContractError as error:
        raise CodecError(str(error)) from error


def _quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _unquote(value: str) -> str:
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as error:
        raise CodecError("invalid quoted string") from error
    if not isinstance(decoded, str):
        raise CodecError("quoted value must decode to string")
    return decoded


def _split_ops(payload: str) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    quoted = False
    escaped = False
    for ch in payload:
        if escaped:
            buf.append(ch)
            escaped = False
            continue
        if quoted and ch == "\\":
            buf.append(ch)
            escaped = True
            continue
        if ch == '"':
            quoted = not quoted
            buf.append(ch)
            continue
        if ch == ";" and not quoted:
            token = "".join(buf)
            if not token:
                raise CodecError("empty operation token")
            out.append(token)
            buf.clear()
        else:
            buf.append(ch)
    if quoted:
        raise CodecError("unterminated quoted string")
    token = "".join(buf)
    if token:
        out.append(token)
    elif payload:
        raise CodecError("trailing operation separator")
    return out


def _encode_op(op: dict[str, Any]) -> str:
    t = op["op"]
    if t == "focus":
        return "F:" + op["target"]
    if t == "key_chord":
        return "K:" + "+".join(op["keys"])
    if t == "key_state":
        return ("D:" if op["down"] else "U:") + op["key"]
    if t == "text":
        return "T:" + _quote(op["text"])
    if t == "pointer_move":
        return f"M:{op['frame']},{op['x']},{op['y']}"
    if t == "pointer_button":
        return ("B+:" if op["down"] else "B-:") + op["button"]
    if t == "scroll":
        return f"S:{op['dx']},{op['dy']}"
    if t == "observe":
        return f"O:{op['frame']},{op['x']},{op['y']},{op['w']},{op['h']}"
    if t == "wait_update":
        return f"W:{op['timeout_ms']}"
    if t == "verify":
        return "V:" + _quote(op["predicate"])
    if t == "release_all":
        return "R"
    raise CodecError(f"unsupported op {t}")


def _decode_op(token: str) -> dict[str, Any]:
    if token == "R":
        return {"op": "release_all"}
    if ":" not in token:
        raise CodecError("operation missing ':'")
    code, payload = token.split(":", 1)
    if code == "F":
        return {"op": "focus", "target": payload}
    if code == "K":
        keys = payload.split("+") if payload else []
        return {"op": "key_chord", "keys": keys}
    if code == "D":
        return {"op": "key_state", "key": payload, "down": True}
    if code == "U":
        return {"op": "key_state", "key": payload, "down": False}
    if code == "T":
        return {"op": "text", "text": _unquote(payload)}
    if code == "M":
        parts = payload.split(",")
        if len(parts) != 3:
            raise CodecError("pointer_move arity")
        frame, x, y = parts
        try:
            return {"op": "pointer_move", "frame": frame, "x": int(x), "y": int(y)}
        except ValueError as error:
            raise CodecError("pointer_move integer") from error
    if code in {"B+", "B-"}:
        return {"op": "pointer_button", "button": payload, "down": code == "B+"}
    if code == "S":
        parts = payload.split(",")
        if len(parts) != 2:
            raise CodecError("scroll arity")
        try:
            return {"op": "scroll", "dx": int(parts[0]), "dy": int(parts[1])}
        except ValueError as error:
            raise CodecError("scroll integer") from error
    if code == "O":
        parts = payload.split(",")
        if len(parts) != 5:
            raise CodecError("observe arity")
        frame, x, y, w, h = parts
        try:
            return {"op": "observe", "frame": frame, "x": int(x), "y": int(y),
                    "w": int(w), "h": int(h)}
        except ValueError as error:
            raise CodecError("observe integer") from error
    if code == "W":
        try:
            return {"op": "wait_update", "timeout_ms": int(payload)}
        except ValueError as error:
            raise CodecError("wait integer") from error
    if code == "V":
        return {"op": "verify", "predicate": _unquote(payload)}
    raise CodecError(f"unknown opcode {code}")


def encode_ops_c1(ops: list[dict[str, Any]]) -> str:
    return ";".join(_encode_op(op) for op in ops)


def decode_ops_c1(payload: str) -> list[dict[str, Any]]:
    return [_decode_op(token) for token in _split_ops(payload)]


def encode_c1(program: dict[str, Any]) -> str:
    validate_program(program)
    pid = program["program_id"]
    lease = program["authority"]["lease_id"]
    if not SAFE_ID.fullmatch(pid) or not SAFE_ID.fullmatch(lease):
        raise CodecError("C1 requires safe program/lease identifiers")
    src = program["source"]
    auth = program["authority"]
    header = (
        f"A0|{pid}|{src['observation_seq']}|{src['binding_revision']}|"
        f"{lease}|{auth['expires_at_ns']}|"
    )
    return header + encode_ops_c1(program["ops"])


def decode_c1(payload: str) -> dict[str, Any]:
    parts = payload.split("|", 6)
    if len(parts) != 7 or parts[0] != "A0":
        raise CodecError("invalid C1 header")
    _, pid, seq, revision, lease, expires, ops_payload = parts
    if not SAFE_ID.fullmatch(pid) or not SAFE_ID.fullmatch(lease):
        raise CodecError("invalid identifier")
    try:
        program = {
            "schema": SCHEMA_PROGRAM,
            "program_id": pid,
            "source": {"observation_seq": int(seq), "binding_revision": int(revision)},
            "authority": {"lease_id": lease, "expires_at_ns": int(expires)},
            "ops": decode_ops_c1(ops_payload),
            "terminal": {"release_all_required": True},
        }
    except ValueError as error:
        raise CodecError("invalid C1 integer") from error
    try:
        return validate_program(program)
    except ContractError as error:
        raise CodecError(str(error)) from error


@dataclass(frozen=True)
class WorkflowDictionary:
    epoch: int
    definitions: dict[str, list[dict[str, Any]]]
    digest: str

    @staticmethod
    def build(epoch: int, definitions: dict[str, list[dict[str, Any]]]) -> "WorkflowDictionary":
        if type(epoch) is not int or epoch < 0:
            raise CodecError("invalid dictionary epoch")
        if not definitions:
            raise CodecError("dictionary must not be empty")
        for alias, ops in definitions.items():
            if not SAFE_ID.fullmatch(alias):
                raise CodecError("invalid dictionary alias")
            if not isinstance(ops, list) or not ops:
                raise CodecError("dictionary definition must be non-empty list")
            test_ops = list(ops)
            if test_ops[-1].get("op") != "release_all":
                test_ops.append({"op": "release_all"})
            validate_program({
                "schema": SCHEMA_PROGRAM,
                "program_id": "dictcheck",
                "source": {"observation_seq": 0, "binding_revision": 0},
                "authority": {"lease_id": "dictcheck", "expires_at_ns": 1},
                "ops": test_ops,
                "terminal": {"release_all_required": True},
            })
        canonical = canonical_json({"epoch": epoch, "definitions": definitions})
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        return WorkflowDictionary(epoch, definitions, digest)

    def definition_payload(self) -> str:
        rows = []
        for alias in sorted(self.definitions):
            rows.append(alias + "=" + encode_ops_c1(self.definitions[alias]))
        return f"D0|{self.epoch}|{self.digest}|" + "~".join(rows)


def encode_c2_reference(program: dict[str, Any], dictionary: WorkflowDictionary, alias: str) -> str:
    validate_program(program)
    if alias not in dictionary.definitions:
        raise CodecError("unknown dictionary alias")
    expected_ops = list(dictionary.definitions[alias])
    if expected_ops[-1].get("op") != "release_all":
        expected_ops.append({"op": "release_all"})
    if program["ops"] != expected_ops:
        raise CodecError("program does not equal dictionary expansion")
    src = program["source"]
    auth = program["authority"]
    return (
        f"R0|{program['program_id']}|{src['observation_seq']}|{src['binding_revision']}|"
        f"{auth['lease_id']}|{auth['expires_at_ns']}|{dictionary.epoch}|{dictionary.digest}|{alias}"
    )


def decode_c2_reference(payload: str, dictionary: WorkflowDictionary) -> dict[str, Any]:
    parts = payload.split("|")
    if len(parts) != 9 or parts[0] != "R0":
        raise CodecError("invalid C2 reference")
    _, pid, seq, revision, lease, expires, epoch, digest, alias = parts
    try:
        parsed_epoch = int(epoch)
        parsed_seq = int(seq)
        parsed_revision = int(revision)
        parsed_expires = int(expires)
    except ValueError as error:
        raise CodecError("invalid C2 integer") from error
    if parsed_epoch != dictionary.epoch or digest != dictionary.digest:
        raise CodecError("stale dictionary epoch/digest")
    if alias not in dictionary.definitions:
        raise CodecError("unknown dictionary alias")
    ops = list(dictionary.definitions[alias])
    if ops[-1].get("op") != "release_all":
        ops.append({"op": "release_all"})
    program = {
        "schema": SCHEMA_PROGRAM,
        "program_id": pid,
        "source": {"observation_seq": parsed_seq, "binding_revision": parsed_revision},
        "authority": {"lease_id": lease, "expires_at_ns": parsed_expires},
        "ops": ops,
        "terminal": {"release_all_required": True},
    }
    try:
        return validate_program(program)
    except ContractError as error:
        raise CodecError(str(error)) from error
