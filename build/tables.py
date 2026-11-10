#!/usr/bin/env python3
"""Build the counts table of the ten-trace reading from each trace folder's links.jsonl
(the deterministic tier, [D]) and fates.csv (the model-read tier, [C]). Standard library only.

    python3 -I -B tables.py <mast-folder>

Writes <mast-folder>/counts.csv (one row per trace, then one per shape, then the total) and
<mast-folder>/counts.md (the same counts, each with its denominator). No percentage is computed.
"""
import csv, json, os, re, sys

LINE_S = re.compile(r"^Losses by site, of (\d+): design (\d+), source (\d+), seam (\d+), sink (\d+)", re.M)
EVENT = re.compile(r"^- (L\d\d)\s*[,·]\s*([MC]\d+)\s*[,·]\s*(narrowed|substituted|absent|softened|hardened|dropped|inverted|restored)\s*[,·]\s*(design|source|seam|sink)", re.M)


def events(text):
    """Loss events as each reading's section 4 lists them: (link, unit, fate, site)."""
    return EVENT.findall(text[text.index("## 4."):text.index("## 5.")])


def zero_codes_set(text, zeros):
    """MAST codes the annotation leaves at 0 that a reading's section 5 table marks as seen or partly seen."""
    sec5 = text[text.index("## 5."):text.index("## 6.")]
    seen, partly = set(), set()
    for row in re.findall(r"^\|([^\n]*)\|\s*$", sec5, re.M):
        cells = [c.strip() for c in row.split("|")]
        m = re.search(r"(\d\.\d)", cells[0]) if cells else None
        if len(cells) >= 3 and cells[1] == "0" and m and m.group(1) in zeros:
            seen.add(m.group(1))
            if cells[2].lower().startswith("partly"):
                partly.add(m.group(1))
    return len(seen), len(partly)

SHAPE = {"MetaGPT": "line", "ChatDev": "line", "HyperAgent": "star", "AG2": "two-agent chat"}
M_FATES = ["intact", "narrowed", "substituted", "absent", "restored"]
C_FATES = ["kept", "softened", "hardened", "dropped", "inverted", "made"]
SITES = ["design", "source", "seam", "sink"]
D_MARKERS = ["sentences", "hedged", "not_found", "strengthened", "sourced", "dated"]


def trace_dirs(root):
    return sorted(d for d in os.listdir(root) if d[:1] == "t" and d[1:3].isdigit() and os.path.isdir(os.path.join(root, d)))


def read_trace(root, t):
    meta = json.loads(open(os.path.join(root, t, "links.jsonl"), encoding="utf-8").readline())
    rows = list(csv.DictReader(open(os.path.join(root, t, "fates.csv"), newline="", encoding="utf-8")))
    m = [r for r in rows if r["kind"] == "meaning"]
    c = [r for r in rows if r["kind"] == "claim"]
    mast = [r for r in rows if r["kind"] == "mast"]
    n, k, j = (mast[0]["final"].split("/") if mast else ("", "", ""))
    rec = {"trace": t, "n_traces": 1, "row": meta["row_idx"], "shape": SHAPE[meta["mas_name"]], "framework": meta["mas_name"],
           "model": meta["llm_name"], "benchmark": meta["benchmark_name"], "commit": (rows[0]["commit"] if rows else ""),
           "links_D": meta["links"], "roles_D": len(meta["roles"]), "inner_steps_D": meta["inner_steps"] or 0}
    for x in D_MARKERS:
        rec[f"{x}_D"] = meta["markers_total"][x]
    rec["meanings_C"] = len(m)
    for f in M_FATES:
        rec[f"m_{f}_C"] = sum(1 for r in m if r["final"] == f)
    rec["claims_C"] = len(c)
    lcols = [k for k in rows[0].keys() if k[:1] == "L" and k[1:].isdigit()]
    last = lcols[-1]
    for f in C_FATES:  # claims are counted at the run's last link, where its own last word sits
        rec[f"c_{f}_C"] = sum(1 for r in c if r[last] == f)
    rec["c_after_commit_C"] = sum(1 for r in c if r["final"] == "·")
    for v in ["yes", "no", "unknown"]:
        rec[f"c_correct_{v}_C"] = sum(1 for r in c if r["correct"] == v)
    for s in SITES:
        rec[f"first_loss_{s}_C"] = sum(1 for r in m + c if r["site"] == s)
    rec["units_with_loss_C"] = sum(1 for r in m + c if r["first_lost"])
    text = open(os.path.join(root, t, "reading.md"), encoding="utf-8").read()
    ev = events(text)
    for kind_, pre in (("meaning", "M"), ("claim", "C")):
        for s_ in SITES:
            rec[f"ev_{kind_}_{s_}_C"] = sum(1 for e in ev if e[1][0] == pre and e[3] == s_)
        rec[f"ev_{kind_}_C"] = sum(1 for e in ev if e[1][0] == pre)
    rec["links_with_loss_C"] = len({e[0] for e in ev})
    rec["events_at_L01_C"] = sum(1 for e in ev if e[0] == "L01")
    zeros = {k for k, v in meta["mast_annotation"].items() if v == 0}
    rec["mast_zero_codes"] = len(zeros)
    rec["zero_codes_set_here_C"], rec["zero_codes_partly_C"] = zero_codes_set(text, zeros)
    lc = [k for k in rows[0].keys() if k[:1] == "L" and k[1:].isdigit()]
    ci = lc.index(rec["commit"]) if rec["commit"] in lc else len(lc) - 1
    rec["c_status_changed_after_commit_C"] = sum(
        1 for r in c if any(r[lc[i]] != r[lc[i - 1]] and r[lc[i]] in ("softened", "hardened", "dropped", "inverted") for i in range(ci + 1, len(lc))))
    rec["c_dropped_any_C"] = sum(1 for r in c if "dropped" in [r[x] for x in lc])
    rec["c_dropped_any_correct_C"] = sum(1 for r in c if "dropped" in [r[x] for x in lc] and r["correct"] == "yes")
    ls = LINE_S.search(text)
    rec["loss_events_C"] = int(ls.group(1))
    for s, v in zip(SITES, ls.groups()[1:]):
        rec[f"events_{s}_C"] = int(v)
    mast_set = sum(1 for v in meta["mast_annotation"].values() if v == 1)
    rec["mast_codes_set"] = mast_set
    rec["mast_seen_here_C"] = int(k) if k else ""
    rec["losses_outside_mast_C"] = int(j) if j else ""
    rec["mast_overall_C"] = mast[0]["type"] if mast else ""
    if n and int(n) != mast_set:
        print(f"warning: {t}: reader's n={n} but the annotation sets {mast_set} codes", file=sys.stderr)
    return rec


