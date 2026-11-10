#!/usr/bin/env python3
"""Make, and check, the public copy of a MAST reading: no third-party text in it, every cut text kept as
its sha256 and its length, and a script that puts each one back from the public source. Standard library
only, no model, nothing fetched.

    python3 -I -B cut.py links <links.jsonl>                             print the cut links.jsonl
    python3 -I -B cut.py restore <public-trace> <rebuilt-trace> <scratch> <out>
    python3 -I -B cut.py make <original-trace> <rebuilt-trace> <scratch> <out>    (the authors' step)

<rebuilt-trace> and <scratch> are what extract.py wrote from the public row. `restore` writes into <out>
the files as they were before the cut, checks each cut text and each whole file against the sha256 in
cuts.jsonl, and checks that the rebuilt links.jsonl cuts to the public one byte for byte. Exit 1 on any
mismatch.

What is cut (the rule of `make`, applied to every file of the reading):
  links.jsonl   every link's text; the record keeps "chars" and gains "text_sha256"
  as-stated.md  the task statement, quoted whole under "Task statement (verbatim)"
  any .md       every quoted span (in double quotes or in code font) of 4 or more words that is found in
                the run's texts (its links, its scrubbed trajectory, the reference block), whole, in parts
                around " ... ", or without the source's code marks; shorter spans are words, not texts,
                and stay; so do the names of MAST's failure modes and quotes of the proxy
Also changed, and put back by `restore`: the word "meaning" of the 2026-10-31 files is printed "term"
(the project's vocabulary since 2026-10-31), in every file except inside a quoted span.
"""
import hashlib, json, os, re, sys

