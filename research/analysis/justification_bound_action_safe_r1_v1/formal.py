#!/usr/bin/env python3
import argparse, hashlib, itertools, json, platform
from pathlib import Path

SUPPORTS = ("B0", "B1", "B2")
JUSTIFICATION_MASKS = (0b001, 0b010, 0b100, 0b011, 0b101, 0b110)
STATE_NAMES = ("SAME_FALSE", "SAME_TRUE", "CHANGED_FALSE", "CHANGED_TRUE")


def family_justifications(family_mask):
    return tuple(JUSTIFICATION_MASKS[i] for i in range(len(JUSTIFICATION_MASKS)) if family_mask & (1 << i))


def is_satisfied(justification_mask, truth_mask):
    return (truth_mask & justification_mask) == justification_mask


def current_truth_mask(states):
    out = 0
    for i, s in enumerate(states):
        if s in (1, 3):
            out |= 1 << i
    return out


def candidate_action_safe(family_mask, commit_truth_mask, states):
    # Frozen candidate: only justifications actually satisfied at COMMIT are recorded.
    # A recorded justification survives only if every support remains same-version + true.
    for j in family_justifications(family_mask):
        if not is_satisfied(j, commit_truth_mask):
            continue
        ok = True
        for i in range(3):
            if (j >> i) & 1 and states[i] != 1:  # SAME_TRUE½¹±ä(½¬ô±Í(É¬(¥½¬è(ÉÑÕÉ¸QÉÕ(ÉÑÕÉ¸±Í(()½µÁÉÑ½É}ÍÑ¥­å}½µµ¥ÑÑ¡µ¥±å}µÍ¬°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬°ÍÑÑÌ¤è(ÉÑÕÉ¸QÉÕ(()½µÁÉÑ½É}ÕÉÉ¹Ñ}ÑÉÕÑ¡}½¹±ä¡µ¥±å}µÍ¬°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬°ÍÑÑÌ¤è(¹½ÜôÕÉÉ¹Ñ}ÑÉÕÑ¡}µÍ¬¡ÍÑÑÌ¤(ÉÑÕÉ¸¹ä¡¥Í}ÍÑ¥Í¥¡¨°¹½Ü¤½È¨¥¸µ¥±å}©ÕÍÑ¥¥Ñ¥½¹Ì¡µ¥±å}µÍ¬¤¤(()½µÁÉÑ½É}±±}½µµ¥ÑÑ}ÍÕÁÁ½ÉÑÍ}ÕÉÉ¹Ð¡µ¥±å}µÍ¬°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬°ÍÑÑÌ¤è(Õ¹¥½¸ôÀ(½È¨¥¸µ¥±å}©ÕÍÑ¥¥Ñ¥½¹Ì¡µ¥±å}µÍ¬¤è(¥¥Í}ÍÑ¥Í¥¡¨°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬¤è(Õ¹¥½¸ðô¨(ÉÑÕÉ¸Õ¹¥½¸ôÀ¹±°¡ÍÑÑÍm¥tôôÄ½È¤¥¸É¹ Ì¤¥¡Õ¹¥½¸øø¤¤Ä¤(()¥¹Á¹¹Ñ}½É±¡µ¥±å}µÍ¬°½µ¥Ñ}ÑÉÕÑ¡}µÍ¬°ÍÑÑÌ¤è(%¹Ñ¹Ñ¥½¹±±äÍÑÉÕÑÕÉÝ¥Ñ ¹µÍÑÌ½¥ÑÌÉÑ¡ÈÑ¡¸¹¥Ñ¥ÐµµÍ¬ÍÕÉÙ¥Ù°±½½¥¸(µ¥±äômt(½È¥à°µÍ¬¥¸¹ÕµÉÑ¡)UMQ%%Q%=9}5M-L¤è(¥µ¥±å}µÍ¬ Äðð¥à¤è(µ¥±ä¹ÁÁ¹¡É½é¹ÍÐ¡MUAA=IQMm¥t½È¤¥¸É¹ Ì¤¥¡µÍ¬øø¤¤Ä¤¤(½µµ¥Ñ}ÑÉÕÑ ôíMUAA=IQMm¥tè½½° ¡½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬øø¤¤Ä¤½È¤¥¸É¹ Ì¥ô(½µµ¥Ñ}ÙÉÍ¥½¸ôí¹µèØÀ½È¹µ¥¸MUAA=IQMô(É½Éôm¨½È¨¥¸µ¥±ä¥±°¡½µµ¥Ñ}ÑÉÕÑ¡m¹µt½È¹µ¥¸¨¥t(ÕÉÉ¹Ðôíô(½È¤°¹µ¥¸¹ÕµÉÑ¡MUAA=IQL¤è(ÍµôÍÑÑÍm¥tðÈ(ÑÉÕÑ ôÍÑÑÍm¥t¥¸ Ä°Ì¤(ÕÉÉ¹Ñm¹µtôìÙÉÍ¥½¸èØÀ¥Íµ±ÍØÄ°ÑÉÕÑ èÑÉÕÑ¡ô(½È©ÕÍÑ¥¥Ñ¥½¸¥¸É½Éè(¥±°¡ÕÉÉ¹Ñm¹µulÑÉÕÑ t¹ÕÉÉ¹Ñm¹µulÙÉÍ¥½¸tôô½µµ¥Ñ}ÙÉÍ¥½¹m¹µt½È¹µ¥¸©ÕÍÑ¥¥Ñ¥½¸¤è(ÉÑÕÉ¸QÉÕ(ÉÑÕÉ¸±Í(()É½Ý}É½É¡µ¥±å}µÍ¬°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬°ÍÑÑÌ¤è(µ¥±äôµ¥±å}©ÕÍÑ¥¥Ñ¥½¹Ì¡µ¥±å}µÍ¬¤(É½ÉôÑÕÁ±¡¨½È¨¥¸µ¥±ä¥¥Í}ÍÑ¥Í¥¡¨°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬¤¤(¥¹½ÐÉ½Éè(ÉÑÕÉ¸9½¹(¹¥Ñô¹¥Ñ}Ñ¥½¹}Í¡µ¥±å}µÍ¬°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬°ÍÑÑÌ¤(½É±ô¥¹Á¹¹Ñ}½É±¡µ¥±å}µÍ¬°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬°ÍÑÑÌ¤(¹½Ý}ÑÉÕÑ ôÕÉÉ¹Ñ}ÑÉÕÑ¡}µÍ¬¡ÍÑÑÌ¤(Õ¹½µµ¥ÑÑ}¹½Ý}ÑÉÕô¹ä (¡¨¹½Ð¥¸É½É¤¹¥Í}ÍÑ¥Í¥¡¨°¹½Ý}ÑÉÕÑ ¤(½È¨¥¸µ¥±ä(¤(±±}½µµ¥ÑÑô½µÁÉÑ½É}±±}½µµ¥ÑÑ}ÍÕÁÁ½ÉÑÍ}ÕÉÉ¹Ð¡µ¥±å}µÍ¬°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬°ÍÑÑÌ¤(ÉÑÕÉ¸ì(µ¥±å}µÍ¬èµ¥±å}µÍ¬°(½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬è½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬°(ÍÑÑÌè±¥ÍÐ¡ÍÑÑÌ¤°(¹¥Ñè¹¥Ñ°(½É±è½É±°(ÍÑ¥­äè½µÁÉÑ½É}ÍÑ¥­å}½µµ¥ÑÑ¡µ¥±å}µÍ¬°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬°ÍÑÑÌ¤°(ÕÉÉ¹Ñ}ÑÉÕÑ¡}½¹±äè½µÁÉÑ½É}ÕÉÉ¹Ñ}ÑÉÕÑ¡}½¹±ä¡µ¥±å}µÍ¬°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬°ÍÑÑÌ¤°(±±}½µµ¥ÑÑè±±}½µµ¥ÑÑ°(¹Ý±å}ÑÉÕ}Õ¹½µµ¥ÑÑèÕ¹½µµ¥ÑÑ}¹½Ý}ÑÉÕ°(É½É}½Õ¹Ðè±¸¡É½É¤°(ô(()¥ÉÑ}½¹ÑÉ½±Ì ¤è(µ¥±äµÍ­ÌÕÍ)UMQ%%Q%=9}5M-L½ÉÉ¥¹èÀ±Ä±È±ÁÄ±ÁÈ±ÅÈ¸(½¹ÑÉ½±Ìôl( Õ¹½µµ¥ÑÑ}¹Ý}ÑÉÕ°ÁÀÀÀÀÄÄ°ÁÀÀÄ° È°Ì°À¤°±Í¤°( ÍÑ±}½¹}½µµ¥ÑÑ}±ÑÉ¹Ñ¥Ù°ÁÀÀÀÀÄÄ°ÁÀÄÄ° Ä°È°À¤°QÉÕ¤°( ÍÑ±}±±}½µµ¥ÑÑ}±ÑÉ¹Ñ¥ÙÌ°ÁÀÀÀÀÄÄ°ÁÀÄÄ° È°È°À¤°±Í¤°( É½É}ÍÕÁÁ½ÉÑ}ÙÉÍ¥½¹}µÕÑÑ¥½¸°ÁÀÀÀÀÀÄ°ÁÀÀÄ° Ì°À°À¤°±Í¤°(t(½ÕÐômt(½È¹µ°´°½µµ¥Ð°ÍÑÑÌ°áÁÑ¥¸½¹ÑÉ½±Ìè(ÈôÉ½Ý}É½É¡´°½µµ¥Ð°ÍÑÑÌ¤(½ÕÐ¹ÁÁ¹¡ì¹µè¹µ°áÁÑèáÁÑ°¹¥ÑèÉl¹¥Ñt°½É±èÉl½É±t°ÁÍÌèÉl¹¥ÑtôôÉl½É±tôôáÁÑô¤(ÉÑÕÉ¸½ÕÐ(()¹ÕµÉÑ}É½ÝÌ¡µ¥±å}µÍ­Ì¤è(½Õ¹ÑÉÌôì(É½ÝÌèÀ°(¹¥Ñ}ÑÉÕèÀ°(¹¥Ñ}±ÍèÀ°(¹¥Ñ}½É±}µ¥ÍµÑ èÀ°(¹¥Ñ}½É±}Õ¹Í}µ¥ÑÌèÀ°(¹¥Ñ}½É±}±Í}É©ÑÌèÀ°(¹¥Ñ}ÑÉÕ}Ý¥Ñ¡½ÕÑ}É½É}ÕÉÉ¹Ñ}Ý¥Ñ¹ÍÌèÀ°(ÍÑ±}±±}½µµ¥ÑÑ}É½ÝÌèÀ°(ÍÑ±}±±}½µµ¥ÑÑ}¹¥Ñ}µ¥ÑÌèÀ°(¹Ý±å}ÑÉÕ}Õ¹½µµ¥ÑÑ}É½ÝÌèÀ°(¹Ý±å}ÑÉÕ}Õ¹½µµ¥ÑÑ}¹¥Ñ}µ¥ÑÌèÀ°(ÍÕÉÙ¥Ù¥¹}½µµ¥ÑÑ}±ÑÉ¹Ñ¥Ù}É½ÝÌèÀ°(ÍÑ¥­å}Õ¹Í}µ¥ÍÍ¥½¹ÌèÀ°(ÕÉÉ¹Ñ}ÑÉÕÑ¡}½¹±å}Õ¹Í}µ¥ÍÍ¥½¹ÌèÀ°(±±}½µµ¥ÑÑ}ÍÕÁÁ½ÉÑÍ}±Í}É©Ñ¥½¹ÌèÀ°(ô(¥ÍÐô¡Í¡±¥¹Í¡ÈÔØ ¤(Ù±¥}½µµ¥Ñ}Á¥ÉÌôÀ(½Èµ¥±å}µÍ¬¥¸µ¥±å}µÍ­Ìè(µ¥±äôµ¥±å}©ÕÍÑ¥¥Ñ¥½¹Ì¡µ¥±å}µÍ¬¤(½È½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬¥¸É¹ à¤è(É½ÉôÑÕÁ±¡¨½È¨¥¸µ¥±ä¥¥Í}ÍÑ¥Í¥¡¨°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬¤¤(¥¹½ÐÉ½Éè(½¹Ñ¥¹Õ(Ù±¥}½µµ¥Ñ}Á¥ÉÌ¬ôÄ(½ÈÍÑÑÌ¥¸¥ÑÉÑ½½±Ì¹ÁÉ½ÕÐ¡É¹ Ð¤°ÉÁÐôÌ¤è(ÈôÉ½Ý}É½É¡µ¥±å}µÍ¬°½µµ¥Ñ}ÑÉÕÑ¡}µÍ¬°ÍÑÑÌ¤(½Õ¹ÑÉÍlÉ½ÝÌt¬ôÄ(¹¥ÑôÉl¹¥Ñt(¥¹¥Ñè(½Õ¹ÑÉÍl¹¥Ñ}ÑÉÕt¬ôÄ(±Íè(½Õ¹ÑÉÍl¹¥Ñ}±Ít¬ôÄ(½Õ¹ÑÉÍlÍÑ±}±±}½µµ¥ÑÑ}É½ÝÌt¬ôÄ(¥¹¥ÑôÉl½É±tè(½Õ¹ÑÉÍl¹¥Ñ}½É±}µ¥ÍµÑ t¬ôÄ(¥¹¥Ñ¹¹½ÐÉl½É±tè(½Õ¹ÑÉÍl¹¥Ñ}½É±}Õ¹Í}µ¥ÑÌt¬ôÄ(±¥Él½É±t¹¹½Ð¹¥Ñè(½Õ¹ÑÉÍl¹¥Ñ}½É±}±Í}É©ÑÌt¬ôÄ(¥¹¥Ñ¹¹½ÐÉl½É±tè(½Õ¹ÑÉÍl¹¥Ñ}ÑÉÕ}Ý¥Ñ¡½ÕÑ}É½É}ÕÉÉ¹Ñ}Ý¥Ñ¹ÍÌt¬ôÄ(¥¹½ÐÉl½É±t¹¹¥Ñè(½Õ¹ÑÉÍlÍÑ±}±±}½µ¥ÑÑ}¹¥Ñ}µ¥ÑÌt¬ôÄ(¥r["newly_true_uncommitted"] and not r["oracle"]:
                    counters["newly_true_uncommitted_rows"] += 1
                    if candidate:
                        counters["newly_true_uncommitted_candidate_admits"] += 1
                if candidate and not r["all_committed"]:
                    counters["surviving_committed_alternative_rows"] += 1
                if r["sticky"] and not candidate:
                    counters["sticky_unsafe_admissions"] += 1
                if r["current_truth_only"] and not candidate:
                    counters["current_truth_only_unsafe_admissions"] += 1
                if candidate and not r["all_committed"]:
                    counters["all_committed_supports_false_rejections"] += 1
                digest.update(json.dumps(r, sort_keys=True, separators=(",", ":")).encode())
                digest.update(b"\n")
    return counters, valid_commit_pairs, digest.hexdigest()


