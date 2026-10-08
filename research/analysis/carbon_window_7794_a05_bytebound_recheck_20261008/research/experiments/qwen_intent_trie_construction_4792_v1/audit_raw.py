import copy
import hashlib
import json
import os
from pathlib import Path

from transformers import AutoTokenizer


MODEL = os.environ["MODEL_DIR"]
RESULT = Path("/out/construction-result.json")
SOURCE = Path("/src/run_construction.py")
CANDIDATES = [
    '{"op":"set","field":"display_name","value":"probe-name"}',
    '{"op":"set","field":"timezone","value":"Asia/Tokyo"}',
    '{"op":"set","field":"digest_frequency","value":"weekly"}',
    '{"op":"set","field":"sharing_visibility","value":"private"}',
    '{"op":"save"}',
    '{"op":"toggle","target":"toggle_email_reminders"}',
    '{"op":"yield","reason":"forbidden"}',
    '{"op":"yield","reason":"ambiguous"}',
    '{"op":"yield","reason":"stale_scope"}',
    '{"op":"yield","reason":"missing_evidence"}',
    '{"op":"yield","reason":"unsupported"}',
    '{"op":"no_action","reason":"already_satisfied"}',
    '{"op":"no_action","reason":"not_requested"}',
]
EXPECTED_SOURCE_SHA256 = "3e20f576d709a78ee06858dcd1076286bf922515bca8b5965dffe668a19bc6f4"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def valid(r, tokenizer):
    if sha(SOURCE.read_bytes()) != EXPECTED_SOURCE_SHA256:
        return False
    if r.get("candidate_hash") != sha("\n".join(CANDIDATES).encode()):
        return False
    if r.get("candidate_count") != len(CANDIDATES) or len(set(CANDIDATES)) != len(CANDIDATES):
        return False
    arms = r.get("arms", {})
    if set(arms) != {"free", "trie"}:
        return False
    free, trie = arms["free"], arms["trie"]
    if free.get("candidate_member") is not False or free.get("parse_error") is not None:
        return False
    if not isinstance(free.get("parsed"), dict) or free["parsed"].get("compactIntent") != "timezoneChange":
        return False
    if trie.get("candidate_member") is not True or trie.get("parse_error") is not None:
        return False
    if trie.get("raw_text") not in CANDIDATES or json.loads(trie["raw_text"]) != trie.get("parsed"):
        return False
    if not trie.get("ended_with_eos"):
        return False
    if tokenizer.decode(trie["token_ids"], skip_special_tokens=True,
                        clean_up_tokenization_spaces=False) != trie["raw_text"]:
        return False
    if r.get("prefix_checks") != 175 or r.get("construction_pass") is not True:
        return False
    return True


def main():
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    raw = json.loads(RESULT.read_text(encoding="utf-8"))
    errors = [] if valid(raw, tokenizer) else ["raw_result_integrity"]
    controls = {}
    mutations = {
        "candidate_hash": lambda x: x.__setitem__("candidate_hash", "0" * 64),
        "candidate_count": lambda x: x.__setitem__("candidate_count", 99),
        "free_candidate": lambda x: x["arms"]["free"].__setitem__("candidate_member", True),
        "trie_member": lambda x: x["arms"]["trie"].__setitem__("candidate_member", False),
        "trie_eos": lambda x: x["arms"]["trie"].__setitem__("ended_with_eos", False),
        "trie_parse": lambda x: x["arms"]["trie"].__setitem__("parse_error", "JSONDecodeError"),
        "prefix_checks": lambda x: x.__setitem__("prefix_checks", 174),
        "construction_gate": lambda x: x.__setitem__("construction_pass", False),
    }
    for name, mutate in mutations.items():
        changed = copy.deepcopy(raw)
        mutate(changed)
        controls[name] = not valid(changed, tokenizer)
    passed = not errors and all(controls.values())
    audit = {"passed": passed, "errors": errors, "checks": 13 + len(controls),
             "corruption_controls": controls, "rejected_controls": sum(controls.values()),
             "result_sha256": sha(RESULT.read_bytes()),
             "source_sha256": sha(SOURCE.read_bytes())}
    (Path("/out") / "independent-audit.json").write_text(
        json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()