def total(recs, name):
    out = {"trace": name, "n_traces": len(recs), "row": "", "shape": "", "framework": "", "model": "", "benchmark": "", "commit": ""}
    for key in recs[0]:
        if key.endswith(("_D", "_C")) or key in ("mast_codes_set", "mast_zero_codes"):
            vals = [r[key] for r in recs if isinstance(r[key], int)]
            out[key] = sum(vals) if vals else ""
    out["mast_overall_C"] = ", ".join(f"{w} {sum(1 for r in recs if r['mast_overall_C'] == w)}"
                                      for w in ["agree", "partly", "disagree"])
    return out


def main():
    root = sys.argv[1]
    recs = [read_trace(root, t) for t in trace_dirs(root)]
    shapes = ["line", "star", "two-agent chat"]
    groups = [total([r for r in recs if r["shape"] == s], f"{s}: {sum(1 for r in recs if r['shape'] == s)} traces") for s in shapes]
    tot = total(recs, f"all: {len(recs)} traces")
    cols = list(recs[0].keys())
    with open(os.path.join(root, "counts.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in recs + groups + [tot]:
            w.writerow(r)

    def frac(a, n):
        return f"{a} of {n}"

    L = []
    L.append("# Ten MAST-Data traces: the counts (task-as-stated proxy)\n")
    L.append("[C] read by Opus 5.5 (claude-opus-5-5) on the night of 2026-10-30 to 31, one model instance per two runs, no second rater; [D] counted by `build/extract.py` on 2026-10-31; this table built by `build/tables.py`. Data: MAST-Data, CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), changes marked in `README.md`.\n")
    L.append(f"Ten of MAST-Data's 1,642 traces, chosen by the rule in `README.md`; counts only, every count with its denominator; no rate is computed, because ten chosen traces estimate nothing about the 1,642. "
             "Tags: [D] counted by the scripts in `build/` from the scrubbed links, no model; [C] one run, read by a model, no second rater, reconciled against the task-as-stated proxy written before the run was read; "
             "MAST's label is the dataset's own annotation, made by an LLM judge (dataset card: \"Annotations are produced by an LLM judge, not by human labelling.\"). Built by `build/tables.py` from each trace's `links.jsonl` and `fates.csv`.\n")
    L.append("## 1. Links and status markers, by script, independent of the task-as-stated proxy [D]\n")
    L.append("| trace | shape | framework (model) | links | roles | sentences | hedged | not found | strengthened | sourced | dated |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in recs:
        L.append(f"| {r['trace']} | {r['shape']} | {r['framework']} ({r['model']}) | {r['links_D']} | {r['roles_D']} | {r['sentences_D']} | "
                 + " | ".join(frac(r[f'{x}_D'], r['sentences_D']) for x in D_MARKERS[1:]) + " |")
    for g in groups + [tot]:
        L.append(f"| **{g['trace']}** | | | {g['links_D']} | | {g['sentences_D']} | "
                 + " | ".join(frac(g[f'{x}_D'], g['sentences_D']) for x in D_MARKERS[1:]) + " |")
    L.append("\nA sentence is counted once per marker class it carries (the claim-ledger lexicon; `README.md`, \"The deterministic tier\"). HyperAgent's inner steps inside a child agent are not links: "
             + ", ".join(f"{r['trace']} {r['inner_steps_D']}" for r in recs if r['inner_steps_D']) + " [D].\n")
    L.append("## 2. The order's meanings at the commit (task-as-stated proxy) [C]\n")
    L.append("| trace | commit | meanings | intact | narrowed | substituted | absent | restored |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in recs + groups + [tot]:
        b = "**" if r in groups or r is tot else ""
        L.append(f"| {b}{r['trace']}{b} | {r['commit']} | {r['meanings_C']} | " + " | ".join(frac(r[f'm_{f}_C'], r['meanings_C']) for f in M_FATES) + " |")
    two = [("t01-chatdev-checkers", "M5"), ("t02-metagpt-checkers", "M5"), ("t05-hyperagent-xarray-4493", "M7")]  # each trace file, section 6
    lost_final = {"narrowed", "substituted", "absent"}
    ok = all(any(r["unit"] == u and r["final"] in lost_final for r in csv.DictReader(open(os.path.join(root, t, "fates.csv"), newline="", encoding="utf-8"))) for t, u in two)
    lost = sum(tot[f"m_{f}_C"] for f in ("narrowed", "substituted", "absent"))
    if ok:
        L.append(f"\nThree of the {lost} meanings lost at the commit depend on a choice between two readings that the proxy itself names (t01 M5 and t02 M5, \"standard capture\"; t05 M7, the constructor question); each trace file says which reading it counted (section 6). Read the other way, {lost - 3} of {tot['meanings_C']}. "
                 f"The {tot['meanings_C']} count meanings per run: two statements ran through two pipelines each, so the eight statements hold {tot['meanings_C'] - 15} distinct meanings.\n")
    L.append("\n## 3. Claims followed, their status at the run's last link (task-as-stated proxy) [C]\n")
    L.append("| trace | claims | kept | softened | hardened | dropped | inverted | still as made | made after the commit | status changed after the commit | correct: yes | no | unknown |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in recs + groups + [tot]:
        b = "**" if r in groups or r is tot else ""
        L.append(f"| {b}{r['trace']}{b} | {r['claims_C']} | " + " | ".join(frac(r[f'c_{f}_C'], r['claims_C']) for f in C_FATES) + " | "
                 + f"{frac(r['c_after_commit_C'], r['claims_C'])} | {frac(r['c_status_changed_after_commit_C'], r['claims_C'])} | "
                 + " | ".join(frac(r[f'c_correct_{v}_C'], r['claims_C']) for v in ["yes", "no", "unknown"]) + " |")
    L.append("\nClaims are counted at the last link of the run, where the run's own last word sits; each trace file's section 3 counts them at the commit. The two differ where a claim is made after the commit (column 9) or its status changes after it (column 10: a softening, hardening, dropping or inversion at a link after the commit). \"Still as made\": a claim in the state it was born in, either born at the last link or never carried on to a link that relies on it. \"Correct\" is judged by the run's own evidence (execution output, the problem's data; for the GitHub issues also the fix the project merged, which the system never saw).\n")
    L.append("\n## 4. Where the first loss of each unit sat, and MAST's label (task-as-stated proxy) [C]\n")
    L.append("| trace | units (meanings + claims) | units with a loss | design | source | seam | sink | MAST codes set, of 14 per trace (their judge) | of them seen here | loss events here under no set code | codes left at 0 that this reading would set | MAST label and this reading |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in recs + groups + [tot]:
        b = "**" if r in groups or r is tot else ""
        units = r['meanings_C'] + r['claims_C']
        L.append(f"| {b}{r['trace']}{b} | {units} | {frac(r['units_with_loss_C'], units)} | "
                 + " | ".join(frac(r[f'first_loss_{s}_C'], r['units_with_loss_C']) for s in SITES) + " | "
                 f"{r['mast_codes_set']} of {14 * r['n_traces']} | {frac(r['mast_seen_here_C'], r['mast_codes_set']) if r['mast_seen_here_C'] != '' else ''} | "
                 f"{frac(r['losses_outside_mast_C'], r['loss_events_C'])} | {frac(r['zero_codes_set_here_C'], r['mast_zero_codes'])} | {r['mast_overall_C']} |")
    L.append("\nA unit's first loss is the first link where a meaning left `intact` or a claim's status changed; its site is one of design, source, seam, sink (`README.md`, \"Method\"). Later losses of the same unit are described in its trace file, not counted here. "
             "\"MAST label and this reading\" is agree when every code MAST set is seen here and no loss found here falls outside them; disagree when none of them is seen, or MAST set none and a loss is found; partly otherwise.\n")
    L.append("\n## 5. Every loss event, by site, as each trace file lists it (task-as-stated proxy) [C]\n")
    L.append("| trace | loss events | at links | meaning losses: design | source | seam | sink | claim changes: design | source | seam | sink |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in recs + groups + [tot]:
        b = "**" if r in groups or r is tot else ""
        L.append(f"| {b}{r['trace']}{b} | {r['loss_events_C']} | {frac(r['links_with_loss_C'], r['links_D'])} | "
                 + " | ".join(frac(r[f'ev_meaning_{s}_C'], r['ev_meaning_C']) for s in SITES) + " | "
                 + " | ".join(frac(r[f'ev_claim_{s}_C'], r['ev_claim_C']) for s in SITES) + " |")
    L.append(("\nA unit can lose more than once (narrowed, then absent; dropped, then hardened); section 4 counts each unit's first loss, this section every loss, each with the site its trace file gives (section 4 of each `reading.md`). One event at one link is counted once for each meaning or claim it touches, so a single decision can count several times (t04 L01: 5 meanings; t05 L01: 4); \"at links\" counts the distinct links that carry a loss. At L01, the first link after the order: line {g0}, star {g1}, two-agent chat {g2} loss events (in the chat runs L01 is the solver's first answer). Three of the ten seam events are one file-writing step of the framework that stored a shell command as the program's main file (t01 L08); the reader filed them as seam and noted that design is arguable.\n").format(g0=frac(groups[0]["events_at_L01_C"], groups[0]["loss_events_C"]), g1=frac(groups[1]["events_at_L01_C"], groups[1]["loss_events_C"]), g2=frac(groups[2]["events_at_L01_C"], groups[2]["loss_events_C"])))
    # section 6: claims, correctness against status (all ten traces pooled)
    claims = []
    for t in trace_dirs(root):
        rows = [r for r in csv.DictReader(open(os.path.join(root, t, "fates.csv"), newline="", encoding="utf-8")) if r["kind"] == "claim"]
        if rows:
            last = [k for k in rows[0] if k[:1] == "L" and k[1:].isdigit()][-1]
            claims += [(r["type"], r["correct"], "unchanged" if r[last] in ("kept", "made") else r[last]) for r in rows]
    nc = len(claims)
    L.append("\n## 6. Claims: correct by the run's own evidence, against what happened to their status (all ten, pooled; task-as-stated proxy) [C]\n")
    L.append("| correct by the run's own evidence | claims | status unchanged at the last link | hardened | softened | dropped | inverted |")
    L.append("|---|---|---|---|---|---|---|")
    for v in ["no", "yes", "unknown"]:
        sub = [c for c in claims if c[1] == v]
        L.append(f"| {v} | {frac(len(sub), nc)} | " + " | ".join(frac(sum(1 for c in sub if c[2] == st), len(sub)) for st in ["unchanged", "hardened", "softened", "dropped", "inverted"]) + " |")
    L.append("\n| marker at birth | claims | correct: yes | no | unknown |")
    L.append("|---|---|---|---|---|")
    for b in ["flat", "hedged", "strengthened"]:
        sub = [c for c in claims if c[0] == b]
        L.append(f"| {b} | {frac(len(sub), nc)} | " + " | ".join(frac(sum(1 for c in sub if c[1] == v), len(sub)) for v in ["yes", "no", "unknown"]) + " |")
    da = sum(r["c_dropped_any_C"] for r in recs); dy = sum(r["c_dropped_any_correct_C"] for r in recs)
    L.append(f"\nClaims dropped at some link, whatever their last state: {frac(da, nc)}; of them correct by the run's own evidence: {frac(dy, da)}.")
    L.append("\nThe claims are the ones each reader chose to follow: at most eight per run, those a later step relied on or that reached the commit or a decision. These counts describe those 49 claims, not claims in general. \"Status unchanged\" is kept, or still as made, at the last link.\n")
    open(os.path.join(root, "counts.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"wrote counts.csv and counts.md for {len(recs)} traces")


if __name__ == "__main__":
    main()
