#!/usr/bin/env python3
"""Coherence/linearization check for adaptive branch witnesses.

Selected branch: a == 0.
Competitor: b == 1 AND c == 1.
Plan state: a=0,b=0,c=0, with b as the retained false witness.
Writer mutation: atomically set b=c=1, making branch selection ambiguous while
the selected branch remains true.
"""
import json, os, sqlite3, statistics, tempfile, threading, time

REPETITIONS = 100
ORDER_REPETITIONS = 50


def init_db(path):
    conn = sqlite3.connect(path, timeout=5, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE state(k TEXT PRIMARY KEY, v INTEGER)")
    conn.executemany("INSERT INTO state(k,v) VALUES (?,?)", [("a",0),("b",0),("c",0)])
    conn.execute("CREATE TABLE effect(id INTEGER PRIMARY KEY AUTOINCREMENT, note TEXT)")
    conn.close()


def readv(conn, key):
    return conn.execute("SELECT v FROM state WHERE k=?", (key,)).fetchone()[0]


def temporary_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    init_db(path)
    return path


def nontransactional_once():
    path = temporary_db()
    checker = sqlite3.connect(path, timeout=5, isolation_level=None)
    writer = sqlite3.connect(path, timeout=5, isolation_level=None)
    a = readv(checker, "a")
    b = readv(checker, "b")
    writer.execute("BEGIN IMMEDIATE")
    writer.execute("UPDATE state SET v=1 WHERE k IN ('b','c')")
    writer.commit()
    accept = a == 0 and b != 1
    if accept:
        checker.execute("INSERT INTO effect(note) VALUES ('go')")
    final = tuple(readv(checker, key) for key in ("a","b","c"))
    effects = checker.execute("SELECT COUNT(*) FROM effect").fetchone()[0]
    checker.close(); writer.close(); os.remove(path)
    return {"accept": accept, "final": final, "effects": effects,
            "wrong_effect_after_writer": final == (0,1,1) and effects == 1}


def writer_first_once():
    path = temporary_db()
    writer = sqlite3.connect(path, timeout=5, isolation_level=None)
    writer.execute("BEGIN IMMEDIATE")
    writer.execute("UPDATE state SET v=1 WHERE k IN ('b','c')")
    writer.commit(); writer.close()
    checker = sqlite3.connect(path, timeout=5, isolation_level=None)
    checker.execute("BEGIN IMMEDIATE")
    a = readv(checker, "a")
    b = readv(checker, "b")
    competitor = b == 1 and readv(checker, "c") == 1
    accept = a == 0 and not competitor
    if accept:
        checker.execute("INSERT INTO effect(note) VALUES ('go')")
    checker.commit()
    final = tuple(readv(checker, key) for key in ("a","b","c"))
    effects = checker.execute("SELECT COUNT(*) FROM effect").fetchone()[0]
    checker.close(); os.remove(path)
    return {"accept": accept, "final": final, "effects": effects,
            "correct": not accept and effects == 0}


def checker_first_once():
    path = temporary_db()
    ready = threading.Event(); done = threading.Event(); writer_wait_ms = []
    def writer_thread():
        conn = sqlite3.connect(path, timeout=5, isolation_level=None)
        ready.wait()
        started = time.perf_counter_ns()
        conn.execute("BEGIN IMMEDIATE")
        writer_wait_ms.append((time.perf_counter_ns() - started) / 1e6)
        conn.execute("UPDATE state SET v=1 WHERE k IN ('b','c')")
        conn.commit(); conn.close(); done.set()
    thread = threading.Thread(target=writer_thread)
    thread.start()
    checker = sqlite3.connect(path, timeout=5, isolation_level=None)
    checker.execute("BEGIN IMMEDIATE")
    a = readv(checker, "a")
    b = readv(checker, "b")
    ready.set()
    time.sleep(0.005)
    competitor = b == 1 and readv(checker, "c") == 1
    accept = a == 0 and not competitor
    if accept:
        checker.execute("INSERT INTO effect(note) VALUES ('go')")
    checker.commit()
    done.wait(); thread.join()
    final = tuple(readv(checker, key) for key in ("a","b","c"))
    effects = checker.execute("SELECT COUNT(*) FROM effect").fetchone()[0]
    checker.close(); os.remove(path)
    return {"accept": accept, "final": final, "effects": effects,
            "writer_wait_ms": writer_wait_ms[0],
            "correct_linearization": accept and effects == 1}


def main():
    sequential = [nontransactional_once() for _ in range(REPETITIONS)]
    writer_first = [writer_first_once() for _ in range(ORDER_REPETITIONS)]
    checker_first = [checker_first_once() for _ in range(ORDER_REPETITIONS)]
    summary = {
        "schema": "adaptive-witness-coherence-sqlite-v1",
        "nontransactional": {
            "rows": len(sequential),
            "wrong_effects": sum(row["wrong_effect_after_writer"] for row in sequential),
        },
        "transaction_writer_first": {
            "rows": len(writer_first),
            "correct_rejects": sum(row["correct"] for row in writer_first),
        },
        "transaction_checker_first": {
            "rows": len(checker_first),
            "correct_effect_first_linearizations": sum(row["correct_linearization"] for row in checker_first),
            "writer_wait_ms_median": statistics.median(row["writer_wait_ms"] for row in checker_first),
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
