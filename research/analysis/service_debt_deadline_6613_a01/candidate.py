import json
import sys


def requests(seed, scenario):
    x = (seed ^ {"asymmetric_recurring": 0x13579BDF, "burst_recovery": 0x2468ACE0,
                 "rights_interrupt": 0x5A5A5A5A}[scenario]) & 0xffffffff
    def draw():
        nonlocal x
        x ^= (x << 13) & 0xffffffff
        x ^= x >> 17
        x ^= (x << 5) & 0xffffffff
        x &= 0xffffffff
        return x
    tasks=[]
    for principal in ("A","B"):
        at=0
        for i in range(6):
            if scenario == "burst_recovery":
                at = (draw() % 2) if i < 3 else 8 + draw() % 3
            else:
                at += draw() % 3
            service=1+draw()%6
            deadline=at+service+draw()%16
            eligible=not (scenario=="rights_interrupt" and principal=="B" and i==2)
            tasks.append({"id":f"{principal}{i}","principal":principal,"arrival":at,
                          "service":service,"deadline":deadline,"eligible":eligible,"mandatory":False})
    if scenario == "rights_interrupt":
        at=1+draw()%4
        tasks.append({"id":"SYS0","principal":"SYS","arrival":at,"service":1,
                      "deadline":at+1,"eligible":True,"mandatory":True})
    return tasks


def schedule(tasks, policy):
    pending = list(tasks)
    done = []
    now = 0
    debt = {}
    turn = 0
    while pending:
        ready = [x for x in pending if x["arrival"] <= now and x["eligible"]]
        if not ready:
            future = [x["arrival"] for x in pending if x["eligible"] and x["arrival"] > now]
            if not future:
                break
            now = min(future)
            continue
        urgent = [x for x in ready if x["mandatory"]]
        pool = urgent or ready
        if policy == "fifo":
            item = min(pool, key=lambda x: (x["arrival"], x["id"]))
        elif policy == "shortest":
            item = min(pool, key=lambda x: (x["service"], x["arrival"], x["id"]))
        else:
            principals = sorted({x["principal"] for x in pool})
            ordered = principals[turn % len(principals):] + principals[:turn % len(principals)]
            rank = {p: i for i, p in enumerate(ordered)}
            item = min(pool, key=lambda x: (debt.get(x["principal"], 0), rank[x["principal"]], x["arrival"], x["id"]))
            turn += 1
        start = max(now, item["arrival"])
        end = start + item["service"]
        done.append({"id": item["id"], "principal": item["principal"], "start": start,
                     "end": end, "wait": start-item["arrival"], "on_time": end <= item["deadline"],
                     "mandatory": item["mandatory"], "eligible": item["eligible"]})
        now = end
        debt[item["principal"]] = debt.get(item["principal"], 0) + item["service"]
        pending.remove(item)
    return done


def main(src, dst, construction=False):
    with open(src, encoding="utf-8") as source:
        fixture = json.load(source)
    result = {"allocation_id": fixture["allocation_id"], "rows": []}
    seeds=fixture["construction_seeds"] if construction else fixture["formal_seeds"]
    for seed in seeds:
      for scenario in fixture["scenarios"]:
        for policy in fixture["policies"]:
            tasks = requests(seed,scenario)
            schedule_rows = schedule(tasks, policy)
            offered = [{"id":t["id"],"eligible":t["eligible"],"mandatory":t["mandatory"]} for t in tasks]
            result["rows"].append({"seed":seed,"scenario":scenario,"policy":policy,"offered":offered,"schedule":schedule_rows})
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--construction" in sys.argv[3:])
