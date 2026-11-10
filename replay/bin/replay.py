#!/usr/bin/env python3
"""replay.py: run the trace bench again on stored reads, with no model call, and check that it gives what the bundle
holds. The bench (bench.py, models.py, prompts.py, cards.py beside this file) runs unchanged on the as_agreed package
installed from PyPI; this file only answers each model prompt with the read stored for it.

    python3 -I -B replay.py <entry> <runs> <full> <out> [--write]

<entry>  the bundle's entry folder (one folder per run, seller-lines.md, hand-check.md)
<runs>   the runs convert_mast.py rebuilt from the public rows (<runs>/<run>/links.jsonl)
<full>   the bundle's files with their texts put back by cut_replay.py restore
<out>    a new folder for what the replay writes: chunk-1/ (the bench's own output), maps/, cards/

Reader 1 answers each link from <full>/<run>/reads.jsonl (matched by run, link and fields); reader 2 answers each
second-read prompt from <full>/<run>/second-reads.jsonl (matched by run and the prompt's sha256). The bench runs as
chunk 1 ran it: --drafter-version v1 --reader-version v2 --second-reader --second-rule d44, each record reused as
drafted (--records). Its clock reads the stored reads' date, so its rows carry the day the reads were made.

Per run it prints tier 1's verdicts on the reads, other than PRESERVED, and one line of checks: the report's lines
from the new ledger are the lines from the stored ledger, byte for byte; the reads it writes are the stored reads;
the map it draws (no values) is flow.svg; the card it composes, cut by the bundle's own cuts, is card.html. Exit 1 when one
fails. --write is the authors' step: it writes flow.svg and card.html into <entry> instead of checking them.
"""
import contextlib, html, io, json, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # the bench's modules; -I keeps every other folder off the path

import bench, cards, cut_replay, models  # noqa: E402

KINDS = ("finding", "proposal", "split")
ONE, TWO, DATES, NOW = {}, {}, {}, {"run": None}


def jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


class Stored(models.Caller):
    """Answers every prompt with the read stored for it; no model is called."""
    mode = "exchange"

    def __call__(self, prompt):
        q = models.request_of(prompt)
        if self.role == "reader2":
            book, key = TWO, (NOW["run"], models.sha(prompt))
        else:
            book, key = ONE, (NOW["run"], q.get("link"), tuple(f["field"] for f in q.get("fields", [])))
        if key not in book:
            raise SystemExit("replay: no stored read for %s at %s %s; the prompts or the rules are not chunk 1's"
                             % (self.role, NOW["run"], q.get("link")))
        self.version, answer, self.answered_at = book[key]
        return answer


def load_reads(full, runs):
    for run in runs:
        first = jsonl(os.path.join(full, run, "reads.jsonl"))
        for link in dict.fromkeys(g["link"] for g in first):
            gs = [g for g in first if g["link"] == link]
            ONE[(run, link, tuple(g["field"] for g in gs))] = (gs[0]["version"], json.dumps({"reads": gs}), None)
        by = {}
        for g in jsonl(os.path.join(full, run, "second-reads.jsonl")):
            by.setdefault(g["prompt_sha256"], []).append(g)
        for h, gs in by.items():
            TWO[(run, h)] = (gs[0]["version"], json.dumps({"reads": gs}), gs[0]["date"])
        DATES[run] = max((v[2] for k, v in TWO.items() if k[0] == run and v[2]), default=None)


def run_bench(runs, full, out):
    clock, inner = models.now, bench.bench_run

    def bench_run(name, *a, **k):
        NOW["run"] = name
        models.now = (lambda: DATES[name]) if DATES.get(name) else clock
        return inner(name, *a, **k)
    bench.bench_run = bench_run
    bench.load_lib = lambda path: None  # as_agreed is the installed package
    models.make_caller = lambda mode, role, model, exchange=None: Stored(role, model)
    os.makedirs(out, exist_ok=True)
    shutil.copy(os.path.join(full, "hand-check.md"), os.path.join(out, "hand-check.md"))
    with contextlib.redirect_stdout(io.StringIO()):
        return bench.main([runs, out, "--mode", "exchange", "--records", full, "--drafter-version", "v1",
                           "--reader-version", "v2", "--second-reader", "--second-rule", "d44"])


def report_lines(ledger):
    from as_agreed.report import build
    return build(jsonl(ledger), tempfile.mkdtemp()).unit_lines


def verdicts(lines):
    """Tier 1's verdicts on the readers' reads ("read at"), each with its link; PRESERVED left out."""
    out, at = [], ""
    for x in lines:
        at = at if x.startswith(" ") else x.split("#")[0]
        if "read at" in x and "PRESERVED" not in x:
            out.append(at + " " + " ".join(x.split()))
    return out


def cut_known(x, marks, long_first):
    """A string the bundle cuts, as the bundle prints it: whole, or each cut text of 4 or more words inside it."""
    if isinstance(x, dict):
        return {k: cut_known(v, marks, long_first) for k, v in x.items()}
    if isinstance(x, list):
        return [cut_known(v, marks, long_first) for v in x]
    if not isinstance(x, str):
        return x
    if x in marks:
        return marks[x]
    for t in long_first:
        if t in x:
            x = x.replace(t, marks[t])
    return x


