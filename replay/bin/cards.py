"""cards.py: one verdict card per loss in a bench results folder, for a person to read (the P0.4 reading format, D-51).

    python3 -I studies/trace-bench/cards.py <results_dir> <out.html> [--runs t02-x,t07-y] [--maps <dir>]

Reads <results_dir>/table.md (the "findings" column names each loss: class, field, link) and, per run,
commitments.json, reads.jsonl and second-reads.jsonl. Writes one self-contained HTML file. Standard library only.

Each card answers: what was agreed (the proxy's field and its quote from the task statement), what arrived (each
reader's value and quote at the link), at which step, and the status by D-44:
  FINDING        two readers (different models) both read the loss at 0.8 or above
  PENDING        the first reader read the loss at 0.8 or above; no second read exists at that link yet
  PROPOSAL       both readers read the loss, either below 0.8: for a hand read (tier 3), never a finding
  SPLIT          the readers disagree on whether the field arrived
Under the card: the field's path across every link of the run, both readers, confidence per link. The loss is drawn
red only at 0.8 or above; below that it is amber. --maps <dir> inlines <dir>/<run>.svg under the card: draw it with
as_agreed.report.redraw(ledger, svg, values=True) from the run's tier-1 ledger. This file draws nothing itself.

Chunk format (2026-11-05): when <results_dir>/rows.json exists it is read instead of table.md. A unit is one field at
one link: reader 1's and reader 2's class, value, confidence and quote, the D-44 kind rows.json gives it (finding,
proposal, split, one reader only, or none), and the hand verdict from hand-check.md's "Every split" table where one
exists. Default: one card per finding, grouped by run (--kinds finding,proposal,split widens it). --seeded: one card per
row of hand-check.md's seeded-rows section, its text verbatim, every unit it names (by field name and link, or by a
quote it shares with a reader), the field's path and the run map (--maps).

Business value (D-54, 2026-11-06): when the chunks.md block of this results folder's chunk (results/<date>-chunk-<n>)
carries a "Business value" sub-list, each card shows the seller's three lines (loss, what the hold would have done,
opportunity) of the entry that names its run, link and field; a seeded card also shows an entry that names its run
only. --chunks <path> points at another chunks.md.

    python3 -I cards.py results/2026-11-05-chunk-1 findings.html
    python3 -I cards.py results/2026-11-05-chunk-1 seeded.html --seeded --maps <dir of run.svg>
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import os
import re
import sys

THRESHOLD = 0.8
LOSS_CLASSES = "WEAKENED|DROPPED|NARROWED|WIDENED|STRENGTHENED|RECONDITIONED|REASSIGNED|RESCHEDULED|ADDED_UNPARENTED"
ENTRY = re.compile(r"(?P<cls>" + LOSS_CLASSES + r") `(?P<path>[^`]+)`: (?P<agreed>.*?) → (?P<arrived>\S+) at (?P<link>L\d+)")


def _jsonl(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _table(path: str) -> list:
    """Rows of table.md as dicts keyed by the header's first word(s), e.g. 'find', 'run', 'findings', 'unexpected'."""
    rows, header = [], None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("|") or line.startswith("|---"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if header is None and cells and cells[0] == "find":
                header = cells
                continue
            if header and len(cells) == len(header):
                rows.append(dict(zip(header, cells)))
    return rows


def _col(row: dict, prefix: str) -> str:
    for k, v in row.items():
        if k.startswith(prefix):
            return v
    return ""


def is_loss(r: dict | None) -> bool:
    return bool(r) and (r.get("status") == "not_carried" or (r.get("status") == "carried" and r.get("value") is False))


def is_kept(r: dict | None) -> bool:
    return bool(r) and r.get("status") == "carried" and r.get("value") is not False


def status(first: dict | None, second: dict | None) -> str:
    """D-44: a finding needs both readers at the threshold or above with the same loss."""
    if not is_loss(first) and not is_loss(second):
        return "NO LOSS"
    if second is None:
        return "PENDING" if is_loss(first) and first.get("confidence", 0) >= THRESHOLD else "PROPOSAL"
    if is_loss(first) and is_loss(second):
        both = min(first.get("confidence", 0), second.get("confidence", 0)) >= THRESHOLD
        return "FINDING" if both else "PROPOSAL"
    return "SPLIT"


STATUS_TEXT = {
    "FINDING": "Finding: both readers read the loss at 0.8 or above. A live run would be held before the commit.",
    "PENDING": "Pending the second reader: one reader read the loss at 0.8 or above, and D-44 needs two. Nothing is held yet.",
    "PROPOSAL": "Proposal: the readers agree on the loss below 0.8. A person reads it against the raw text (tier 3); it is never a finding.",
    "SPLIT": "Split: the readers disagree. A person reads it against the raw text before the row is final.",
    "NO LOSS": "No loss read at this link.",
}
STATUS_COLOUR = {"FINDING": "#c0392b", "PENDING": "#b9770e", "PROPOSAL": "#b9770e", "SPLIT": "#6c6c6c", "NO LOSS": "#2e8b57"}


def _agreed(commitment: dict, path: str) -> str:
    if path.startswith("acceptance_criteria."):
        cid = path.split(".", 1)[1]
        for x in commitment.get("acceptance_criteria") or []:
            if x.get("criterion_id") == cid:
                return x.get("text", "")
    if path.startswith("limit."):
        return f"{commitment.get('act', '')}: {path} {json.dumps((commitment.get('limit') or {}).get(path[6:]))}"
    return str(commitment.get(path, ""))


def _value(r: dict | None) -> str:
    if not r:
        return "no read"
    if r.get("status") == "not_addressed":
        return "not addressed"
    if r.get("status") == "not_carried":
        return "not carried (absent)"
    if r.get("value") is False:
        return "read as false: the criterion is not met"
    return f"carried, {json.dumps(r.get('value'))}"


def _cell(r: dict | None) -> str:
    if not r:
        return "<td class='none'></td>"
    c = r.get("confidence", 0)
    if is_loss(r):
        cls, mark = ("loss" if c >= THRESHOLD else "weak"), "✗"
    elif is_kept(r):
        cls, mark = ("kept" if c >= THRESHOLD else "kept-low"), "✓"
    else:
        cls, mark = "none", "·"
    tip = html.escape(f"{_value(r)} ({c:.2f}) {r.get('quote') or ''}", quote=True)
    return f"<td class='{cls}' title='{tip}'>{mark}<small>{c:.2f}</small></td>"


def card(results: str, row: dict, entry: dict, maps: str | None) -> str:
    run = row["run"]
    rdir = os.path.join(results, run)
    with open(os.path.join(rdir, "commitments.json"), encoding="utf-8") as f:
        record = json.load(f)
    first = _jsonl(os.path.join(rdir, "reads.jsonl"))
    second = _jsonl(os.path.join(rdir, "second-reads.jsonl"))
    path, link = entry["path"], entry["link"]
    field = next((r["field"] for r in first if r["field"].split(":", 1)[-1] == path), None)
    if field is None:
        return f"<section><h2>{html.escape(run)}: {html.escape(path)}</h2><p>No read of this field in reads.jsonl.</p></section>"
    cid = field.split(":", 1)[0]
    commitment = next((c for c in record.get("commitments", []) if c.get("commitment_id") == cid), {})
    links = []
    for r in first:
        if r["link"] not in links:
            links.append(r["link"])
    sender = {r["link"]: r.get("sender", "") for r in first}
    f1 = {r["link"]: r for r in first if r["field"] == field}
    f2 = {r["link"]: r for r in second if r["field"] == field}
    a, b = f1.get(link), f2.get(link)
    st = status(a, b)
    later = [f"{l} {sender.get(l, '')} {'kept' if is_kept(f1[l]) else 'lost'} ({f1[l].get('confidence', 0):.2f})"
             for l in links[links.index(link) + 1:] if l in f1 and (is_kept(f1[l]) or is_loss(f1[l]))]
    drafted = record.get("drafted_by") or {}
    esc = html.escape

    def reader(r: dict | None, n: int) -> str:
        if not r:
            return f"<dt>Reader {n}</dt><dd>{'no second read at this link yet' if n == 2 else 'no read'}</dd>"
        return (f"<dt>Reader {n}</dt><dd>{esc(_value(r))} at confidence {r.get('confidence', 0):.2f}, "
                f"{esc(r.get('version') or r.get('model') or '')} [C]: <q>{esc(r.get('quote') or '')}</q></dd>")

    strip_head = "".join(f"<th class='{'here' if l == link else ''}'>{esc(l)}<br><small>{esc(sender.get(l, ''))}</small></th>" for l in links)
    strip_1 = "".join(_cell(f1.get(l)).replace("<td ", f"<td data-here='{l == link}' ", 1) for l in links)
    strip_2 = "".join(_cell(f2.get(l)).replace("<td ", f"<td data-here='{l == link}' ", 1) for l in links)
    svg = os.path.join(maps, f"{run}.svg") if maps else ""
    if svg and os.path.exists(svg):
        with open(svg, encoding="utf-8") as fh:
            run_map = "<div class='map'>" + re.sub(r"^<\?xml[^>]*>\s*", "", fh.read()) + "</div>"
    else:
        run_map = ("<p class='note'>Run map: not drawn yet. It is drawn from the run's tier-1 ledger with "
                   "<code>as_agreed.report.redraw(ledger, svg, values=True)</code> and passed with <code>--maps</code>.</p>")
    return f"""<section>
<div class='status' style='background:{STATUS_COLOUR[st]}'>{esc(st)}</div>
<h2>{esc(_col(row, 'find') or run)}</h2>
<p class='tag'>{esc(run)} · field <code>{esc(cid)}:{esc(path)}</code> · the table says <b>{esc(entry['cls'])}</b> at {esc(link)} · a loss the dataset's authors did not label: {esc(_col(row, 'unexpected') or 'not given')}</p>
<dl>
<dt>Agreed</dt><dd>{esc(_agreed(commitment, path))} <span class='src'>(task statement: <q>{esc((record.get('quotes') or {}).get(cid, ''))}</q>; a proxy drafted by {esc(drafted.get('model', 'a model'))} from the task alone [C])</span></dd>
<dt>Arrived</dt><dd>at <b>{esc(link)} {esc(sender.get(link, ''))}</b></dd>
{reader(a, 1)}
{reader(b, 2)}
<dt>Status</dt><dd>{esc(STATUS_TEXT[st])}</dd>
<dt>After it</dt><dd>{esc('; '.join(later)) if later else 'no later link reads this field'}</dd>
</dl>
<div class='strip'><table><tr><th></th>{strip_head}</tr><tr><th>reader 1</th>{strip_1}</tr><tr><th>reader 2</th>{strip_2}</tr></table></div>
<p class='legend'><span class='sw loss'></span>loss at 0.8+ <span class='sw weak'></span>loss below 0.8 <span class='sw kept'></span>arrived at 0.8+ <span class='sw kept-low'></span>arrived below 0.8 <span class='sw none'></span>not addressed. Hover a cell for the quote.</p>
{run_map}
</section>"""


# ---- rows.json path (chunk format, 2026-11-05) ------------------------------------------------------------------------
# One unit = one field at one link. rows.json gives, per run and field, tier 1's class at every link (reader 1) and, at
# every link read twice, both readers' class, status, value, confidence and quote with the D-44 kind of the unit
# (finding / proposal / split, or none when neither reader gives a loss). hand-check.md gives the hand verdict per split
# ("Every split" table) and the rows seeded for a person's own read ("seeded rows" section).

KIND_STATUS = {"finding": "FINDING", "proposal": "PROPOSAL", "split": "SPLIT", "one_reader": "ONE READER"}
LOSS_SET = set(LOSS_CLASSES.split("|"))
STATUS_TEXT_ROWS = dict(STATUS_TEXT, **{
    "ONE READER": "One reader only: a loss read once, its second read missing. Kept apart; never a finding.",
    "NO LOSS": "No loss: no reader gives a loss class at this link. The bench holds nothing here.",
    "PROPOSAL": "Proposal: both readers give the same loss class, one or both below 0.8. For a hand read (tier 3); never a finding.",
    "SPLIT": "Split: the two readers give different classes and at least one gives a loss. Read against the raw link text by hand.",
})
STATUS_COLOUR["ONE READER"] = "#b9770e"
ABBR = {"PRESERVED": "PRE", "UNDECLARED": "UND", "ESCALATED": "ESC", "RESTATED": "RST", "ADDED_UNPARENTED": "ADD"}


def _md(text: str) -> str:
    """The inline markdown of hand-check.md (`code`, **bold**) as HTML; everything else escaped."""
    out = []
    for i, part in enumerate(re.split(r"`([^`]*)`", text)):
        if i % 2:
            out.append(f"<code>{html.escape(part)}</code>")
        else:
            out.append(re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(part, quote=False)))
    return "".join(out)


