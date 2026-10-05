"""Compare naive text recall, lifecycle-typed recall, and ordinary packets."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "INPUT.json").read_text())
cue = data["cue"]
plain = [x["id"] for x in data["intentions"] if cue in x["text"]]
typed = []
for x in data["intentions"]:
    if x["cue"] != cue or x["authority"] != "CONFIRMED":
        continue
    if x["lifecycle"] == "PENDING":
        typed.append({"id": x["id"], "disposition": "RETRIEVE_CONTINUE"})
    elif x["lifecycle"] == "UNKNOWN_EFFECT":
        typed.append({"id": x["id"], "disposition": "RETRIEVE_VERIFY_FIRST"})
packets = [{"id": x["id"], "lifecycle": x["lifecycle"], "origin": x["authority"]}
           for x in data["intentions"]]
packet_recall = []
for packet in packets:
    if packet["origin"] == "CONFIRMED" and packet["lifecycle"] in {"PENDING", "UNKNOWN_EFFECT"}:
        packet_recall.append({"id": packet["id"], "disposition":
                              "RETRIEVE_CONTINUE" if packet["lifecycle"] == "PENDING"
                              else "RETRIEVE_VERIFY_FIRST"})
result = {"cue": cue, "plain_text": plain, "typed_lifecycle": typed,
          "ordinary_resumption_packet": packet_recall,
          "input_authority": False}
(HERE / "CANDIDATE.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
