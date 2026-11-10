#!/usr/bin/env python3
"""Draw one map per trace (tNN/flow.svg) from its fates.csv with a status-flow renderer, draw_flow.py,
given as the third argument (the maps of 2026-10-31 were drawn with the renderer of sha256
bd6de9e29776716deb4583770a9d2959fc0a0366fb6fc7159b236ecd2134b948; REBUILD.md says which public copy
draws the same bytes). Standard library only; run with python3 -I -B.

    python3 -I -B maps.py <mast-folder> <scratch-folder> <draw_flow.py>

Columns of a map: the unit's kind (first column), the order (L00), every link where any unit's
state changed from the link before, and the commit; at most 13 columns of links (the order, the
first eleven change links, the commit). Red: narrowed, substituted, absent (terms) and
softened, hardened, dropped, inverted (claims), with every ribbon after them.
"""
import csv, json, os, subprocess, sys

BAD = ["narrowed", "substituted", "absent", "softened", "hardened", "dropped", "inverted"]
SHORT = {"Chief Executive Officer": "CEO", "Chief Product Officer": "CPO", "Chief Technology Officer": "CTO",
         "Programmer": "Programmer", "Code Reviewer": "Reviewer", "Counselor": "Counselor", "SimpleCoder": "Coder",
         "SimpleTester": "Tester", "SimpleReviewer": "Reviewer", "Planner": "Planner", "Navigator": "Navigator",
         "Editor": "Editor", "Executor": "Executor", "mathproxyagent": "proxy", "assistant": "solver", "Human": "order"}
SHAPE = {"MetaGPT": "line", "ChatDev": "line", "HyperAgent": "star", "AG2": "two-agent chat"}


def main():
    root, scratch, DRAW = sys.argv[1], sys.argv[2], os.path.abspath(sys.argv[3])
    os.makedirs(scratch, exist_ok=True)
    for t in sorted(d for d in os.listdir(root) if d[:1] == "t" and d[1:3].isdigit()):
        lines = [json.loads(x) for x in open(os.path.join(root, t, "links.jsonl"), encoding="utf-8")]
        meta, links = lines[0], {f"L{x['n']:02d}": x for x in lines[1:]}
        rows = [r for r in csv.DictReader(open(os.path.join(root, t, "fates.csv"), newline="", encoding="utf-8"))
                if r["kind"] in ("term", "meaning", "claim")]
        lcols = [c for c in rows[0].keys() if c[:1] == "L" and c[1:].isdigit()]
        commit = rows[0]["commit"]
        changed = [c for p, c in zip(lcols, lcols[1:]) if any(r[c] != r[p] for r in rows)]
        sel = ["L00"] + [c for c in changed if c not in ("L00", commit)][:11]
        if commit in lcols and commit not in sel:
            sel.append(commit)
        sel = sorted(set(sel), key=lcols.index)

        def name(c):
            who = SHORT.get(links[c]["from"], links[c]["from"]) if c in links else c
            return f"{c}_{who}" + ("_commit" if c == commit else "")

        stages = ["unit"] + [name(c) for c in sel]
        mp = os.path.join(scratch, f"{t}-map.csv")
        with open(mp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(stages)
            for r in rows:
                w.writerow([f"{r['kind']} ({r['type']})"] + [("not yet" if r[c] == "·" else r[c]) for c in sel])
        reds = []
        for s in stages[1:]:
            for b in BAD:
                reds += ["--red", f"{s}={b}"]
        title = f"{t[:3]} {meta['mas_name']} ({SHAPE[meta['mas_name']]}), MAST-Data row {meta['row_idx']}: where the order's terms and the claims' status went"
        sub = (f"{sum(1 for r in rows if r['kind'] in ('term', 'meaning'))} terms of the task-as-stated proxy and "
               f"{sum(1 for r in rows if r['kind'] == 'claim')} claims; {meta['links']} links, of which {len(sel)} drawn")
        notes = ["One run, read by a model, no second rater [C]; reconciled against the task-as-stated proxy, written before the run was read.",
                 "Columns: the order (L00), every link where a state changed, the commit. Red: narrowed, substituted, absent, softened, hardened, dropped, inverted.",
                 f"Source: MAST-Data (CC BY 4.0), {meta['mas_name']} on {meta['benchmark_name']} with {meta['llm_name']}; changed: scrubbed, split into links, read."]
        cmd = [sys.executable, "-I", "-B", DRAW, mp, "--stages", ",".join(stages), "--out", os.path.join(root, t, "flow.svg"),
               "--title", title, "--subtitle", sub] + sum((["--note", n] for n in notes), []) + reds + \
              ["--order", "unit=" + "|".join(sorted({f"{r['kind']} ({r['type']})" for r in rows}))]
        out = subprocess.run(cmd, capture_output=True, text=True)
        print(t, out.stdout.strip() or out.stderr.strip()[-300:])


if __name__ == "__main__":
    main()