QUOTE = re.compile(r'"([^"\n]+)"')
CODE = re.compile(r"`([^`\n]+)`")
WORD = re.compile(r"(?<![A-Za-z])([Mm])eaning(s?)(?![a-z])")
ELLIPSIS = re.compile(r"(\s*(?:\.\.\.|…)\s*)")
FILES = ("as-stated.md", "reading.md", "fates.csv", "flow.svg", "counts.md", "counts.csv")


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def dumps(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def cut_links(path):
    out = []
    for i, line in enumerate(open(path, encoding="utf-8").read().splitlines()):
        d = json.loads(line)
        if i == 0:
            d["cut"] = "each link's text is cut; text_sha256 and chars stay; build/extract.py rebuilds it from the public row"
        else:
            d["text_sha256"] = sha(d.pop("text"))
        out.append(dumps(d) + "\n")
    return "".join(out)


def sources(rebuilt, scratch):
    src = {}
    p = os.path.join(rebuilt, "links.jsonl")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8").read().splitlines()[1:]:
            d = json.loads(line)
            src["L%02d" % d["n"]] = d["text"]
    for name, f in (("trajectory", "trace-scrubbed.txt"), ("reference", "reference-not-seen-by-system.txt")):
        p = os.path.join(scratch or "", f)
        if scratch and os.path.exists(p):
            src[name] = open(p, encoding="utf-8").read()
    return src


def locate(s, src):
    for name, text in src.items():
        i = text.find(s)
        if i >= 0:
            return {"src": name, "from": i, "chars": len(s)}
    loose = re.compile("`?".join(map(re.escape, s)))  # a quote that drops the source's code marks
    for name, text in src.items():
        m = loose.search(text)
        if m and m.group(0).replace("`", "") == s:
            return {"src": name, "from": m.start(), "chars": len(m.group(0)), "drop": "`"}
    return None


def locate_parts(s, src):
    whole = locate(s, src)
    if whole:
        return whole
    bits = ELLIPSIS.split(s)
    if len(bits) < 3:
        return None
    parts = []
    for k, b in enumerate(bits):
        if k % 2:
            parts.append(b)
        elif b:
            loc = locate(b, src)
            if not loc:
                return None
            parts.append(loc)
    return {"parts": parts}


def original_of(o, src):
    if "word" in o:
        return o["word"]
    if "parts" in o:
        return "".join(p if isinstance(p, str) else original_of(p, src) for p in o["parts"])
    text = src[o["src"]]
    if o.get("form") == "quote-block":
        return "\n".join(("> " + l) if l else ">" for l in text.split("\n"))
    return text[o["from"]:o["from"] + o["chars"]].replace(o.get("drop") or "\0", "")


def marker(s, what="cut"):
    return "[%s %d chars, sha256 %s]" % (what, len(s), sha(s)[:12])


def make_file(name, text, src, unfound):
    """Edits as (start, end, public text, how to get the original back), on the original text."""
    edits, protected = [], []
    if name == "as-stated.md" and "L00" in src:
        head = "## Task statement (verbatim)\n"
        block = original_of({"src": "L00", "form": "quote-block"}, src)
        i = text.find(head)
        if i < 0 or text[i + len(head):i + len(head) + len(block)] != block:
            sys.exit("as-stated.md: the verbatim block is not the task statement of L00")
        a = i + len(head)
        edits.append((a, a + len(block), "> [cut: the task statement, which is the text of link L00 in links.jsonl"
                      " (%d chars, sha256 %s), quoted here line by line]" % (len(src["L00"]), sha(src["L00"])), {"src": "L00", "form": "quote-block", "sha256": sha(block), "text_chars": len(block)}))
        protected.append((a, a + len(block)))
    if name.endswith(".md"):
        spans = [(m.start(1), m.end(1)) for m in QUOTE.finditer(text)]
        spans += [(m.start(1), m.end(1)) for m in CODE.finditer(text)
                  if not any(a - 1 <= m.start() < b + 1 for a, b in spans)]
        for a, b in sorted(spans):
            if any(x <= a < y for x, y in protected):
                continue
            protected.append((a, b))
            s = text[a:b]
            if len(s.split()) < 4:
                continue
            loc = locate_parts(s, src)
            if loc is None:
                unfound.append((name, s))
                continue
            loc.update({"sha256": sha(s), "text_chars": len(s)})
            edits.append((a, b, marker(s), loc))
    for m in WORD.finditer(text):
        if not any(x <= m.start() < y for x, y in protected):
            edits.append((m.start(), m.end(), ("T" if m.group(1) == "M" else "t") + "erm" + m.group(2), {"word": m.group(0)}))
    edits.sort()
    out, at, pos, rec = [], 0, 0, []
    for a, b, pub, o in edits:
        out.append(text[at:a]); pos += a - at
        rec.append({"at": pos, "len": len(pub), "orig": o})
        out.append(pub); pos += len(pub); at = b
    out.append(text[at:])
    return "".join(out), rec


def make(orig, rebuilt, scratch, out):
    src = sources(rebuilt, scratch)
    os.makedirs(out, exist_ok=True)
    manifest, unfound, ncut = [], [], 0
    if os.path.exists(os.path.join(rebuilt, "links.jsonl")):
        full = os.path.join(rebuilt, "links.jsonl")
        if open(full, "rb").read() != open(os.path.join(orig, "links.jsonl"), "rb").read():
            sys.exit("the rebuilt links.jsonl differs from the original")
        open(os.path.join(out, "links.jsonl"), "w", encoding="utf-8").write(cut_links(full))
        manifest.append({"file": "links.jsonl", "original_sha256": hashlib.sha256(open(full, "rb").read()).hexdigest(),
                         "rebuild": "build/extract.py from the public row", "cut_texts": len(src) - sum(k in src for k in ("trajectory", "reference"))})
        ncut += manifest[-1]["cut_texts"]
    for name in FILES:
        p = os.path.join(orig, name)
        if not os.path.exists(p):
            continue
        text = open(p, encoding="utf-8", newline="").read()
        pub, rec = make_file(name, text, src, unfound)
        open(os.path.join(out, name), "w", encoding="utf-8", newline="").write(pub)
        cuts = sum(1 for r in rec if "word" not in r["orig"])
        ncut += cuts
        manifest.append({"file": name, "original_sha256": sha(text), "public_sha256": sha(pub), "cut_texts": cuts,
                         "words_changed": len(rec) - cuts, "edits": rec})
    with open(os.path.join(out, "cuts.jsonl"), "w", encoding="utf-8") as f:
        for m in manifest:
            f.write(dumps(m) + "\n")
    for name, s in unfound:
        print("not found, kept: %s %r" % (name, s[:90]), file=sys.stderr)
    print(json.dumps({"folder": os.path.basename(os.path.normpath(out)), "cut_texts": ncut, "kept_unfound": len(unfound)}))


def restore(public, rebuilt, scratch, out):
    src = sources(rebuilt, scratch)
    os.makedirs(out, exist_ok=True)
    bad = 0
    for line in open(os.path.join(public, "cuts.jsonl"), encoding="utf-8"):
        m = json.loads(line)
        if m["file"] == "links.jsonl":
            full = os.path.join(rebuilt, "links.jsonl")
            ok = hashlib.sha256(open(full, "rb").read()).hexdigest() == m["original_sha256"]
            same = cut_links(full) == open(os.path.join(public, "links.jsonl"), encoding="utf-8").read()
            print("links.jsonl: rebuilt sha256 %s; cuts to the public file %s" % ("matches" if ok else "DIFFERS", "byte for byte" if same else "WITH A DIFFERENCE"))
            bad += (not ok) + (not same)
            continue
        text = open(os.path.join(public, m["file"]), encoding="utf-8", newline="").read()
        for e in sorted(m["edits"], key=lambda e: e["at"], reverse=True):
            o = original_of(e["orig"], src)
            if "sha256" in e["orig"] and sha(o) != e["orig"]["sha256"]:
                print("%s: the cut text at %d does not match its sha256" % (m["file"], e["at"])); bad += 1
            text = text[:e["at"]] + o + text[e["at"] + e["len"]:]
        open(os.path.join(out, m["file"]), "w", encoding="utf-8", newline="").write(text)
        ok = sha(text) == m["original_sha256"]
        bad += not ok
        print("%s: %d texts put back; sha256 %s the original %s" % (m["file"], m["cut_texts"], "matches" if ok else "DIFFERS FROM", m["original_sha256"][:12]))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["links"] and len(a) == 2:
        sys.stdout.write(cut_links(a[1]))
    elif a[:1] == ["restore"] and len(a) == 5:
        restore(*a[1:])
    elif a[:1] == ["make"] and len(a) == 5:
        make(*a[1:])
    else:
        sys.exit(__doc__)
