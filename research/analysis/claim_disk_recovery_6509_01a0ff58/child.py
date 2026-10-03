"""One isolated writer or read-only recovery process; not a runtime adapter."""
import hashlib
import json
import os
from pathlib import Path
import sys

from recovery import recover

def write(folder, case):
    folder.mkdir(exist_ok=False)
    journal = folder / "receipts.jsonl"
    with journal.open("xb") as stream:
        for number, check in enumerate(("identity", "freshness", "effect"), 1):
            value = not (case["negative"] and check == "identity")
            item = dict(sequence=number, check=check, value=value, generation=1, scope="synthetic-claim")
            if case["cut"] == "torn_third" and number == 3:
                stream.write(b'{"sequence":3')
                stream.flush()
                os.fsync(stream.fileno())
                os._exit(73)
            stream.write((json.dumps(item, sort_keys=True) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())
            if case["cut"] == "receipt_" + str(number):
                os._exit(73)
        if case["cut"] == "before_commit":
            os._exit(73)
        marker = folder / "cached-verdict.json"
        with marker.open("x", encoding="utf-8", newline="\n") as target:
            json.dump({"disposition": "COMPLETE_VERDICT"}, target)
            target.write("\n")
            target.flush()
            os.fsync(target.fileno())
        if case["duplicate"]:
            duplicate = dict(sequence=4, check="effect", value=True, generation=1, scope="synthetic-claim")
            stream.write((json.dumps(duplicate, sort_keys=True) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())
        os._exit(73)

def read(folder, case):
    journal = folder / "receipts.jsonl"
    result = recover(journal, generation=case["generation"])
    result["journal_sha256"] = hashlib.sha256(journal.read_bytes()).hexdigest()
    result["consumer_authority"] = False
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    mode, folder, encoded = sys.argv[1:]
    case = json.loads(encoded)
    (write if mode == "write" else read)(Path(folder), case)