VALUE_HEAD = re.compile(r"^  - `(?P<run>[^`]+)`(?: (?P<link>L\d+))?(?: `(?P<field>[^`]+)`)?: ?(?P<title>.*)$")
VALUE_LINE = re.compile(r"^    - (?P<key>loss|hold|opportunity): (?P<text>.+)$")
VALUE_LABEL = {"loss": "Loss", "hold": "What the hold would have done", "opportunity": "Opportunity"}


def business_value(chunks_md: str, results: str) -> list:
    """D-54: the seller's three lines per finding, from the "Business value" sub-list of the chunks.md block whose
    number the results folder names (results/<date>-chunk-<n>). An entry is `run` [Lnn] [`field`]: title, then the
    three lines loss, hold and opportunity, each four spaces in. Returns a list of entries; none when the block has no
    such sub-list, so cards of earlier chunks are unchanged."""
    m = re.search(r"chunk-(\d+)", os.path.basename(os.path.normpath(results)))
    if not m or not chunks_md or not os.path.exists(chunks_md):
        return []
    with open(chunks_md, encoding="utf-8") as f:
        text = f.read()
    block = re.search(rf"^## Chunk {m.group(1)} .*?(?=^## Chunk |\Z)", text, re.M | re.S)
    sec = re.search(r"^- \*\*Business value\*\*[^\n]*\n(?P<body>(?:(?: {2,}).*\n?)*)", block.group(0), re.M) if block else None
    out = []
    for line in (sec.group("body").splitlines() if sec else []):
        h, v = VALUE_HEAD.match(line), VALUE_LINE.match(line)
        if h:
            out.append(dict(h.groupdict(), lines={}))
        elif v and out:
            out[-1]["lines"][v.group("key")] = v.group("text").strip()
    return [e for e in out if len(e["lines"]) == 3]


