#!/usr/bin/env python3
"""Check each trace's fates.csv against its links.jsonl, its as-stated.md and the reading protocol
(README, "Method"). Standard library only; prints one line per problem, exit 1 if any.

    python3 -I -B validate.py <mast-folder> [trace-folder ...]
"""
import csv, json, os, re, sys

LINE_M = re.compile(r"^Of (\d+) meanings, at the commit: (\d+) intact, (\d+) narrowed, (\d+) substituted, (\d+) absent, (\d+) restored", re.M)
LINE_C = re.compile(r"^Of (\d+) claims followed: (\d+) kept, (\d+) softened, (\d+) hardened, (\d+) dropped, (\d+) inverted at the commit"
                    r"(?:, and (\d+) made at the commit|[^\n]*?; (\d+) (?:of \d+ is made at the commit|stand as made))?", re.M)
LINE_S = re.compile(r"^Losses by site, of (\d+): design (\d+), source (\d+), seam (\d+), sink (\d+)", re.M)

M_STATES = {"intact", "narrowed", "substituted", "absent", "restored"}
C_STATES = {"·", "made", "kept", "softened", "hardened", "dropped", "inverted"}
SITES = {"design", "source", "seam", "sink"}


def check(root, t):
    out = []
    p = os.path.join(root, t)
    meta = json.loads(open(os.path.join(p, "links.jsonl"), encoding="utf-8").readline())
    links = [f"L{i:02d}" for i in range(meta["links"])]
    proxy = re.findall(r"^\|\s*(M\d+)\s*\|", open(os.path.join(p, "as-stated.md"), encoding="utf-8").read(), re.M)
    rd = csv.DictReader(open(os.path.join(p, "fates.csv"), newline="", encoding="utf-8"))
    head = rd.fieldnames
    want = ["unit", "kind", "type"] + links + ["final", "first_lost", "site", "correct", "commit"]
    if head != want:
        out.append(f"header differs: has {len(head)} columns, expected {len(want)} ({head[:4]}...{head[-6:]})")
        return out
    rows = list(rd)
    ms = [r for r in rows if r["kind"] == "meaning"]
    cs = [r for r in rows if r["kind"] == "claim"]
    mast = [r for r in rows if r["kind"] == "mast"]
    if [r["unit"] for r in ms] != proxy:
        out.append(f"meanings {[r['unit'] for r in ms]} differ from the proxy's {proxy}")
    if len(cs) > 8:
        out.append(f"{len(cs)} claims, protocol allows at most 8")
    commits = {r["commit"] for r in rows}
    if len(commits) != 1 or next(iter(commits)) not in links:
        out.append(f"commit column not one valid link: {commits}")
        return out
    commit = next(iter(commits))
    for r in ms + cs:
        states = [r[l] for l in links]
        ok = M_STATES if r["kind"] == "meaning" else C_STATES
        bad = [s for s in states if s not in ok]
        if bad:
            out.append(f"{r['unit']}: invalid states {sorted(set(bad))}")
            continue
        if r["final"] != r[commit]:
            out.append(f"{r['unit']}: final {r['final']!r} is not the state at the commit {r[commit]!r}")
        if r["kind"] == "meaning":
            if states[0] != "intact":
                out.append(f"{r['unit']}: L00 is {states[0]!r}, not intact")
            first = next((l for l in links if r[l] != "intact"), "")
            if r["correct"]:
                out.append(f"{r['unit']}: a meaning carries a correct value")
        else:
            first = next((l for l in links if r[l] not in ("·", "made", "kept")), "")
            if r["correct"] not in ("yes", "no", "unknown"):
                out.append(f"{r['unit']}: correct is {r['correct']!r}")
        if r["first_lost"] != first:
            out.append(f"{r['unit']}: first_lost {r['first_lost']!r}, the states say {first!r}")
        if bool(r["first_lost"]) != bool(r["site"]) or (r["site"] and r["site"] not in SITES):
            out.append(f"{r['unit']}: site {r['site']!r} with first_lost {r['first_lost']!r}")
    if len(mast) != 1:
        out.append(f"{len(mast)} MAST rows, expected 1")
    else:
        m = mast[0]
        try:
            n, k, j = (int(x) for x in m["final"].split("/"))
        except ValueError:
            out.append(f"MAST counts {m['final']!r} not n/k/j")
            return out
        set1 = sum(1 for v in meta["mast_annotation"].values() if v == 1)
        if n != set1:
            out.append(f"MAST n={n}, the annotation sets {set1}")
        word = "agree" if (k == n and j == 0) else ("disagree" if (k == 0 and n > 0) or (n == 0 and j > 0) else "partly")
        if m["type"] != word:
            out.append(f"MAST overall {m['type']!r}, the rule gives {word!r} for {n}/{k}/{j}")
    text = open(os.path.join(p, "reading.md"), encoding="utf-8").read() if os.path.exists(os.path.join(p, "reading.md")) else ""
    mm, mc, msi = LINE_M.search(text), LINE_C.search(text), LINE_S.search(text)
    if not (mm and mc and msi):
        out.append("reading.md lacks one of the three count lines (meanings, claims, losses by site)")
        return out
    want_m = [len(ms)] + [sum(1 for r in ms if r["final"] == f) for f in ("intact", "narrowed", "substituted", "absent", "restored")]
    if [int(x) for x in mm.groups()] != want_m:
        out.append(f"meanings line {mm.group(0)!r} differs from fates.csv {want_m}")
    want_c = [len(cs)] + [sum(1 for r in cs if r["final"] == f) for f in ("kept", "softened", "hardened", "dropped", "inverted")]
    got_c = [int(x) for x in mc.groups()[:6]]
    made = int(mc.group(7) or mc.group(8) or 0)
    if got_c != want_c or made != sum(1 for r in cs if r["final"] == "made"):
        out.append(f"claims line {mc.group(0)!r} differs from fates.csv {want_c} + made {sum(1 for r in cs if r['final'] == 'made')}")
    n, d, so, se, si = (int(x) for x in msi.groups())
    if d + so + se + si != n:
        out.append(f"losses line sums to {d + so + se + si}, not {n}")
    units = sum(1 for r in ms + cs if r["first_lost"])
    if n < units:
        out.append(f"losses line counts {n} events, fewer than the {units} units with a first loss")
    return out


def main():
    root = sys.argv[1]
    traces = sys.argv[2:] or sorted(d for d in os.listdir(root) if d[:1] == "t" and d[1:3].isdigit())
    bad = 0
    for t in traces:
        if not os.path.exists(os.path.join(root, t, "fates.csv")):
            print(f"{t}: no fates.csv yet")
            continue
        probs = check(root, t)
        print(f"{t}: {'ok' if not probs else str(len(probs)) + ' problem(s)'}")
        for x in probs:
            print("   ", x)
        bad += len(probs)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
