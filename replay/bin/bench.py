#!/usr/bin/env python3
"""Trace bench: draft the as-agreed record from a run's task statement, read the delivered value of every typed field
at every link, run tier 1 against the drafted record, and write one table row per run.

    python3 -I -B bench.py <runs_dir> <out_dir> [--mode api|exchange|dry-run] [--exchange <dir>] [--lib <claim-ledger>]
        [--second-reader [--exchange2 <dir>]] [--records <earlier out_dir>]   # D-42: a second read of every read below 0.8

<runs_dir> holds one folder per run, either a `links.jsonl` as studies/public-readings/mast/build/extract.py writes it
(line 1 the metadata, then one link per line; link 0 is the order) or a stage folder (numeric-prefixed .md or .txt
files, the first being the order). Folders whose names start with "_" or "." are skipped.

Per run, <out_dir>/<run>/ gets commitments.json (the drafted record, proxy: true, model, version, date, tag [C]),
reads.jsonl (per link, per field: the value read, confidence, quote, whether tier 1 got it), calls.jsonl (every model
call with its prompt and raw answer), and tier1/<field>/ (the stage folder tier 1 ran on, and the library's report:
ledger.jsonl, counts.csv, flow.svg). <out_dir>/table.md gets one row per run; <out_dir>/hand-check.md, when present,
is printed at its foot.

Modes (models.py): api when the `anthropic` package and ANTHROPIC_API_KEY are present; exchange (prompts written to a
folder, answers read back, so any model can answer and a rerun resumes; exit code 4 while prompts are pending);
dry-run (fixtures, no model). Default: api when available, else dry-run.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from typing import Any, Dict, List, Optional

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # our own modules only; -I keeps the data folders off the path

import models  # noqa: E402
import prompts as P  # noqa: E402

DRAFTER_MODEL = "claude-opus-5-5"
READER_MODEL = "claude-sonnet"  # the exact id is taken from the answer when the mode can tell (exchange: <sha>.model)
PREFIX = re.compile(r"^(\d+)[-_ ]*(.*)\.(md|txt)$")
DRAFTER_V = P.DRAFTER_DEFAULT  # the drafter prompt version; --drafter-version v1 reproduces chunk 1
READER_V = P.READER_DEFAULT  # the reader prompt version; --reader-version v2 reproduces chunk 1
# which first reads the second reader reads again (D-44 and after): "d44" is chunk 1's rule (every read below 0.8,
# every read giving a class other than PRESERVED); "d44-preserved" adds every PRESERVED read at a final output or a
# code link (chunk 1's rule delta, applied in chunk 2: forced by aegis-08 L11 and, in the regression, t01 L10)
SECOND_RULES = ("d44", "d44-preserved")
SECOND_RULE = "d44-preserved"
REREAD_SITES = ("final output", "code link")
LOSS = ("DROPPED", "WIDENED", "NARROWED", "WEAKENED", "STRENGTHENED", "RECONDITIONED", "REASSIGNED", "RESCHEDULED",
        "ADDED_UNPARENTED")


def load_lib(path: str) -> None:
    src = os.path.join(os.path.abspath(path), "src")
    if not os.path.isdir(os.path.join(src, "as_agreed")):
        raise SystemExit(f"no as_agreed package under {src}")
    sys.path.insert(1, src)


# ---------- runs ----------
def load_run(folder: str) -> Dict[str, Any]:
    lj = os.path.join(folder, "links.jsonl")
    if os.path.exists(lj):
        with open(lj, encoding="utf-8") as f:
            rows = [json.loads(l) for l in f.read().splitlines() if l.strip()]
        meta = rows[0] if rows and rows[0].get("type") == "meta" else {}
        links = [r for r in rows if r.get("type") == "link"]
        return {"meta": meta, "task": links[0]["text"],
                "links": [{"n": r["n"], "from": r.get("from"), "kind": r.get("kind"), "text": r["text"],
                           **{k: r[k] for k in ("parent", "to", "outputs") if k in r}} for r in links[1:]]}
    files = sorted((int(m.group(1)), f) for f in os.listdir(folder) for m in [PREFIX.match(f)] if m)
    if len(files) < 2:
        raise ValueError(f"{folder}: neither links.jsonl nor two stage files")
    texts = [(n, f, open(os.path.join(folder, f), encoding="utf-8").read()) for n, f in files]
    return {"meta": {}, "task": texts[0][2].strip(),
            "links": [{"n": n, "from": PREFIX.match(f).group(2) or f, "kind": "stage", "text": t} for n, f, t in texts[1:]]}


def find_name(meta: Dict[str, Any], name: str) -> str:
    if "row_idx" in meta:
        return f"MAST-Data row {meta['row_idx']} ({meta.get('mas_name')}, {meta.get('llm_name')}, {meta.get('benchmark_name')})"
    return name


def mast_codes(meta: Dict[str, Any]) -> Optional[List[str]]:
    ann = meta.get("mast_annotation")
    return None if ann is None else sorted(k for k, v in ann.items() if v)


# ---------- one run ----------
def result_kind(class1: Any, conf1: Optional[float], class2: Any, conf2: Optional[float]) -> Optional[str]:
    """D-42, for one field at one link read twice: "finding" when both readers give the same loss class at 0.8 or above,
    "proposal" when they give the same loss class and one or both is below 0.8, "split" when they differ and at least
    one gives a loss (one says carried, one says not addressed, or a different loss). None when neither gives a loss."""
    l1, l2 = class1 in LOSS, class2 in LOSS
    if not (l1 or l2):
        return None
    if class1 == class2:
        return "finding" if min(conf1 or 0.0, conf2 or 0.0) >= P.THRESHOLD else "proposal"
    return "split"


def needs_second(g: Dict[str, Any]) -> bool:
    """A first read below the threshold, whatever its status (D-42: every read below 0.8 gets a second reader)."""
    return g.get("status") in ("carried", "not_carried", "not_addressed") and g.get("confidence") is not None \
        and g["confidence"] < P.THRESHOLD


def reused_record(path: str, task: str) -> Dict[str, Any]:
    """A record drafted by an earlier run, taken as it is (not redrafted); refused when its task statement differs."""
    with open(path, encoding="utf-8") as f:
        record = json.load(f)
    if record.get("task_statement_sha256") != models.sha(task):
        raise ValueError(f"{path}: drafted from another task statement")
    return record


def bench_run(name: str, run: Dict[str, Any], out: str, drafter: models.Caller, reader: models.Caller,
              reader2: Optional[models.Caller] = None, record_from: Optional[str] = None) -> Dict[str, Any]:
    from as_agreed.check import Escalation
    from as_agreed.commitment import Commitment
    os.makedirs(out, exist_ok=True)
    for f in ("calls.jsonl", "reads.jsonl", "second-calls.jsonl", "second-reads.jsonl"):
        if os.path.exists(os.path.join(out, f)):
            os.remove(os.path.join(out, f))
    log = models.CallLog(os.path.join(out, "calls.jsonl"))
    row: Dict[str, Any] = {"run": name, "find": find_name(run["meta"], name), "mast": mast_codes(run["meta"]),
                           "mode": drafter.mode, "links": len(run["links"])}
    task = run["task"]
    # 1. the drafter, or the record an earlier run drafted (reused as it is, never redrafted)
    if record_from and os.path.exists(record_from):
        try:
            record = dict(reused_record(record_from, task), reused_from=os.path.relpath(record_from, HERE))
        except (OSError, ValueError) as e:
            row.update(status=f"record not reused: {e}", declared=0)
            return row
        recs, dropped, quotes = record["commitments"], record.get("dropped_by_check") or [], record.get("quotes") or {}
    else:
        try:
            answer = log.wrap(drafter)(P.drafter_prompt(task, DRAFTER_V))
        except models.Pending:
            row["status"] = "pending: drafter"
            return row
        try:
            draft = P.parse_json(answer)
            recs, dropped, quotes = P.record_from_draft(draft, task)
        except (ValueError, TypeError, AttributeError) as e:
            row.update(status=f"drafter answer refused: {e}", declared=0)
            return row
        record = {"kind": "as_agreed_proxy", "proxy": True, "tag": "[C]", "drafted_by": {
            "mode": drafter.mode, "model": drafter.model, "version": drafter.version, "date": models.now(),
            "prompt": P.DRAFTERS[DRAFTER_V][0]},
            "task_statement_sha256": models.sha(task), "obligor_obligee": "set by the harness, not drafted",
            "commitments": recs, "quotes": quotes, "untyped": draft.get("untyped") or [], "dropped_by_check": dropped}
    with open(os.path.join(out, "commitments.json"), "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=1)
    by_id = {r["commitment_id"]: r for r in recs}
    paths = [(r["commitment_id"], p) for r in recs for p in P.typed_paths(r)]
    row.update(declared=len(paths), drafter=f"{record['drafted_by']['version']}, {record['drafted_by']['date'][:10]}",
               dropped_by_check=len(dropped), untyped=len(record["untyped"]))
    if not paths:
        row.update(status="undecided", decided=0, note="no typed field in the task statement")
        return row
    objs = {cid: Commitment.from_mapping(by_id[cid]) for cid in by_id}
    # 2. the reader, one call per link over every typed field (the escalations of that link)
    reads: Dict[int, Dict[str, Dict[str, Any]]] = {}
    pending = 0
    versions = set()
    rlog = open(os.path.join(out, "reads.jsonl"), "a", encoding="utf-8")
    for link in run["links"]:
        link_id = f"L{link['n']:02d}"
        escs = [Escalation(commitment=objs[cid], field=p, agreed=objs[cid].value_at(p), declared=None, link=link_id,
                           link_text=link["text"], reason="a prose link declares no fields") for cid, p in paths]
        prompt = P.reader_prompt(escs, by_id, quotes, link_id, link["from"], link["kind"], version=READER_V)
        try:
            ans = log.wrap(reader)(prompt)
        except models.Pending:
            pending += 1
            continue
        versions.add(reader.version)
        got = P.parse_reads(ans, escs, link["text"])
        reads[link["n"]] = {g["field"]: g for g in got}
        for g in got:
            rlog.write(json.dumps(dict(g, link=link_id, sender=link["from"], model=reader.model, version=reader.version,
                                       mode=reader.mode, prompt=P.READERS[READER_V][0], tag="[C]"), ensure_ascii=False) + "\n")
    rlog.close()
    if pending:
        row["status"] = f"pending: reader ({pending} links)"
        return row
    row["reader"] = ", ".join(sorted(versions)) + f", {models.now()[:10]}"
    # 2b. the second reader (D-42): every field read below the threshold at a link, read again by a fresh prompt
    # context over the same reader prompt, with no sight of the first answer; one call per link over those fields
    reads2: Dict[int, Dict[str, Dict[str, Any]]] = {}
    w1 = tier1_world(name, run, out, recs, reads, "tier1", record)
    if reader2 is not None:
        log2 = models.CallLog(os.path.join(out, "second-calls.jsonl"))
        r2log = open(os.path.join(out, "second-reads.jsonl"), "a", encoding="utf-8")
        pending2, versions2 = 0, set()
        for link in run["links"]:
            link_id = f"L{link['n']:02d}"
            per = reads.get(link["n"], {})
            low = [g["field"] for g in per.values() if needs_second(g)]
            # D-44: a finding needs both readers at 0.8 or above, so a loss read at or above the threshold is read
            # twice as well, in a prompt of its own (the prompts over the low reads stay as they were, and so their
            # stored answers are reused)
            # (orchestrator, 2026-11-04: every read that gives any class but PRESERVED, a change tier 1 cannot class too)
            sure = [f for f, g in per.items() if g.get("used") and f not in low
                    and (w1["cls"].get((f, link_id)) or {}).get("class") not in (None, "PRESERVED", "UNDECLARED")]
            # chunk 2 (d44-preserved): a PRESERVED read at or above the threshold at a final output or a code link is
            # read twice too, in a prompt of its own, because a wrong delivered answer or code read as carried was in
            # no column in chunk 1 (aegis-08 L11 states 4254; the total is 1000)
            kept = [f for f, g in per.items() if SECOND_RULE == "d44-preserved" and g.get("used") and f not in low
                    and f not in sure and site_of(run, link) in REREAD_SITES
                    and (w1["cls"].get((f, link_id)) or {}).get("class") == "PRESERVED"]
            for fields_, extra, why in ((low, None, "below the threshold"), (sure, {"confirm": "loss"}, "a loss at or above the threshold"),
                                        (kept, {"confirm": "preserved"}, "PRESERVED at a final output or a code link")):
                if not fields_:
                    continue
                escs = [Escalation(commitment=objs[cid], field=p, agreed=objs[cid].value_at(p), declared=None, link=link_id,
                                   link_text=link["text"], reason="a prose link declares no fields")
                        for cid, p in paths if f"{cid}:{p}" in fields_]
                prompt = P.reader_prompt(escs, by_id, quotes, link_id, link["from"], link["kind"], read_no=2, extra=extra,
                                         version=READER_V)
                try:
                    ans = log2.wrap(reader2)(prompt)
                except models.Pending:
                    pending2 += 1
                    continue
                versions2.add(reader2.version)
                got = P.parse_reads(ans, escs, link["text"])
                reads2.setdefault(link["n"], {}).update({g["field"]: dict(g, why_second=why) for g in got})
                for g in got:
                    first = reads[link["n"]][g["field"]]
                    r2log.write(json.dumps(dict(g, link=link_id, sender=link["from"], model=reader2.model,
                                                version=reader2.version, mode=reader2.mode, prompt=P.READERS[READER_V][0], read=2,
                                                why_second=why, date=getattr(reader2, "answered_at", None) or models.now(),
                                                prompt_sha256=models.sha(prompt), tag="[C]",
                                                first={k: first.get(k) for k in ("status", "value", "confidence", "quote")}),
                                           ensure_ascii=False) + "\n")
        r2log.close()
        if pending2:
            row["status"] = f"pending: second reader ({pending2} links)"
            return row
        row["second_reader"] = (", ".join(sorted(versions2)) or "none needed") + f", {models.now()[:10]}"
        row["second_rule"] = SECOND_RULE
        row["second_reads"] = sum(len(v) for v in reads2.values())
    used = [g for per in reads.values() for g in per.values() if g["used"]]
    row["min_confidence"] = min((g["confidence"] for g in used), default=None)
    row["reads_used"] = len(used)
    row["reads_refused"] = sum(1 for per in reads.values() for g in per.values() if g.get("why_not_used"))
    # 3. tier 1 through the library's value reader (SPEC §4, draft 8: ValueReader, batch=True): one run over every
    # typed field per reader world; a link that does not address a field leaves it UNDECLARED. World 1 holds reader 1's
    # reads; world 2 holds reader 2's read wherever reader 1 was below the threshold. The reader's threshold is set to 0
    # so that tier 1 classes every read; the bench then applies D-44 (finding, proposal, split) to the two classes.
    merged = {n: dict(per) for n, per in reads.items()}
    for n, per in reads2.items():
        merged[n].update(per)
    w2 = tier1_world(name, run, out, recs, merged, "tier1-second-reader", record) if reader2 is not None else None
    row["library_refused"] = w1["refused"] + (w2["refused"] if w2 else 0)
    fields = []
    for cid, path in paths:
        fname = f"{cid}:{path}"
        per_link = []
        for link in run["links"]:
            lk = f"L{link['n']:02d}"
            v = w1["cls"].get((fname, lk), {})
            g = reads.get(link["n"], {}).get(fname) or {}
            took = bool(g.get("used"))
            per_link.append({"link": lk, "class": v.get("class"), **({"refusal": v["refusal"]} if v.get("refusal") else {}),
                             **({"unit_converted": True} if v.get("unit_converted") else {}),
                             "decided": bool(v.get("class")) and v.get("class") != "ESCALATED" and took,
                             "reason": v.get("reason"), "state": v.get("state"), "site": site_of(run, link),
                             "value": g.get("value") if took else None, "quote": g.get("quote") if took else None,
                             "confidence": g.get("confidence") if took else None})
        decided = [p for p in per_link if p["decided"]]
        losses = [p for p in decided if p["class"] in LOSS]
        proposed = []
        for p in per_link:
            g = reads.get(int(p["link"][1:]), {}).get(fname) or {}
            c = w1["cls"].get((fname, p["link"]), {}).get("class")
            if g.get("proposal") and c in LOSS:
                proposed.append(dict(p, **{"class": c, "value": g.get("value"), "quote": g.get("quote"),
                                           "confidence": g.get("confidence")}))
        agreed_v = by_id[cid].get("limit", {}).get(path.split(".", 1)[-1]) if path.startswith("limit.") else (
            by_id[cid].get("deadline") if path == "deadline" else
            next(c["text"] for c in by_id[cid]["acceptance_criteria"] if f"acceptance_criteria.{c['criterion_id']}" == path))
        f = {"field": fname, "agreed": agreed_v, "modality": by_id[cid]["modality"], "decided": len(decided),
             "losses": losses, "per_link": per_link, "last_decided": decided[-1] if decided else None,
             "proposed_losses": proposed}
        if reader2 is not None:
            f["second"] = []
            for n in sorted(k for k, per in reads2.items() if fname in per):
                lk = f"L{n:02d}"
                g1, g2 = reads[n][fname], reads2[n][fname]
                a = w1["cls"].get((fname, lk), {}).get("class") if (g1.get("used") or g1.get("proposal")) else None
                b = w2["cls"].get((fname, lk), {}).get("class") if (g2.get("used") or g2.get("proposal")) else None
                a, b = a or "UNDECLARED", b or "UNDECLARED"
                link = next(x for x in run["links"] if x["n"] == n)
                f["second"].append({"link": lk, "kind": result_kind(a, g1.get("confidence"), b, g2.get("confidence")),
                                    "site": site_of(run, link), "state": state_of(run, link),
                                    "reader1": {"class": a, **{k: g1.get(k) for k in ("status", "value", "confidence", "quote")}},
                                    "reader2": {"class": b, "why_not_used": g2.get("why_not_used") if not g2.get("proposal") else None,
                                                **{k: g2.get(k) for k in ("status", "value", "confidence", "quote")}}})
            twice = {x["link"] for x in f["second"]}
            # a loss read once (its second read still missing) is "one reader only", never a finding (D-44)
            f["one_reader"] = [dict(x, state=state_of(run, next(l for l in run["links"] if f"L{l['n']:02d}" == x["link"])),
                                    one_reader=True) for x in f["losses"] if x["link"] not in twice]
            f["findings"] = [x for x in f["second"] if x["kind"] == "finding"]
            f["proposals2"] = [x for x in f["second"] if x["kind"] == "proposal"]
            f["splits"] = [x for x in f["second"] if x["kind"] == "split"]
        fields.append(f)
    row["fields"] = fields
    row["escalated_reads"] = [{"field": f["field"], "link": p["link"], "value": p["value"], "reason": p["reason"],
                               "refusal": p.get("refusal")} for f in fields for p in f["per_link"] if p["class"] == "ESCALATED"]
    row["unit_converted_reads"] = [{"field": f["field"], "link": p["link"], "class": p["class"]}
                                   for f in fields for p in f["per_link"] if p.get("unit_converted")]
    row["proposals"] = sum(1 for f in fields if f["proposed_losses"])
    row["decided"] = sum(1 for f in fields if f["decided"])
    found = [f for f in fields if f["losses"]]
    row["status"] = "found" if found else ("preserved" if row["decided"] else "undecided")
    if reader2 is not None:
        row["n_findings"] = sum(len(f["findings"]) for f in fields)
        row["n_one_reader"] = sum(len(f["one_reader"]) for f in fields)
        row["n_proposals"] = sum(len(f["proposals2"]) for f in fields)
        row["n_splits"] = sum(len(f["splits"]) for f in fields)
        row["status"] = ("found" if row["n_findings"] else "split" if row["n_splits"] else
                         "proposal" if row["n_proposals"] else "one reader only" if row["n_one_reader"] else
                         ("preserved" if row["decided"] else "undecided"))
    return row


CODE = re.compile(r"(^|\n)\s*(def |class |import |from \S+ import |#include|function |const |let |public |```)|"
                  r"\bdiff --git\b|^@@ ", re.M)


def site_of(run: Dict[str, Any], link: Dict[str, Any]) -> str:
    """Where a link sits, for the chunk block (D-48): the final output (the last link), the first hand-off (the first
    link after the order), a code link (the text holds code), or a middle hop. The first rule that holds wins."""
    ns = [x["n"] for x in run["links"]]
    if link["n"] == ns[-1] and (run.get("meta") or {}).get("delivered", True):
        return "final output"
    if link["n"] == ns[0]:
        return "first hand-off"
    if CODE.search(link["text"] or ""):
        return "code link"
    return "middle hop"


def state_of(run: Dict[str, Any], link: Dict[str, Any]) -> str:
    """as-delivered at the last link (the commit), as-briefed (a restatement handed on) at every other link, and at
    the last link too when the converter says the run stops at a hand-off (meta "delivered": false)."""
    if not (run.get("meta") or {}).get("delivered", True):
        return "as-briefed"
    return "as-delivered" if link["n"] == run["links"][-1]["n"] else "as-briefed"


def exact_span(quote: str, text: str) -> str:
    """The quote as the library's check wants it (whitespace collapsed, case kept): the bench accepts a quote under
    case folding and stripped quotation marks, so the span is taken back from the link text itself."""
    flat = " ".join(str(text).split())
    q = " ".join(str(quote or "").split()).strip("\"'“”‘’ ")
    if q and q in flat:
        return q
    i = flat.casefold().find(q.casefold())
    if q and i >= 0 and len(flat.casefold()) == len(flat):
        return flat[i:i + len(q)]
    return q


def tier1_world(name: str, run: Dict[str, Any], out: str, recs: List[Dict[str, Any]],
                reads: Dict[int, Dict[str, Dict[str, Any]]], folder_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Tier 1 over every typed field at once, the reads handed in through ab.ValueReader(batch=True), each link a
    prose step (so every field escalates) with on_missing_key="undeclared". Returns (field, link) -> class, the
    library's reason and state, and the number of reads the library refused (its stricter quote check)."""
    import as_agreed.sdk as ab
    from as_agreed.adapters.plain import PlainAdapter
    folder = os.path.join(out, folder_name)
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    d = record.get("drafted_by") or {}
    drafter = {"model": str(d.get("model", "")), "version": str(d.get("version", "")), "date": str(d.get("date", "")),
               "prompt_id": str(d.get("prompt", ""))}
    with open(os.path.join(folder, "commitments.json"), "w", encoding="utf-8") as f:
        json.dump({"commitments": recs, "proxy": True, "drafter": drafter}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(folder, "00-order.md"), "w", encoding="utf-8") as f:
        f.write(run["task"] + "\n")
    report_dir = os.path.join(folder, "report")
    ad = PlainAdapter(run_dir=report_dir, pipeline=P.slug(name))
    agreed = ab.register(run["task"], recs, adapter=ad, proxy=True, source="00-order.md", drafter=drafter)
    steps: Dict[str, str] = {}
    previous: Any = run["task"]
    for i, link in enumerate(run["links"]):
        lk = f"L{link['n']:02d}"
        step_name = f"{lk}-{P.slug(link['from'])}"
        steps[step_name] = lk
        with open(os.path.join(folder, f"{link['n']:02d}-{P.slug(link['from'])}.md"), "w", encoding="utf-8") as f:
            f.write(link["text"] + "\n")
        per = reads.get(link["n"], {})

        def answer(escs: List[Any], _per: Dict[str, Any] = per) -> List[Any]:
            got = []
            for e in escs:
                g = _per.get(f"{e.commitment.commitment_id}:{e.field}")
                if not g or not (g.get("used") or g.get("proposal")):
                    got.append(None)  # not addressed, or refused by the bench's checks: the field stays undeclared
                    continue
                got.append({"value": P.delivered(g, e.field), "confidence": g["confidence"],
                            "quote": exact_span(g["quote"], e.link_text)})
            return got
        tier = ab.ValueReader(answer, threshold=0.0, batch=True)

        def body(prev: Any, _t: str = link["text"], **kw: Any) -> Any:
            return _t
        last = i == len(run["links"]) - 1
        fn = ab.step(step_name, agreed, commit=True if last else None, retries=0, on_undecided="record", adapter=ad,
                     tiers=[tier], on_missing_key="undeclared")(body)
        try:
            fn(previous)
        except ab.DriftHold:
            pass
        previous = link["text"]
    ab.report(ad, out_dir=report_dir, quiet=True)
    cls: Dict[tuple, Dict[str, Any]] = {}
    refused = 0
    for v in ad.records():
        if v.get("kind") != "verdict" or v.get("unit_kind") != "commitment":
            continue
        lk = steps.get(str(v.get("link", "")).split("#")[0])
        if not lk:
            continue
        key = (f"{v['unit']}:{v['field']}", lk)
        if v.get("tier") == 2:
            units = {k: v[k] for k in ("refusal", "unit_agreed", "unit_read", "unit_converted") if v.get(k)}
            if v.get("drift_class"):
                # draft 9: a value in another unit that tier 1's table converts is classed (unit_converted)
                cls[key] = {"class": v["drift_class"], "reason": v.get("reason"), "state": v.get("state"), **units}
            elif "cannot decide the value read" in str(v.get("reason")):
                # a read tier 1 has no procedure for: since draft 9 a unit it cannot convert is refused by name
                # (refusal unit_mismatch); kept apart from not addressed either way
                cls[key] = {"class": "ESCALATED", "reason": v.get("reason"), "state": v.get("state"), **units}
            elif "quote is not in the link" in str(v.get("reason")):
                refused += 1
        elif key not in cls:
            cls[key] = {"class": v.get("drift_class") or v.get("undecided"), "reason": v.get("reason"),
                        "state": v.get("state")}
    return {"cls": cls, "refused": refused}