def value_for(entries: list, run: str, link: str | None = None, field: str | None = None) -> list:
    """The entries that name this run, and this link and field where they name one."""
    def names(f: str) -> set:
        cid, path = f.split(":", 1) if ":" in f else (f, f)
        return {f, cid, path, path.split(".", 1)[-1]}
    hits = []
    for e in entries:
        if e["run"] != run or (link and e["link"] and e["link"] != link) or (link is None and e["link"]):
            continue
        if field and e["field"] and e["field"] not in names(field):
            continue
        if link and not e["link"]:
            continue
        hits.append(e)
    return hits


def value_html(entries: list) -> str:
    esc = html.escape
    return "".join(f"<div class='value'><p class='vt'>Business value{': ' + _md(e['title']) if e['title'] else ''} "
                   f"<span class='src'>(chunks.md, D-54; a seller's reading of the row, not a measured figure)</span></p><ul>"
                   + "".join(f"<li><b>{VALUE_LABEL[k]}</b>: {_md(e['lines'][k])}</li>" for k in ("loss", "hold", "opportunity"))
                   + "</ul></div>" for e in entries)


def load_rows(results: str) -> list:
    with open(os.path.join(results, "rows.json"), encoding="utf-8") as f:
        return json.load(f)


def hand_splits(path: str) -> dict:
    """hand-check.md's "Every split" table: {(run, field, link): {hand, quote, why, reader 1, reader 2}}."""
    out, header = {}, None
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("|"):
                header = None if not line.strip() else header
                continue
            if line.startswith("|---"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and cells[0] == "run" and "hand" in cells:
                header = cells
                continue
            if header and len(cells) == len(header):
                row = dict(zip(header, cells))
                field = row.get("field", "").strip("`")
                for link in re.findall(r"\bL\d+\b", row.get("links", "")):
                    out[(row["run"], field, link)] = row
    return out


def seeded_rows(path: str) -> dict:
    """hand-check.md's seeded-rows section: {"title", "intro", "items": [{n, run, head, bullets}], "outro"}."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"^## (?P<title>[^\n]*[Ss]eeded rows[^\n]*)\n(?P<body>.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return {"title": "", "intro": [], "items": [], "outro": []}
    sec = {"title": m.group("title").strip(), "intro": [], "items": [], "outro": []}
    for line in m.group("body").splitlines():
        item = re.match(r"^(\d+)\. \*\*([^*]+)\*\*\s*(.*)$", line)
        bullet = re.match(r"^\s+- (.*)$", line)
        if item:
            sec["items"].append({"n": int(item.group(1)), "run": item.group(2).strip(), "head": item.group(3), "bullets": []})
        elif bullet and sec["items"]:
            sec["items"][-1]["bullets"].append(bullet.group(1))
        elif line.strip():
            (sec["outro"] if sec["items"] else sec["intro"]).append(line.strip())
    return sec


def _conf(x: dict | None):
    if not x:
        return None
    if x.get("confidence") is not None:
        return x["confidence"]
    m = re.search(r"read at (\d\.\d+)", x.get("reason") or "")
    return float(m.group(1)) if m else None


def units(row: dict) -> list:
    """Every unit of a run (one field at one link), in link order, both readers where the link was read twice."""
    out = []
    for f in row.get("fields") or []:
        second = {s["link"]: s for s in f.get("second") or []}
        one = {s["link"]: s for s in f.get("one_reader") or []}
        for p in f.get("per_link") or []:
            s = second.get(p["link"]) or one.get(p["link"])
            r1 = dict(s["reader1"]) if s else {"class": p.get("class"), "value": p.get("value"), "quote": p.get("quote"),
                                               "confidence": _conf(p), "reason": p.get("reason")}
            r1.setdefault("reason", p.get("reason"))
            if r1.get("confidence") is None:
                r1["confidence"] = _conf(p)
            out.append({"run": row["run"], "field": f["field"], "agreed": f.get("agreed"), "modality": f.get("modality"),
                        "link": p["link"], "site": p.get("site") or (s or {}).get("site", ""),
                        "state": (s or {}).get("state") or p.get("state", ""), "kind": (s or {}).get("kind"),
                        "r1": r1, "r2": (s or {}).get("reader2") if s and s.get("reader2") else None})
    return out


def unit_status(u: dict) -> str:
    if u["kind"] in KIND_STATUS:
        return KIND_STATUS[u["kind"]]
    if u["r2"] is None and (u["r1"] or {}).get("class") in LOSS_SET:
        return "ONE READER"
    return "NO LOSS"


def _rcell(r: dict | None, here: bool) -> str:
    """One cell of the path strip from a rows.json reader dict (class, confidence, quote)."""
    if not r:
        return f"<td class='none' data-here='{here}'></td>"
    cls_name, c = r.get("class") or "", r.get("confidence")
    strong = c is not None and c >= THRESHOLD
    if cls_name in LOSS_SET:
        css, mark = ("loss" if strong else "weak"), "✗"
    elif cls_name == "PRESERVED":
        css, mark = ("kept" if strong else "kept-low"), "✓"
    else:
        css, mark = "none", "·"
    conf = "" if c is None else f"{c:.2f}"
    tip = html.escape(f"{cls_name} ({conf or 'no read'}) {r.get('quote') or r.get('reason') or ''}", quote=True)
    return (f"<td class='{css}' data-here='{here}' title='{tip}'>{mark}<small>{ABBR.get(cls_name, cls_name[:3])}"
            f"{' ' + conf if conf else ''}</small></td>")


def _rvalue(r: dict) -> str:
    st, v = r.get("status"), r.get("value")
    if st == "not_addressed" or (st is None and r.get("class") == "UNDECLARED"):
        return "not addressed"
    if st == "not_carried":
        return "not carried (absent)"
    if v is False:
        return "read as false: the criterion is not met"
    if v is None:
        return "no value given"
    if v is True:
        return "carried: read as met"
    return f"carried, {json.dumps(v, ensure_ascii=False)}"


class RunView:
    """What a card needs about one run: its rows.json row, record, link senders, units, hand verdicts."""

    def __init__(self, results: str, row: dict, hand: dict, value: list | None = None):
        self.row, self.run = row, row["run"]
        self.value = value or []
        rdir = os.path.join(results, self.run)
        cpath = os.path.join(rdir, "commitments.json")
        self.record = {}
        if os.path.exists(cpath):
            with open(cpath, encoding="utf-8") as f:
                self.record = json.load(f)
        self.sender = {}
        for r in _jsonl(os.path.join(rdir, "reads.jsonl")):
            self.sender.setdefault(r.get("link"), r.get("sender", ""))
        self.units = units(row)
        self.links = []
        for u in self.units:
            if u["link"] not in self.links:
                self.links.append(u["link"])
        self.hand = {k[1:]: v for k, v in hand.items() if k[0] == self.run}

    def by_field(self, field: str) -> dict:
        return {u["link"]: u for u in self.units if u["field"] == field}

    def task_quote(self, field: str) -> str:
        return (self.record.get("quotes") or {}).get(field.split(":", 1)[0], "")

    def strip(self, field: str, here: str = "") -> str:
        f = self.by_field(field)
        esc = html.escape
        head = "".join(f"<th class='{'here' if l == here else ''}'>{esc(l)}<br><small>{esc(self.sender.get(l, ''))}</small></th>"
                       for l in self.links)
        s1 = "".join(_rcell((f.get(l) or {}).get("r1"), l == here) for l in self.links)
        s2 = "".join(_rcell((f.get(l) or {}).get("r2"), l == here) for l in self.links)
        return (f"<div class='strip'><table><tr><th></th>{head}</tr><tr><th>reader 1</th>{s1}</tr>"
                f"<tr><th>reader 2</th>{s2}</tr></table></div>{LEGEND}")

    def unit_card(self, u: dict) -> str:
        esc, st = html.escape, unit_status(u)
        field, link = u["field"], u["link"]
        drafted = self.record.get("drafted_by") or {}
        agreed = u["agreed"] if isinstance(u["agreed"], str) else f"{field.split(':', 1)[1]} = {json.dumps(u['agreed'], ensure_ascii=False)}"

        def reader(r: dict | None, n: int, model: str) -> str:
            if not r:
                return f"<dt>Reader {n}</dt><dd>no read at this link{' a second time' if n == 2 else ''}</dd>"
            c = r.get("confidence")
            quote = r.get("quote")
            return (f"<dt>Reader {n}</dt><dd><b>{esc(r.get('class') or '')}</b>: {esc(_rvalue(r))}, confidence "
                    f"{'none' if c is None else f'{c:.2f}'}, {esc(model)} [C]"
                    + (f": <q>{esc(quote)}</q>" if quote else ": no quote") + "</dd>")

        h = self.hand.get((field, link))
        if h:
            hand = (f"<b>{esc(h.get('hand', ''))}</b>: <q>{esc(h.get('quote', '').strip().strip(chr(34)).strip('`'))}</q> "
                    f"{_md(h.get('why, from the raw text', '') or _col(h, 'why'))} <span class='src'>(hand-check.md, one reader [C])</span>")
        elif st == "SPLIT":
            hand = "open: this split has no row in hand-check.md"
        else:
            hand = "none: the hand check reads every split, and this unit is not a split"
        return f"""<article class='unit'>
<div class='status' style='background:{STATUS_COLOUR[st]}'>{esc(st)}</div>
<h3><code>{esc(field)}</code> at {esc(link)} {esc(self.sender.get(link, ''))}</h3>
<dl>
<dt>Agreed</dt><dd>{esc(agreed)} ({esc(u.get('modality') or '')}) <span class='src'>(task statement: <q>{esc(self.task_quote(field))}</q>; a proxy drafted by {esc(drafted.get('model', 'a model'))} from the task alone [C])</span></dd>
<dt>Link</dt><dd><b>{esc(link)}</b> {esc(self.sender.get(link, ''))} · {esc(u.get('site') or '')} · {esc(u.get('state') or '')}</dd>
{reader(u['r1'], 1, self.row.get('reader', 'reader 1'))}
{reader(u['r2'], 2, self.row.get('second_reader', 'reader 2'))}
<dt>Status</dt><dd>{esc(STATUS_TEXT_ROWS[st])}</dd>
<dt>Hand</dt><dd>{hand}</dd>
<dt>Path</dt><dd>the field across every link of the run:</dd>
</dl>
{value_html(value_for(self.value, self.run, link, field))}
{self.strip(field, link)}
</article>"""

    def head(self) -> str:
        r, esc = self.row, html.escape
        final = (r.get("final") or {}).get("status", "")
        return (f"<p class='tag'>{esc(self.run)} · {r.get('links', '?')} links · {r.get('declared', '?')} fields declared · "
                f"bench: {esc(r.get('status', ''))}, after the hand check: {esc(final)} · findings {r.get('n_findings', 0)}, "
                f"proposals {r.get('n_proposals', 0)}, splits {r.get('n_splits', 0)}, one reader only {r.get('n_one_reader', 0)} · "
                f"drafter {esc(r.get('drafter', ''))} · reader 1 {esc(r.get('reader', ''))} · reader 2 {esc(r.get('second_reader', ''))}</p>")


LEGEND = ("<p class='legend'><span class='sw loss'></span>loss at 0.8+ <span class='sw weak'></span>loss below 0.8 "
          "<span class='sw kept'></span>preserved at 0.8+ <span class='sw kept-low'></span>preserved below 0.8 "
          "<span class='sw none'></span>undeclared, not addressed or not read. Hover a cell for the quote.</p>")


def _map(maps: str | None, run: str) -> str:
    svg = os.path.join(maps, f"{run}.svg") if maps else ""
    if svg and os.path.exists(svg):
        with open(svg, encoding="utf-8") as fh:
            return "<div class='map'>" + re.sub(r"^<\?xml[^>]*>\s*", "", fh.read()) + "</div>"
    return ("<p class='note'>Run map: not drawn. It is drawn from the run's tier-1 ledger with "
            "<code>as_agreed.report.redraw(ledger, svg, values=True)</code> and passed with <code>--maps</code>.</p>")


def _named(view: RunView, bullet: str) -> list:
    """The units a seeded bullet names: its links, and either its backticked field names or, when it names no field,
    a quote it shares with a reader (filtered by any class word it gives)."""
    links = re.findall(r"\bL\d+\b", bullet)
    ticks = set(re.findall(r"`([^`]+)`", bullet))
    plain = bullet.replace("**", "")
    spans = [a or b for a, b in re.findall(r'"([^"]{12,})"|`([^`]{12,})`', plain)]
    classes = {c for c in re.findall(r"\b[A-Z_]{6,}\b", bullet) if c in LOSS_SET or c == "PRESERVED"}

    def names(field: str) -> set:
        cid, path = field.split(":", 1)
        return {field, cid, path, path.split(".", 1)[-1]}

    by_field = [u for u in view.units if u["link"] in links and names(u["field"]) & ticks]
    if by_field:
        return by_field
    hits = []
    for u in view.units:
        if u["link"] not in links:
            continue
        quotes = [q.replace("**", "") for q in ((u["r1"] or {}).get("quote"), (u["r2"] or {}).get("quote")) if q and len(q) >= 12]
        if not any(s in q or q in s for s in spans for q in quotes):
            continue
        if classes and not classes & {(u["r1"] or {}).get("class"), (u["r2"] or {}).get("class")}:
            continue
        hits.append(u)
    return hits


def seeded_page(results: str, maps: str | None, runs: set, value: list | None = None) -> tuple:
    """One card per seeded row of hand-check.md: its text verbatim, every unit it names, the run map, and the
    seller's lines (D-54) where the chunk block carries them."""
    rows = {r["run"]: r for r in load_rows(results)}
    hpath = os.path.join(results, "hand-check.md")
    hand, sec = hand_splits(hpath), seeded_rows(hpath)
    esc, cards, gaps = html.escape, [], []
    for it in sec["items"]:
        if runs and it["run"] not in runs:
            continue
        row = rows.get(it["run"])
        if not row or not row.get("fields"):
            gaps.append(f"{it['run']}: no fields in rows.json")
            cards.append(f"<section><h2>{it['n']}. {esc(it['run'])}</h2><p>No fields for this run in rows.json.</p></section>")
            continue
        view = RunView(results, row, hand, value)
        blocks, seen = [], set()
        for b in it["bullets"]:
            hits = _named(view, b)
            named = [u for u in hits if (u["field"], u["link"]) not in seen]
            if not hits:
                gaps.append(f"{it['run']}: no unit matched the bullet {b[:60]!r}")
            seen.update((u["field"], u["link"]) for u in named)
            blocks.append(f"<div class='seed'><p class='said'>{_md(b)} <span class='src'>(hand-check.md)</span></p>"
                          + ("".join(view.unit_card(u) for u in named) or
                             "<p class='note'>The bench has no unit for this sentence: no reader read this field at these links.</p>")
                          + "</div>")
        cards.append(f"""<section>
<h2>{it['n']}. {esc(it['run'])}</h2>
{view.head()}
<p class='said'>{_md(it['head'])} <span class='src'>(hand-check.md)</span></p>
{value_html(value_for(value or [], it['run']))}
{''.join(blocks)}
<h3>Run map</h3>
{_map(maps, it['run'])}
</section>""")
    intro = "".join(f"<p class='lede'>{_md(p)}</p>" for p in sec["intro"])
    outro = "".join(f"<p class='lede'>{_md(p)} <span class='src'>(hand-check.md)</span></p>" for p in sec["outro"])
    return cards, f"<h2 class='plain'>{esc(sec['title'])}</h2>{intro}", outro, gaps


def findings_page(results: str, kinds: set, runs: set, value: list | None = None) -> tuple:
    """One card per unit of the given D-44 kinds, grouped by run, in rows.json order."""
    hand = hand_splits(os.path.join(results, "hand-check.md"))
    cards, groups = [], []
    for row in load_rows(results):
        if (runs and row["run"] not in runs) or not row.get("fields"):
            continue
        view = RunView(results, row, hand, value)
        mine = [view.unit_card(u) for u in view.units if u["kind"] in kinds]
        if not mine:
            continue
        cards.extend(mine)
        groups.append(f"<section><h2>{html.escape(row['run'])} <small>{len(mine)} card(s)</small></h2>{view.head()}"
                      + "".join(mine) + "</section>")
    return cards, groups


CSS = """body{font:15px/1.45 -apple-system,Helvetica,Arial,sans-serif;margin:0;background:#f6f6f4;color:#1d1d1b}
main{max-width:1500px;margin:0 auto;padding:24px 16px 64px}h1{font-size:24px;margin:0 0 4px}.lede{color:#555;margin:0 0 14px}
section{position:relative;background:#fff;border:1px solid #ddd;border-radius:8px;margin:0 0 28px;padding:18px 20px}
h2{font-size:19px;margin:0 0 2px;padding-right:200px}.tag{color:#555;font-size:13px;margin:0 0 12px}
.status{position:absolute;top:16px;right:20px;color:#fff;font-weight:700;font-size:13px;padding:3px 10px;border-radius:4px}
dl{display:grid;grid-template-columns:90px 1fr;gap:6px 14px;margin:0 0 14px}dt{font-weight:600;color:#444}dd{margin:0}
q{font-family:ui-monospace,Menlo,monospace;font-size:13px;background:#f3f3f0;padding:1px 4px;border-radius:3px}
.src{color:#666;font-size:13px}.strip{overflow-x:auto}table{border-collapse:collapse;font-size:12px}
th,td{border:1px solid #e2e2e2;padding:4px 6px;text-align:center;min-width:46px}th small,td small{display:block;color:#555;font-weight:400}
th.here{outline:3px solid #1d1d1b;outline-offset:-3px}td[data-here='True']{outline:3px solid #1d1d1b;outline-offset:-3px}
td.loss{background:#c0392b;color:#fff}td.loss small{color:#fde}td.weak{background:#f5c77e}td.kept{background:#5b8c5a;color:#fff}
td.kept small{color:#e6f2e6}td.kept-low{background:#cfe3cf}td.none{background:#f7f7f7;color:#aaa}
.legend{font-size:12px;color:#555}.sw{display:inline-block;width:12px;height:12px;vertical-align:-2px;margin:0 4px 0 10px;border:1px solid #ccc}
.sw.loss{background:#c0392b}.sw.weak{background:#f5c77e}.sw.kept{background:#5b8c5a}.sw.kept-low{background:#cfe3cf}.sw.none{background:#f7f7f7}
.note{color:#666;font-size:13px}h3{font-size:16px;margin:14px 0 6px;padding-right:130px}h2.plain{padding:0}
article.unit{position:relative;border-top:1px solid #e4e4e0;padding:10px 0 6px;margin-top:8px}article.unit .status{top:10px;right:0}
.seed{margin:14px 0 0}.said{background:#f8f6ee;border-left:3px solid #c9b46a;padding:6px 10px;margin:8px 0}
.value{background:#eef4fb;border-left:3px solid #3b6ea8;padding:6px 10px;margin:10px 0}.value ul{margin:4px 0 2px 18px;padding:0}.vt{margin:0;font-weight:600}
code{font-family:ui-monospace,Menlo,monospace;font-size:13px}h2 small{color:#666;font-weight:400;font-size:14px}.map svg{width:100%;height:auto;min-width:900px}.map{overflow-x:auto}"""


def _page(title: str, sub: str, body: str) -> str:
    return (f"<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style><main><h1>{html.escape(title)}</h1>"
            f"<p class=lede>{sub}</p>{body}</main></html>")


NOTE = ("status by D-44 (two readers, different models, same loss, both at 0.8 or above). Every agreed field is a model's "
        "proxy and every read is a model's read [C]; agreement between readers is not truth, and neither is the hand check.")


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="One verdict card per loss in a bench results folder.")
    ap.add_argument("results")
    ap.add_argument("out")
    ap.add_argument("--runs", default="", help="comma-separated run names; default every run with a loss")
    ap.add_argument("--maps", default=None, help="folder of <run>.svg maps to inline under each card")
    ap.add_argument("--seeded", action="store_true", help="rows.json only: one card per seeded row of hand-check.md")
    ap.add_argument("--kinds", default="finding", help="rows.json only: D-44 kinds to card (finding,proposal,split,one_reader)")
    ap.add_argument("--chunks", default=None, help="chunks.md whose block for this chunk carries the Business value lines "
                                                   "(D-54); default: chunks.md beside the results folder's parent")
    args = ap.parse_args(argv)
    chunks_md = args.chunks or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(args.results))), "chunks.md")
    value = business_value(chunks_md, args.results)
    wanted = {r for r in args.runs.split(",") if r}
    made = f"{html.escape(os.path.normpath(args.results))} · made {datetime.date.today().isoformat()} by cards.py · "
    if os.path.exists(os.path.join(args.results, "rows.json")):
        if args.seeded:
            cards, head, tail, gaps = seeded_page(args.results, args.maps, wanted, value)
            for g in gaps:
                print("gap:", g, file=sys.stderr)
            what = "seeded row(s)"
            page = _page("Seeded rows", made + f"{len(cards)} {what} · " + NOTE, head + "".join(cards) + tail)
        else:
            kinds = {k for k in args.kinds.split(",") if k}
            cards, groups = findings_page(args.results, kinds, wanted, value)
            what = f"card(s) of kind {', '.join(sorted(kinds))} in {len(groups)} run(s)"
            page = _page("Verdict cards", made + f"{len(cards)} {what} · " + NOTE, "".join(groups))
        if not cards:
            print("no unit to card in", os.path.join(args.results, "rows.json"), file=sys.stderr)
            return 1
    else:
        cards, what = [], "card(s)"
        for row in _table(os.path.join(args.results, "table.md")):
            if wanted and row["run"] not in wanted:
                continue
            for m in ENTRY.finditer(_col(row, "findings")):
                cards.append(card(args.results, row, m.groupdict(), args.maps))
        if not cards:
            print("no loss named in the findings column of", os.path.join(args.results, "table.md"), file=sys.stderr)
            return 1
        page = (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
                f"<title>Verdict cards</title><style>{CSS}</style><main><h1>Verdict cards</h1>"
                f"<p class=lede>{html.escape(os.path.normpath(args.results))} · {len(cards)} card(s) · made "
                f"{datetime.date.today().isoformat()} by cards.py · status by D-44 (two readers at 0.8 or above). Every "
                f"agreed field is a model's proxy and every read is a model's read [C]; agreement between readers is not "
                f"truth.</p>" + "".join(cards) + "</main>")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"{len(cards)} {what} written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