def card_page(results, run, seller):
    """The run's cards of kind finding, proposal and split, each drawn by cards.py; the page head carries the run's
    result after the hand check and no tally (D-30)."""
    value = cards.business_value(seller, results)
    row = next(r for r in cards.load_rows(results) if r["run"] == run)
    view = cards.RunView(results, row, cards.hand_splits(os.path.join(results, "hand-check.md")), value)
    esc = html.escape
    head = ("<p class='tag'>%s · %s · result after the hand check: <b>%s</b> · drafter %s · reader 1 %s · reader 2 %s</p>"
            % (esc(run), esc(row.get("find", "")), esc((row.get("final") or {}).get("status", "")), esc(row.get("drafter", "")),
               esc(row.get("reader", "")), esc(row.get("second_reader", ""))))
    body = "".join(view.unit_card(u) for u in view.units if u["kind"] in KINDS) or \
        "<p class='note'>No unit of kind finding, proposal or split in this run.</p>"
    lede = ("One run's cards of kind finding, proposal and split, each drawn by cards.py, with the seller's lines on the "
            "card they name (D-54). " + cards.NOTE)
    return cards._page("Verdict cards: " + run, lede, "<section><h2>%s</h2>%s%s</section>" % (esc(run), head, body))


def public_view(entry, runs, run, results, out):
    """The results folder as the bundle shows it: the bench's rows cut by the bundle's own cuts, and the bundle's
    commitments.json, reads.jsonl and hand-check.md as they are."""
    marks = cut_replay.texts_of(os.path.join(entry, run), runs, run)
    long_first = sorted((t for t in marks if len(t.split()) >= 4), key=len, reverse=True)
    rows = [cut_known(r, marks, long_first) for r in cards.load_rows(results) if r["run"] == run]
    os.makedirs(os.path.join(out, run), exist_ok=True)
    with open(os.path.join(out, "rows.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    for name in ("commitments.json", "reads.jsonl"):
        shutil.copy(os.path.join(entry, run, name), os.path.join(out, run, name))
    shutil.copy(os.path.join(entry, "hand-check.md"), os.path.join(out, "hand-check.md"))
    return out


def same_file(a, b):
    return os.path.exists(a) and os.path.exists(b) and open(a, "rb").read() == open(b, "rb").read()


def main(argv):
    write = "--write" in argv
    argv = [a for a in argv if a != "--write"]
    if len(argv) != 4:
        sys.exit(__doc__)
    entry, runs, full, out = (os.path.abspath(a) for a in argv)
    import as_agreed
    from as_agreed.report import redraw
    print("Python %s; as_agreed %s" % (sys.version.split()[0], as_agreed.__version__))
    names = cut_replay.runs_in(full)
    load_reads(full, names)
    results = os.path.join(out, "chunk-1")  # cards.py finds the seller's lines by this folder's chunk number
    rc = run_bench(runs, full, results)
    rows = {r["run"]: r for r in cards.load_rows(results)}
    seller = os.path.join(entry, "seller-lines.md")
    bad = 0
    for run in names:
        row = rows.get(run) or {}
        ledger = os.path.join(results, run, "tier1", "report", "ledger.jsonl")
        new = report_lines(ledger)
        print(run)
        for line in verdicts(new):
            print("  " + line)
        checks = []
        stored = os.path.join(full, run, "ledger.jsonl")
        if os.path.exists(stored):
            checks.append(("verdict lines as the stored ledger's", new == report_lines(stored)))
        checks.append(("reads as stored", all(same_file(os.path.join(results, run, n), os.path.join(full, run, n))
                                              for n in ("reads.jsonl", "second-reads.jsonl"))))
        os.makedirs(os.path.join(out, "maps"), exist_ok=True)
        if write and not os.path.exists(os.path.join(entry, run, "cuts.jsonl")):
            print("  no cuts.jsonl yet: run cut_replay.py make on this replay's ledgers, then --write again")
            continue
        svg = redraw(ledger, os.path.join(out, "maps", run + ".svg"))  # the shareable map: no value; the cards carry them
        os.makedirs(os.path.join(out, "cards"), exist_ok=True)
        with open(os.path.join(out, "cards", run + ".html"), "w", encoding="utf-8") as f:
            f.write(card_page(results, run, seller))
        view = public_view(entry, runs, run, results, os.path.join(out, "public", run, "chunk-1"))
        card = card_page(view, run, seller)
        if write:
            shutil.copy(svg, os.path.join(entry, run, "flow.svg"))
            with open(os.path.join(entry, run, "card.html"), "w", encoding="utf-8") as f:
                f.write(card)
        else:
            checks.append(("map as flow.svg", same_file(svg, os.path.join(entry, run, "flow.svg"))))
            with open(os.path.join(entry, run, "card.html"), encoding="utf-8") as f:
                checks.append(("card as card.html", card == f.read()))
        bad += sum(1 for _, ok in checks if not ok)
        print("  result after the hand check: %s; %s" % ((row.get("final") or {}).get("status", "none"),
                                                         "; ".join("%s: %s" % (n, "yes" if ok else "NO") for n, ok in checks)))
    print("replay: bench exit %d; %s" % (rc, "every check passed" if not bad and rc == 0 else "A CHECK FAILED"))
    return 1 if bad or rc else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
