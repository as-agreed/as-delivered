#!/usr/bin/env python3
"""cut_replay.py: cut, and restore, the files of a replay bundle by the collection's standard (build/cut.py): no
third-party text in the bundle, each cut text kept as its sha256 and its length, and the place where it sits in
the texts rebuilt from the public row. Standard library only, no model, nothing fetched.

    python3 -I -B cut_replay.py restore <entry> <runs> <out>
    python3 -I -B cut_replay.py make <stored> <ledgers> <runs> <entry>     (the authors' step)

<runs> is what convert_mast.py wrote from the public rows: <runs>/<run>/links.jsonl and
<runs>/_scratch/<run>/trace-scrubbed.txt. `restore` writes into <out>/<run>/ each file of <entry>/<run>/ as it was
before the cut, and <out>/hand-check.md; it checks every cut text and every whole file against its sha256 in
cuts.jsonl, and checks that the rebuilt links.jsonl has its sha256 and cuts to the public one byte for byte. It
prints one line per run, each file and "matches" or "DIFFERS". Exit 1 on any mismatch.

What `make` cuts, in each run folder:
  links.jsonl          every link's text, by build/cut.py: the record keeps "chars" and gains "text_sha256"
  commitments.json, reads.jsonl, second-reads.jsonl, ledger.jsonl
                       a string under the key "quote", or under "quotes", is cut whole when it is found in the run's
                       texts (its links, its scrubbed trajectory); in every other string, each span of 4 or more words
                       found there is cut, verbatim or with other whitespace between its words (then the cut keeps that
                       whitespace); shorter spans are words, not texts, and stay
In the entry folder:
  hand-check.md        each quoted span of 4 or more words found in the runs' texts (build/cut.py's rule for a .md)
A cut text is printed "[cut <chars> chars, sha256 <first 12>]", as build/cut.py prints it.
"""
import hashlib, importlib.util, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUN_FILES = ("commitments.json", "reads.jsonl", "second-reads.jsonl", "ledger.jsonl")
MARK = re.compile(r"\[cut (\d+) chars, sha256 ([0-9a-f]{12})\]")
WORDS = re.compile(r"\S+")
PUNCT = "\"'`*()[]{}<>,.;:!?#"