def decision(counters, controls, expected_rows=None):
    gates = {
        "row_count": expected_rows is None or counters["rows"] == expected_rows,
        "candidate_oracle_mismatch0": counters["candidate_oracle_mismatch"] == 0,
        "candidate_oracle_unsafe_admits0": counters["candidate_oracle_unsafe_admits"] == 0,
        "candidate_oracle_false_rejects0": counters["candidate_oracle_false_rejects"] == 0,
        "candidate_witness_integrity": counters["candidate_true_without_recorded_current_witness"] == 0,
        "stale_all_admits0": counters["stale_all_committed_candidate_admits"] == 0,
        "newly_true_uncommitted_rows_positive": counters["newly_true_uncommitted_rows"] > 0,
        "newly_true_uncommitted_admits0": counters["newly_true_uncommitted_candidate_admits"] == 0,
        "surviving_alternative_positive": counters["surviving_committed_alternative_rows"] > 0,
        "sticky_unsafe_positive": counters["sticky_unsafe_admissions"] > 0,
        "current_truth_only_unsafe_positive": counters["current_truth_only_unsafe_admissions"] > 0,
        "all_committed_false_rejections_positive": counters["all_comitted_supports_false_rejections"] > 0,
        "directed_controls": all(x["pass"] for x in controls),
    }
    if all(gates.values()):
        return "PASS_JUSTIFICATION_BOUND_ACTION_SAFE_SCOPED", gates
    if counters["candidate_oracle_unsafe_admits"] or counters["stale_all_committed_candidate_admits"] or counters["newly_true_uncommitted_candidate_admits"]:
        return "FAIL_ACTION_SUPPORT_LAUNDERING", gates
    if counters["candidate_oracle_false_rejects"]:
        return "FAIL_ALTERNATIVE_SUPPORT_OVERINVALIDATION", gates
    return "FAIL_INTEGRITY", gates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("construction", "formal"), required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.mode == "construction":
        family_masks = tuple(range(1, 9))
        expected_rows = None
    else:
        family_masks = tuple(range(1, 64))
        expected_rows = 20928
    counters, valid_commit_pairs, stream_sha256 = enumerate_rows(family_masks)
    controls = directed_controls()
    dec, gates = decision(counters, controls, expected_rows)
    if args.mode == "construction" and dec == "PASS_JUSTIFICATION_BOUND_ACTION_SAFE_SCOPED":
        dec = "PASS_CONSTRUCTION_ELIGIBLE(    result = {
        "task": "JUSTIFICATION-BOUND-ACTION-SAFE-R1-20260919-001",
        "mode": args.mode,
        "decision": dec,
        "supports": list(SUPPORTS),
        "justification_masks": list(JUSTIFICATION_MASKS),
        "family_count": len(family_masks),
        "valid_commit_pairs": valid_commit_pairs,
        "state_alphabet": list(STATE_NAMES),
        "counters": counters,
        "directed_controls": controls,
        "gates": gates,
        "stream_sha256": stream_sha256,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "formal_invocations": 1 if args.mode == "formal" else 0,
        "reruns": 0,
        "replacements": 0,
        "post_freeze_tuning": 0,
    }
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": dec, "valid_commit_pairs": valid_commit_pairs, "counters": counters, "stream_sha256": stream_sha256}, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