# ---------- the table ----------
def cell(s: Any, n: int = 160) -> str:
    s = " ".join(str(s).split()).replace("|", "\\|")
    return s if len(s) <= n else s[: n - 1] + "…"


def short_value(v: Any) -> str:
    return "absent" if v is None else json.dumps(v, ensure_ascii=False)


VERDICT = re.compile(r"^(agree with reader 1|agree with reader 2|neither)\b")


def hand_verdicts(out_dir: str) -> Dict[tuple, str]:
    """(run, field, link) -> the hand check's verdict on a split, from the rows of hand-check.md's split table:
    | run | field | links (comma-separated) | reader 1 | reader 2 | hand | quote |."""
    hc = os.path.join(out_dir, "hand-check.md")
    out: Dict[tuple, str] = {}
    if not os.path.exists(hc):
        return out
    with open(hc, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines:
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or not re.search(r"L\d\d", cells[2]):
            continue
        m = VERDICT.match(cells[5].strip("*"))
        if not m:
            continue
        for lk in re.findall(r"L\d\d", cells[2]):
            out[(cells[0], cells[1], lk)] = m.group(1)
    return out


def final_result(r: Dict[str, Any], verdicts: Dict[tuple, str]) -> Dict[str, Any]:
    """The row's result after the hand check of its splits (D-42): final only when every split has a verdict."""
    tally = {"agree with reader 1": 0, "agree with reader 2": 0, "neither": 0, "open": 0}
    by_hand = []
    for f in r.get("fields", []):
        for x in f.get("splits", []):
            v = verdicts.get((r["run"], f["field"], x["link"]))
            tally[v or "open"] += 1
            side = {"agree with reader 1": "reader1", "agree with reader 2": "reader2"}.get(v or "")
            if side and x[side]["class"] in LOSS:
                by_hand.append((f["field"], x["link"], x[side]["class"]))
    if tally["open"]:
        status = f"not final: {tally['open']} splits unchecked"
    elif r.get("n_findings"):
        status = "found"
    elif by_hand:
        status = "loss by hand check"
    elif r.get("n_proposals"):
        status = "proposal"
    elif r.get("n_one_reader"):
        status = "one reader only"
    else:
        status = "preserved" if r.get("decided") else "undecided"
    return {"tally": tally, "by_hand": by_hand, "status": status}


def first_of(items: List[Dict[str, Any]], f: Dict[str, Any], fmt) -> str:
    if not items:
        return ""
    more = len(items) - 1
    return fmt(items[0], f) + (f" (+{more} links)" if more else "")


def table_second(rows: List[Dict[str, Any]], out_dir: str, mode: str) -> str:
    """The table under D-42: findings, proposals and splits in separate columns, and each row's result after the hand
    check of its splits."""
    verdicts = hand_verdicts(out_dir)
    fld = lambda f: f["field"].split(":", 1)[1]
    lines = [f"# Trace bench table, two readers (D-42, D-44), {time.strftime('%Y-%m-%d')}",
             "",
             "**No recall measured.** Every as-agreed record here is a proxy drafted by a model from the task statement "
             "alone [C], or reused as drafted by an earlier run (the drafter column names which); every delivered value is a model's read of one link [C]; "
             "the class is tier 1's, deterministic given those reads [D]. Every read below the 0.8 threshold was read a "
             "second time by a fresh reader context of another model (same prompt, no sight of the first answer); two "
             "model readers are not two raters of record. Nothing here leaves the machine until the project has read it (D-30).",
             "",
             f"Mode: **{mode}**. Prompts: {P.DRAFTERS[DRAFTER_V][0]}; {P.READERS[READER_V][0]}, both reads. Units: one field at one "
             "link. **Finding** (D-44): two readers, the second a different model (Opus where the first is Sonnet), give the "
             "same loss class, both at 0.8 or above; every first read below 0.8, and every first read that gives a class "
             "other than PRESERVED, is read twice" + (", and so is every PRESERVED first read at a final output or a code link "
             "(rule d44-preserved, chunk 2)" if SECOND_RULE == "d44-preserved" else "") + ". **One reader only**: a loss read once, its second read missing (kept "
             "apart, never a finding). Agreement between two readers is not truth. **Proposal**: both readers give the same loss "
             "class and one or both is below 0.8 (for tier 3, not a finding). **Split**: the two readers give different "
             "classes and at least one gives a loss (one says carried, or not addressed, or another loss); every split "
             "is read against the raw link text by hand (hand-check.md). A field read twice where neither reader gives "
             "a loss is in none of the three. Result: the row after the hand check; final only when no split is open.",
             "",
             "| find | run | declared | decided | result after hand check | findings (two readers, same loss, both 0.8 or above) | one reader only (loss read once, second read missing) | proposals (two readers, same loss, below 0.8) | splits | splits by hand: r1 · r2 · neither · open | unexpected | drafter | reader 1 | reader 2 | second reads | tags |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        fin = final_result(r, verdicts) if r.get("fields") else {"status": r.get("status", ""), "tally": None}
        r["final"] = fin
        found, props, splits = [], [], []
        for f in r.get("fields", []):
            found.append(first_of(f.get("findings", []), f, lambda p, f: (
                f"{p['class']} `{fld(f)}`: {short_value(f['agreed'])} → {short_value(p['value'])} at {p['link']}"
                if "class" in p else f"{p['reader1']['class']} `{fld(f)}` at {p['link']}, two readers")))
            props.append(first_of(f.get("proposals2", []), f, lambda p, f: (
                f"{p['reader1']['class']} `{fld(f)}`: {short_value(f['agreed'])} → {short_value(p['reader2']['value'])} "
                f"at {p['link']}, conf. {p['reader1']['confidence']} / {p['reader2']['confidence']}")))
            splits.append(first_of(f.get("splits", []), f, lambda p, f: (
                f"`{fld(f)}` at {p['link']}: r1 {p['reader1']['class']} ({p['reader1']['confidence']}) / "
                f"r2 {p['reader2']['class']} ({p['reader2']['confidence']})")))
        found, props, splits = [x for x in found if x], [x for x in props if x], [x for x in splits if x]
        if fin["status"] in ("found", "loss by hand check"):
            codes = r.get("mast")
            unexpected = ("n/a (no MAST label)" if codes is None else
                          "no: MAST sets 1.1" if "1.1" in codes else f"yes: MAST codes {', '.join(codes) or 'none'}")
        else:
            unexpected = "n/a"
        t = fin.get("tally")
        tally = "" if not t else (f"{t['agree with reader 1']} · {t['agree with reader 2']} · {t['neither']} · {t['open']}")
        lines.append("| " + " | ".join([
            cell(r["find"], 70), r["run"], str(r.get("declared", "")), str(r.get("decided", "")), cell(fin["status"], 60),
            f"{r.get('n_findings', 0)}: " + cell("; ".join(found) or "none", 300), str(r.get("n_one_reader", 0)),
            f"{r.get('n_proposals', 0)}: " + cell("; ".join(props) or "none", 300),
            f"{r.get('n_splits', 0)}: " + cell("; ".join(splits) or "none", 300), tally, unexpected,
            cell(r.get("drafter", ""), 40), cell(r.get("reader", ""), 40), cell(r.get("second_reader", ""), 40),
            str(r.get("second_reads", "")),
            "record [C] · reads [C] · class [D] given reads · hand [C]" + (" · dry-run fixture" if r.get("mode") == "dry-run" else "")]) + " |")
    lines += ["", "## Per field, read twice", "",
              "Every field with a proposal or a split, link by link: reader 1 and reader 2 as class (confidence) and quote.", ""]
    for r in rows:
        items = [(f, x) for f in r.get("fields", []) for x in f.get("second", []) if x["kind"]]
        lines.append(f"**{r['run']}** ({r.get('final', {}).get('status', r.get('status', ''))}; {r.get('links', 0)} links; "
                     f"first reads below 0.8: {r.get('second_reads', 0)}; proposals {r.get('n_proposals', 0)}, splits "
                     f"{r.get('n_splits', 0)})")
        for f, x in items:
            a, b = x["reader1"], x["reader2"]
            lines.append(f"- {x['kind']} `{f['field']}` {x['link']}, agreed {short_value(f['agreed'])}: r1 {a['class']} "
                         f"({a['status']}, {a['confidence']}) \"{cell(a['quote'], 140)}\" / r2 {b['class']} ({b['status']}, "
                         f"{b['confidence']}{'; ' + b['why_not_used'] if b.get('why_not_used') else ''}) \"{cell(b['quote'], 140)}\"")
        lines.append("")
    hc = os.path.join(out_dir, "hand-check.md")
    if os.path.exists(hc):
        lines += ["The hand check is in `hand-check.md` beside this table.", ""]
    text = "\n".join(lines) + "\n"
    with open(os.path.join(out_dir, "table.md"), "w", encoding="utf-8") as f:
        f.write(text)
    with open(os.path.join(out_dir, "rows.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    return text


def table(rows: List[Dict[str, Any]], out_dir: str, mode: str) -> str:
    if any("second_reader" in r for r in rows):
        return table_second(rows, out_dir, mode)
    lines = [f"# Trace bench table, {time.strftime('%Y-%m-%d')}",
             "",
             "**No recall measured.** Every as-agreed record here is a proxy drafted by a model from the task statement "
             "alone [C]; every delivered value is one model's read of one link [C]; the class is tier 1's, deterministic "
             "given those reads [D]. One read per field per link, no second rater. Nothing here leaves the machine "
             "until the project has read it (D-30).",
             "",
             f"Mode: **{mode}**. Prompts: {P.DRAFTERS[DRAFTER_V][0]}; {P.READERS[READER_V][0]}. Columns: find · run · fields declared (typed, by the drafter) · fields decided (tier 1 "
             "gave a class at one link at least) · result · classes found, by field: agreed → arrived, at which link · "
             "the unexpected (a loss where MAST's own annotation does not set 1.1, disobey task specification) · "
             "proposals (a loss tier 1 gives only when reads below the 0.8 threshold are used: for tier 3, not a finding) · "
             "drafter · reader · lowest confidence among the reads used · tags.",
             "",
             "| find | run | declared | decided | result | classes found: field, agreed → arrived, link | unexpected | proposals below 0.8 (tier 3) | drafter | reader | min conf. | tags |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        found = []
        for f in r.get("fields", []):
            for p in f["losses"][:1]:  # the first loss of the field; every link is in reads.jsonl and tier1/
                more = len(f["losses"]) - 1
                found.append(f"{p['class']} `{f['field'].split(':', 1)[1]}`: {short_value(f['agreed'])} → "
                             f"{short_value(p['value'])} at {p['link']}" + (f" (+{more} links)" if more else ""))
        props = []
        for f in r.get("fields", []):
            for p in f.get("proposed_losses", [])[:1]:
                more = len(f["proposed_losses"]) - 1
                props.append(f"{p['class']} `{f['field'].split(':', 1)[1]}`: {short_value(f['agreed'])} → "
                             f"{short_value(p['value'])} at {p['link']}, conf. {p['confidence']}" + (f" (+{more} links)" if more else ""))
        if r.get("status") == "found":
            codes = r.get("mast")
            unexpected = ("n/a (no MAST label)" if codes is None else
                          "no: MAST sets 1.1" if "1.1" in codes else f"yes: MAST codes {', '.join(codes) or 'none'}")
        else:
            unexpected = "n/a"
        note = r.get("note") or ""
        lines.append("| " + " | ".join([
            cell(r["find"], 70), r["run"], str(r.get("declared", "")), str(r.get("decided", "")),
            cell(r.get("status", "") + (f" ({note})" if note else ""), 70),
            cell("; ".join(found) or "none", 400), unexpected, cell("; ".join(props) or "none", 400), cell(r.get("drafter", ""), 40), cell(r.get("reader", ""), 40),
            "" if r.get("min_confidence") is None else f"{r['min_confidence']:.2f}",
            "record [C] · reads [C] · class [D] given reads" + (" · dry-run fixture" if r.get("mode") == "dry-run" else "")]) + " |")
    lines += ["", "## Per field", ""]
    for r in rows:
        lines.append(f"**{r['run']}** ({r.get('status', '')}; {r.get('links', 0)} links; drafter fields dropped by the "
                     f"quote or schema check: {r.get('dropped_by_check', 0)}; reads refused by the quote, confidence or "
                     f"shape check: {r.get('reads_refused', 0)})")
        for f in r.get("fields", []):
            seq = " ".join(f"{p['link']}:{p['class'][:4]}" for p in f["per_link"] if p["decided"]) or "nothing decided"
            lines.append(f"- `{f['field']}` {f['modality']}, agreed {short_value(f['agreed'])}: {seq}")
            for p in f.get("proposed_losses", [])[:1]:
                lines.append(f"  - proposal (below 0.8) {p['class']} first at {p['link']}, read {short_value(p['value'])} "
                             f"(confidence {p['confidence']}), quote: \"{cell(p['quote'], 200)}\"")
            for p in f["losses"][:1]:
                lines.append(f"  - first loss {p['link']}, read {short_value(p['value'])} (confidence {p['confidence']}), "
                             f"quote: \"{cell(p['quote'], 200)}\"; tier 1: {cell(p['reason'], 160)}")
        lines.append("")
    hc = os.path.join(out_dir, "hand-check.md")
    if os.path.exists(hc):
        lines += [open(hc, encoding="utf-8").read().rstrip(), ""]
    text = "\n".join(lines) + "\n"
    with open(os.path.join(out_dir, "table.md"), "w", encoding="utf-8") as f:
        f.write(text)
    with open(os.path.join(out_dir, "rows.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    return text


# ---------- the chunk block (D-48) ----------
SITES = ("first hand-off", "middle hop", "code link", "final output")
STATES = ("as-briefed", "as-delivered")
BLOCK_LINES = ("Runs", "Findings", "Proposals", "Splits", "Hand agreement", "Losses by site", "Losses by state",
               "Unexpected", "Rule delta", "Regression", "Next five")
DELTA_PARTS = ("reader", "drafter", "converter", "library")


def chunk_counts(rows: List[Dict[str, Any]], verdicts: Dict[tuple, str]) -> Dict[str, Any]:
    """The mechanical part of a chunk block: field-link units by kind, the hand tally of the splits, and every loss
    by site and by state (findings, proposals, and splits the hand check resolved to a loss, apart)."""
    kinds = ("finding", "proposal", "split by hand")
    by_site = {s: dict.fromkeys(kinds, 0) for s in SITES}
    by_state = {s: dict.fromkeys(kinds, 0) for s in STATES}
    tally = {"agree with reader 1": 0, "agree with reader 2": 0, "neither": 0, "open": 0}
    n = {"finding": 0, "proposal": 0, "split": 0}
    for r in rows:
        for f in r.get("fields", []):
            units = [("finding", x) for x in f.get("findings", [])] + [("proposal", x) for x in f.get("proposals2", [])]
            for x in f.get("splits", []):
                n["split"] += 1
                v = verdicts.get((r["run"], f["field"], x["link"]))
                tally[v or "open"] += 1
                side = {"agree with reader 1": "reader1", "agree with reader 2": "reader2"}.get(v or "")
                if side and x[side]["class"] in LOSS:
                    units.append(("split by hand", x))
            for kind, x in units:
                if kind != "split by hand":
                    n[kind] += 1
                by_site[x.get("site") or "middle hop"][kind] += 1
                by_state[x.get("state") or "as-briefed"][kind] += 1
    n["one reader only"] = sum(len(f.get("one_reader", [])) for r in rows for f in r.get("fields", []))
    return {"runs": len(rows), "links": sum(r.get("links", 0) for r in rows), "n": n, "tally": tally,
            "by_site": by_site, "by_state": by_state}


def _cells(d: Dict[str, Dict[str, int]]) -> str:
    return " · ".join(f"{k} {v['finding']} / {v['proposal']} / {v['split by hand']}" for k, v in d.items())


def chunk_block(number: int, date: str, rows: List[Dict[str, Any]], verdicts: Dict[tuple, str], prose: Dict[str, Any]) -> str:
    """One block of chunks.md. `prose` holds what a person writes: unexpected (one paragraph), delta (a mapping of
    reader, drafter, converter, library to a list of (rule, row)), regression, next_five (a list of (find, why))."""
    c = chunk_counts(rows, verdicts)
    t = c["tally"]
    lines = [f"## Chunk {number} · {date}", "",
             f"- **Runs**: {c['runs']} runs, {c['links']} links; units are one field at one link; [C] reads, [D] class given reads",
             f"- **Findings**: {c['n']['finding']} (two readers, same loss, both 0.8 or above); one reader only, apart: "
             f"{c['n']['one reader only']}",
             f"- **Proposals**: {c['n']['proposal']}",
             f"- **Splits**: {c['n']['split']}",
             f"- **Hand agreement**: of {c['n']['split']} splits, reader 1 {t['agree with reader 1']} · reader 2 "
             f"{t['agree with reader 2']} · neither {t['neither']} · open {t['open']}",
             f"- **Losses by site** (finding / proposal / split resolved to a loss by hand): {_cells(c['by_site'])}",
             f"- **Losses by state** (same three): as-briefed restatement {c['by_state']['as-briefed']['finding']} / "
             f"{c['by_state']['as-briefed']['proposal']} / {c['by_state']['as-briefed']['split by hand']} · as-delivered "
             f"output {c['by_state']['as-delivered']['finding']} / {c['by_state']['as-delivered']['proposal']} / "
             f"{c['by_state']['as-delivered']['split by hand']}",
             f"- **Unexpected**: {' '.join(str(prose.get('unexpected', '')).split())}"]
    if prose.get("value"):
        # D-54: per finding, the seller's three lines (the loss in the task's own terms, what the hold would have done
        # at that link, the opportunity), under a head naming the run, the link and the field
        lines.append("- **Business value** (D-54; a seller's reading of each row, no figure beyond the row's own):")
        for head, loss, hold, opp in prose["value"]:
            lines += [f"  - {head}", f"    - loss: {loss}", f"    - hold: {hold}", f"    - opportunity: {opp}"]
    lines.append("- **Rule delta**:")
    for part in DELTA_PARTS:
        items = (prose.get("delta") or {}).get(part) or [("none", "no row forced a change")]
        for rule, row in items:
            lines.append(f"  - {part}: {rule} (forced by {row})")
    lines.append(f"- **Regression**: {' '.join(str(prose.get('regression', '')).split())}")
    lines.append("- **Next five**:")
    for find, why in prose.get("next_five") or []:
        lines.append(f"  - {find}: {why}")
    return "\n".join(lines) + "\n"


def check_block(text: str) -> List[str]:
    """What a chunk block lacks: every block line in order, the four parts of the rule delta, five next finds, each
    delta rule naming the row that forced it. An empty list is a well-formed block."""
    problems = []
    if not re.match(r"^## Chunk \d+ · \d{4}-\d{2}-\d{2}", text):
        problems.append("heading '## Chunk <n> · <date>' missing")
    at = -1
    for name in BLOCK_LINES:
        i = text.find(f"- **{name}**")
        if i < 0:
            problems.append(f"line '{name}' missing")
        elif i < at:
            problems.append(f"line '{name}' out of order")
        at = max(at, i)
    for part in DELTA_PARTS:
        rows = re.findall(rf"^  - {part}: .+ \(forced by .+\)$", text, re.M)
        if not rows:
            problems.append(f"rule delta '{part}' missing or without 'forced by'")
    nxt = text.split("- **Next five**", 1)[-1]
    if len(re.findall(r"^  - .+: .+$", nxt, re.M)) != 5:
        problems.append("next five: not five finds with a reason")
    if "- **Unexpected**: " in text and len(text.split("- **Unexpected**: ", 1)[1].split("\n", 1)[0].strip()) < 20:
        problems.append("unexpected: no paragraph")
    if "- **Business value**" in text:
        # optional since chunk 2 (D-54); where present it sits between Unexpected and Rule delta, and every entry
        # carries the three lines
        body = text.split("- **Business value**", 1)[1].split("\n", 1)[-1].split("\n- **", 1)[0]
        if not (text.find("- **Unexpected**") < text.find("- **Business value**") < text.find("- **Rule delta**")):
            problems.append("business value: not between Unexpected and Rule delta")
        entries = re.split(r"(?m)^  - ", body)[1:]
        if not entries:
            problems.append("business value: no entry")
        for e in entries:
            keys = re.findall(r"(?m)^    - (loss|hold|opportunity): \S", e)
            if keys != ["loss", "hold", "opportunity"]:
                problems.append(f"business value: entry {e.splitlines()[0][:50]!r} lacks loss, hold and opportunity in order")
    return problems


def blocks_of(chunks_md: str) -> List[str]:
    parts = re.split(r"(?m)^(?=## Chunk \d+ )", chunks_md)
    return [p for p in parts if p.startswith("## Chunk ")]


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--mode", choices=("api", "exchange", "dry-run"), default=None)
    ap.add_argument("--exchange", default=None, help="the exchange folder (exchange mode)")
    ap.add_argument("--lib", default=os.path.join(HERE, "..", "..", "tools", "claim-ledger"),
                    help="the claim-ledger folder whose src/as_agreed is used (read only)")
    ap.add_argument("--drafter-model", default=DRAFTER_MODEL)
    ap.add_argument("--reader-model", default=READER_MODEL)
    ap.add_argument("--only", default="", help="comma-separated run folder names")
    ap.add_argument("--second-reader", action="store_true",
                    help="D-42: read every field below the 0.8 threshold a second time, with a fresh prompt context")
    ap.add_argument("--second-reader-model", default=READER_MODEL)
    ap.add_argument("--exchange2", default=None,
                    help="the exchange folder of the second reader (exchange mode; default --exchange)")
    ap.add_argument("--records", default=None,
                    help="an earlier out_dir whose <run>/commitments.json are reused as drafted (no drafter call)")
    ap.add_argument("--drafter-version", choices=sorted(P.DRAFTERS), default=P.DRAFTER_DEFAULT,
                    help="drafter prompt: v1 (chunk 1 and before) or v2 (the chunk 1 rule delta)")
    ap.add_argument("--reader-version", choices=sorted(P.READERS), default=P.READER_DEFAULT,
                    help="reader prompt: v2 (chunk 1 and before) or v3 (the chunk 1 rule delta)")
    ap.add_argument("--second-rule", choices=SECOND_RULES, default="d44-preserved",
                    help="which first reads are read twice: d44 (chunk 1) or d44-preserved (chunk 2: also every "
                         "PRESERVED read at a final output or a code link)")
    a = ap.parse_args(argv)
    global READER_V, DRAFTER_V, SECOND_RULE
    READER_V, DRAFTER_V, SECOND_RULE = a.reader_version, a.drafter_version, a.second_rule
    load_lib(a.lib)
    mode = a.mode or ("api" if models.api_available() else "dry-run")
    drafter = models.make_caller(mode, "drafter", a.drafter_model, a.exchange)
    reader = models.make_caller(mode, "reader", a.reader_model, a.exchange)
    reader2 = (models.make_caller(mode, "reader2", a.second_reader_model, a.exchange2 or a.exchange)
               if a.second_reader else None)
    names = sorted(n for n in os.listdir(a.runs_dir) if not n.startswith(("_", "."))
                   and os.path.isdir(os.path.join(a.runs_dir, n)))
    if a.only:
        keep = {s.strip() for s in a.only.split(",") if s.strip()}
        names = [n for n in names if n in keep]
    os.makedirs(a.out_dir, exist_ok=True)
    rows = []
    for n in names:
        rec = os.path.join(a.records, n, "commitments.json") if a.records else None
        row = bench_run(n, load_run(os.path.join(a.runs_dir, n)), os.path.join(a.out_dir, n), drafter, reader,
                        reader2, rec)
        rows.append(row)
        extra = (f"\tfindings {row.get('n_findings')}\tproposals {row.get('n_proposals')}\tsplits {row.get('n_splits')}"
                 if "n_splits" in row else "")
        print(f"{n}\t{row.get('status')}\tdeclared {row.get('declared', '-')}\tdecided {row.get('decided', '-')}{extra}")
    table(rows, a.out_dir, mode)
    pending = [r for r in rows if str(r.get("status", "")).startswith("pending")]
    if pending:
        print(f"{len(pending)} runs wait on answers in {a.exchange2 or a.exchange}/pending", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