def _collection_cut():
    """build/cut.py of the collection: beside this folder's parent as convert_mast.py expects its extractor
    (../public-readings/mast/build/), or in the collection tree (../../build/)."""
    for p in (os.path.join(HERE, "..", "public-readings", "mast", "build", "cut.py"),
              os.path.join(HERE, "..", "..", "build", "cut.py")):
        if os.path.exists(p):
            spec = importlib.util.spec_from_file_location("collection_cut", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    sys.exit("build/cut.py of the collection is not found")


CUT = _collection_cut()
sha = CUT.sha


def runs_in(folder):
    return sorted(n for n in os.listdir(folder) if os.path.isdir(os.path.join(folder, n)) and not n.startswith(("_", ".")))


def sources(runs, run):
    return CUT.sources(os.path.join(runs, run), os.path.join(runs, "_scratch", run))


# ---------- the forms the files are written in (each checked to round-trip before it is cut) ----------
def load(text, form):
    if form == "json":
        return json.loads(text)
    return [json.loads(x) for x in text.split("\n") if x]


def dump(obj, form):
    if form == "json":
        return json.dumps(obj, ensure_ascii=False, indent=1)
    return "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in obj)


def form_of(name):
    return "json" if name.endswith(".json") else "jsonl"


# ---------- make ----------
def bare(word):
    """A word without the marks around it, so that "grid" in a string meets "grid." in the run's text; the span is
    then checked against the text itself."""
    return word.strip(PUNCT) or word


class Index:
    """The run's texts, and the 4-word sequences in them, to find the spans of a string that are third-party text."""

    def __init__(self, src):
        self.src, self.sh, self.memo = src, set(), {}
        for t in src.values():
            w = [bare(x) for x in t.split()]
            self.sh.update(zip(w, w[1:], w[2:], w[3:]))

    def find(self, s):
        for name, t in self.src.items():
            i = t.find(s)
            if i >= 0:
                return {"src": name, "from": i, "chars": len(s)}
        return None

    def find_loose(self, s):
        """s found with other whitespace between its words (a line of code whose spaces a sentence splitter
        collapsed): its place, and the whitespace of s, which is all `restore` needs to give s back."""
        rx = re.compile(r"\s+".join(map(re.escape, s.split())))
        for name, t in self.src.items():
            m = rx.search(t)
            if m:
                return {"src": name, "from": m.start(), "chars": m.end() - m.start(), "ws": re.findall(r"\s+", s)}
        return None

    def spans(self, s):
        """Each span of 4 or more words of s found in the texts, verbatim or with other whitespace between its words,
        longest first from the left."""
        if s in self.memo:
            return self.memo[s]
        toks = [(m.start(), m.end(), m.group()) for m in WORDS.finditer(s)]
        keys = [bare(t[2]) for t in toks]
        out, i = [], 0
        while i + 4 <= len(toks):
            if tuple(keys[i:i + 4]) not in self.sh:
                i += 1
                continue
            j = i + 4
            while j < len(toks) and tuple(keys[j - 3:j + 1]) in self.sh:
                j += 1
            w = toks[i][2]
            a = toks[i][0] + (len(w) - len(w.lstrip(PUNCT)) if w.strip(PUNCT) else 0)  # from the first word itself

            def ends(k):
                """The span to the end of word k, with the marks after it or without them, as found in the texts."""
                last = toks[k - 1]
                for b in (last[1], last[1] - (len(last[2]) - len(last[2].rstrip(PUNCT)) if last[2].strip(PUNCT) else 0)):
                    loc = b > a and (self.find(s[a:b]) or self.find_loose(s[a:b]))
                    if loc:
                        return b, loc
                return None
            lo, hi, best = i + 4, j, None  # a part of a span found is found too: search the longest
            while lo <= hi:
                k = (lo + hi) // 2
                got = ends(k)
                if got:
                    best, lo = (k,) + got, k + 1
                else:
                    hi = k - 1
            if best:
                out.append((a, best[1], best[2]))
                i = best[0]
            else:
                i += 1
        self.memo[s] = out
        return out


def cut_value(x, idx, texts, key=None, parent=None):
    if isinstance(x, dict):
        return {k: cut_value(v, idx, texts, k, key) for k, v in x.items()}
    if isinstance(x, list):
        return [cut_value(v, idx, texts, key, parent) for v in x]
    if not isinstance(x, str) or not x:
        return x

    def mark(s, loc):
        texts.setdefault(sha(s), dict(loc, text_sha256=sha(s), text_chars=len(s)))
        return CUT.marker(s)
    if key == "quote" or parent == "quotes":
        loc = idx.find(x) or CUT.locate(x, idx.src)
        if loc:
            return mark(x, loc)
    out, at = [], 0
    for a, b, loc in idx.spans(x):
        out += [x[at:a], mark(x[a:b], loc)]
        at = b
    return "".join(out) + x[at:]


def count_marks(obj):
    if isinstance(obj, dict):
        return sum(count_marks(v) for v in obj.values())
    if isinstance(obj, list):
        return sum(count_marks(v) for v in obj)
    return len(MARK.findall(obj)) if isinstance(obj, str) else 0


def make_run(paths, runs, run, out):
    """paths: file name -> the full file the replay made or read. Writes the cut files and cuts.jsonl into out."""
    src = sources(runs, run)
    idx, texts, manifest = Index(src), {}, []
    os.makedirs(out, exist_ok=True)
    full = os.path.join(runs, run, "links.jsonl")
    with open(os.path.join(out, "links.jsonl"), "w", encoding="utf-8") as f:
        f.write(CUT.cut_links(full))
    manifest.append({"file": "links.jsonl", "original_sha256": hashlib.sha256(open(full, "rb").read()).hexdigest(),
                     "rebuild": "convert_mast.py (build/extract.py) from the public row", "cut_texts": sum(1 for k in src if k.startswith("L"))})
    for name in RUN_FILES:
        text = open(paths[name], encoding="utf-8", newline="").read()
        form = form_of(name)
        obj = load(text, form)
        if dump(obj, form) != text:
            sys.exit(f"{run}/{name}: the file does not round-trip as {form}; it cannot be cut and restored byte for byte")
        pub = dump(cut_value(obj, idx, texts), form)
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as f:
            f.write(pub)
        manifest.append({"file": name, "form": form, "original_sha256": sha(text), "public_sha256": sha(pub),
                         "cut_texts": count_marks(load(pub, form))})
    with open(os.path.join(out, "cuts.jsonl"), "w", encoding="utf-8") as f:
        for m in manifest:
            f.write(CUT.dumps(m) + "\n")
        for t in sorted(texts.values(), key=lambda t: (t["src"], t["from"], t["text_sha256"])):
            f.write(CUT.dumps(t) + "\n")
    return {"run": run, "cut_texts": sum(m["cut_texts"] for m in manifest), "distinct_texts": len(texts)}


def all_sources(runs):
    return {f"{run}/{k}": v for run in runs_in(runs) for k, v in sources(runs, run).items()}


def make_hand(hand_md, runs, entry):
    src = all_sources(runs)
    text = open(hand_md, encoding="utf-8", newline="").read()
    unfound = []
    pub, rec = CUT.make_file("hand-check.md", text, src, unfound)
    with open(os.path.join(entry, "hand-check.md"), "w", encoding="utf-8", newline="") as f:
        f.write(pub)
    cuts = sum(1 for r in rec if "word" not in r["orig"])
    with open(os.path.join(entry, "cuts.jsonl"), "w", encoding="utf-8") as f:
        f.write(CUT.dumps({"file": "hand-check.md", "original_sha256": sha(text), "public_sha256": sha(pub),
                           "cut_texts": cuts, "words_changed": len(rec) - cuts, "edits": rec}) + "\n")
    for name, s in unfound:
        print("not found, kept: %s %r" % (name, s[:90]), file=sys.stderr)
    return {"file": "hand-check.md", "cut_texts": cuts, "kept_unfound": len(unfound)}


def make(stored, ledgers, runs, entry):
    """stored: the bench's results folder (<run>/commitments.json, reads.jsonl, second-reads.jsonl) with the hand
    check extract as hand-check.md; ledgers: the replay's out folder (<run>/tier1/report/ledger.jsonl)."""
    for run in runs_in(runs):
        paths = {n: os.path.join(stored, run, n) for n in RUN_FILES[:3]}
        paths["ledger.jsonl"] = os.path.join(ledgers, run, "tier1", "report", "ledger.jsonl")
        print(json.dumps(make_run(paths, runs, run, os.path.join(entry, run))))
    print(json.dumps(make_hand(os.path.join(stored, "hand-check.md"), runs, entry)))


# ---------- restore ----------
def original(t, src):
    """A cut text from its place in the rebuilt texts (build/cut.py), or from its words there and its own whitespace."""
    if "ws" in t:
        words = src[t["src"]][t["from"]:t["from"] + t["chars"]].split()
        return "".join(w + g for w, g in zip(words, t["ws"] + [""]))
    return CUT.original_of(t, src)


def table(entry_run):
    out = {}
    for line in open(os.path.join(entry_run, "cuts.jsonl"), encoding="utf-8"):
        m = json.loads(line)
        if "text_sha256" in m:
            out[(m["text_chars"], m["text_sha256"][:12])] = m
    return out


def texts_of(entry_run, runs, run):
    """Every text cut in a run folder, rebuilt from the public row and checked: {text: its marker}."""
    src, out = sources(runs, run), {}
    for t in table(entry_run).values():
        s = original(t, src)
        if sha(s) != t["text_sha256"]:
            raise ValueError(f"{run}: the text at {t['src']} {t['from']} does not match its sha256")
        out[s] = CUT.marker(s)
    return out


def put_back(x, tab, src, bad):
    if isinstance(x, dict):
        return {k: put_back(v, tab, src, bad) for k, v in x.items()}
    if isinstance(x, list):
        return [put_back(v, tab, src, bad) for v in x]
    if not isinstance(x, str):
        return x

    def one(m):
        t = tab.get((int(m.group(1)), m.group(2)))
        s = original(t, src) if t else None
        if s is None or sha(s) != t["text_sha256"]:
            bad.append(m.group(0))
            return m.group(0)
        return s
    return MARK.sub(one, x)


def restore_run(entry_run, runs, run, out):
    """Puts back every text of a run folder; one line: each file and whether it matches its sha256 of the bundle."""
    src, tab, said = sources(runs, run), table(entry_run), []
    os.makedirs(out, exist_ok=True)
    for line in open(os.path.join(entry_run, "cuts.jsonl"), encoding="utf-8"):
        m = json.loads(line)
        if "file" not in m:
            continue
        if m["file"] == "links.jsonl":
            full = os.path.join(runs, run, "links.jsonl")
            ok = hashlib.sha256(open(full, "rb").read()).hexdigest() == m["original_sha256"] and \
                CUT.cut_links(full) == open(os.path.join(entry_run, "links.jsonl"), encoding="utf-8").read()
            said.append(("links.jsonl", ok))
            continue
        missing = []
        obj = put_back(load(open(os.path.join(entry_run, m["file"]), encoding="utf-8", newline="").read(), m["form"]), tab, src, missing)
        text = dump(obj, m["form"])
        with open(os.path.join(out, m["file"]), "w", encoding="utf-8", newline="") as f:
            f.write(text)
        said.append((m["file"], sha(text) == m["original_sha256"] and not missing))
    print("%s: %s" % (run, "; ".join("%s %s" % (n, "matches" if ok else "DIFFERS") for n, ok in said)))
    return sum(1 for _, ok in said if not ok)


def restore_hand(entry, runs, out):
    src, bad = all_sources(runs), 0
    for line in open(os.path.join(entry, "cuts.jsonl"), encoding="utf-8"):
        m = json.loads(line)
        text = open(os.path.join(entry, m["file"]), encoding="utf-8", newline="").read()
        for e in sorted(m["edits"], key=lambda e: e["at"], reverse=True):
            o = CUT.original_of(e["orig"], src)
            if "sha256" in e["orig"] and sha(o) != e["orig"]["sha256"]:
                print("  %s: the cut text at %d does not match its sha256" % (m["file"], e["at"]))
                bad += 1
            text = text[:e["at"]] + o + text[e["at"] + e["len"]:]
        with open(os.path.join(out, m["file"]), "w", encoding="utf-8", newline="") as f:
            f.write(text)
        ok = sha(text) == m["original_sha256"]
        bad += not ok
        print("%s: %s" % (m["file"], "matches" if ok else "DIFFERS"))
    return bad


def restore(entry, runs, out):
    bad = 0
    for run in runs_in(entry):
        bad += restore_run(os.path.join(entry, run), runs, run, os.path.join(out, run))
    bad += restore_hand(entry, runs, out)
    print("restore: %s" % ("every cut text put back; each file matches its sha256 before the cut" if not bad else "A FILE DIFFERS"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["restore"] and len(a) == 4:
        restore(*a[1:])
    elif a[:1] == ["make"] and len(a) == 5:
        make(*a[1:])
    else:
        sys.exit(__doc__)
