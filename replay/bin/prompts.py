"""The drafter and the reader: their prompts, the parsing of their answers, and the deterministic checks on them.

Drafter: task statement only -> the as-agreed record, typed only where the statement's words type it, every field
quoted verbatim (the quote is checked by script; a field whose quote is not in the statement is dropped and logged).
Reader: one link's text and the escalations of that link (SPEC §4's Escalation) -> per field the delivered value,
a confidence and the quote it was read from, or None (the link does not address the field). The reader returns a
value, not a drift class: tier 1 decides the class from the value, so the class stays deterministic given the read.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

OBLIGOR, OBLIGEE = "the-system", "the-requester"  # a task statement names neither party; set by the harness, not drafted
ID = re.compile(r"[^a-z0-9_-]+")
THRESHOLD = 0.8  # the spec's default tier 2 threshold (SPEC §4); a read below it is not written into the link
DRAFTER_VERSION = "drafter-v1 (2026-11-04)"
DRAFTER_V2_VERSION = "drafter-v2 (2026-11-05): a limit on a kind of thing is a criterion, never a set"
DRAFTER_V2_RULE = """   A rule that limits a kind of thing ("changes limited to non-test implementation files", "only official sources")
   is a forbidden_act or a deliverable criterion, never a set: a set lists the values the field itself takes.
"""
DRAFTERS = {"v1": (DRAFTER_VERSION, ""), "v2": (DRAFTER_V2_VERSION, DRAFTER_V2_RULE)}
DRAFTER_DEFAULT = "v2"  # chunk 1 drafted with v1; later chunks draft with v2
READER_VERSION = "reader-v2 (2026-11-04): an artifact carries a field only by what it does"
READER_V3_VERSION = ("reader-v3 (2026-11-05): v2 plus three rules from the chunk 1 hand check: recompute an answer from "
                     "the task's numbers; naming or reviewing is not handing over; a brief carries what it states")
# reader-v1 counted words inside an artifact (a prompt string such as "Enter number (1-9)") as carrying the field;
# v2 adds the rule below. v2 was written after reading v1's answers on t03, and is applied to every run alike.
TYPES = ("amount", "count", "range", "set", "date", "forbidden_act", "deliverable")

DRAFTER = """You draft the as-agreed record of one task from its task statement alone. The record lists what the statement
commits the system to, field by field, so that a script can later check each field against what the system delivered.

Rules.
1. Use only the task statement below. Add nothing that the statement does not say, however usual it is for such a task.
2. Type a field only where the statement's own words type it:
   - amount: a sum of money or a quantity with a unit ("up to 18,400 dollars");
   - count: a number of things ("three files", "a 9x9 grid");
   - range: a span of allowed values ("from 1 to 9", "1 through 9", "between 2 and 5");
   - set: an enumerated list of allowed or excluded values;
   - date: a calendar date or deadline written in the statement;
   - forbidden_act: something the statement says must not be done ("do not", "must not", "never", "without");
   - deliverable: a thing or a behaviour the statement names as part of what is delivered ("a function named X",
     "the program should allow the player to input values").
{v2_rule}   Everything else (style, quality, open choices) is not a field: put its words in `untyped`.
3. Every field carries `quote`: a contiguous span copied character for character from the statement. A field you cannot
   quote is not written. The script drops any field whose quote is not found in the statement.
4. Shapes, by type:
   - range "a to b": "limit": {"<name>_min": {"min": a}, "<name>_max": {"max": b}}
   - at most n: "limit": {"<name>": {"max": n}}; at least n: "limit": {"<name>": {"min": n}}
   - an exact number or size, or an enumerated set: "limit": {"<name>": {"in": [v, ...]}}; excluded values: {"not_in": [...]}
   - add "unit" inside the bound only when the statement names one ("unit": "USD")
   - date: "deadline": "YYYY-MM-DD"
   - forbidden_act and deliverable: "criterion": {"text": "<one sentence: what is true when it is met>", "key": "<snake_case>"};
     for a forbidden act the sentence says the act is not performed
   Numbers are JSON numbers; names, ids and keys use lower case letters, digits, "_" and "-".
5. modality, from the statement's verb: MUST (must, shall, is required, an imperative), SHOULD (should), MAY (may, can),
   MUST_NOT (a forbidden act).
6. `act` is the verb and object the field belongs to, in the statement's words.

Return one JSON object and nothing else, of this shape:
{"act": "<the main act, verb and object>", "act_quote": "<verbatim span>",
 "fields": [{"id": "<id>", "type": "<one of: amount, count, range, set, date, forbidden_act, deliverable>", "act": "<verb and object>",
             "modality": "MUST", "quote": "<verbatim span>", "limit": {...} | "deadline": "..." | "criterion": {...}}],
 "untyped": [{"quote": "<verbatim span>", "why": "<why it has no type>"}]}

Task statement:
<<<
{task}
>>>

<request>{request}</request>
"""

READER = """You read one link of a multi-agent run: one message or artifact that one agent handed to another. For each field
below, say what this link carries for it. The fields come from a record of what was agreed, drafted from the task
statement; the agreed value is given for each.

For each field give exactly one status:
- "carried": the link states the field, or the artifact it hands over (code, an answer, a plan) enforces or delivers it.
  Give `value` in the shape the field asks for (below).
- "not_carried": the link hands over or restates the very thing the field governs (the code that takes the value, the final
  answer, the plan that lists the limits) and the field is missing from it: not stated, not checked, not delivered.
  Give `value`: null.
- "not_addressed": the link does not deal with the thing the field governs. Give `value`: null.
When the link hands over an artifact (code, a configuration, a computed answer), judge the artifact by what it does:
the field is carried only when the artifact enforces or delivers it. Words inside the artifact that it does not act on
(a prompt string, a comment, a docstring, a label) do not carry the field: if the artifact takes or produces the value
without enforcing the field, the status is "not_carried", quoting the line that takes or produces the value.
{v3_rules}`quote`: the shortest span (at most 300 characters) copied character for character from the link text that shows your
answer; for not_carried, the span where the field should have been (for example the line that accepts the value).
For not_addressed give "". The script drops any read whose quote is not in the link text.
`confidence`: a number from 0 to 1.
Read this link only. Do not judge whether the run succeeded, and do not guess what other links say.

Fields:
{fields}

Return one JSON object and nothing else:
{"reads": [{"field": "<field path>", "status": "carried|not_carried|not_addressed", "value": ..., "confidence": 0.0, "quote": "..."}]}

Link {link_id} (from {sender}, {kind}):
<<<
{text}
>>>

<request>{request}</request>
"""


# reader-v3: three rules, each written after the chunk 1 hand check (studies/trace-bench/chunks.md, chunk 1)
V3_RULES = """When the link states an answer to the task's question and the task's own numbers determine that answer, work it
out from the task's numbers: a stated answer that differs from yours, or that is hedged among several values, is
"carried" with value false.
A link that names the thing a field governs without giving its value (an evaluation saying "the initial shipment is
right"), or that reviews, diagnoses or reports an artifact without handing that artifact over, does not address the
field: "not_addressed". Use "not_carried" only when the link hands over that very thing and the field is missing from it.
An instruction, plan or hand-off note that states the requirement to the next agent carries it ("carried", value true
for a criterion), even though nothing is delivered yet.
"""
# reader-v4: v3 with its second rule narrowed after the chunk 1 regression lost t07 L16 (an Executor report that runs
# the fix and shows the attribute missing was read as "not addressed" under v3)
V4_RULES = """When the link states an answer to the task's question and the task's own numbers determine that answer, work it
out from the task's numbers: a stated answer that differs from yours, or that is hedged among several values, is
"carried" with value false.
A link that names the thing a field governs without giving its value (an evaluation saying "the initial shipment is
right"), or that reviews or diagnoses an artifact without handing it over and without running it, does not address the
field: "not_addressed". Use "not_carried" only when the link hands over that very thing and the field is missing from it.
A link that reports running the artifact (a test, an execution and its output) shows what the artifact does: judge the
field by that output.
An instruction, plan or hand-off note that states the requirement to the next agent carries it ("carried", value true
for a criterion), even though nothing is delivered yet.
"""
assert V4_RULES != V3_RULES
READER_V4_VERSION = ("reader-v4 (2026-11-05): v3 with rule 2 narrowed: a report of running the artifact is read as the "
                     "artifact's behaviour (forced by the chunk 1 regression, t07 L16)")
READERS = {"v2": (READER_VERSION, ""), "v3": (READER_V3_VERSION, V3_RULES), "v4": (READER_V4_VERSION, V4_RULES)}
READER_DEFAULT = "v4"  # chunk 1 ran on v2; the regression ran on v3 (lost t07 L16), then on v4; later chunks run on v4


def squash(s: str) -> str:
    return " ".join(str(s).split()).casefold()


def quoted(quote: Any, text: str) -> bool:
    """A quote counts when it is non-empty and found in the text under whitespace and case folding."""
    q = squash(quote or "").strip("\"'“”‘’ ")
    return bool(q) and q in squash(text)


def parse_json(answer: str) -> Any:
    """The first JSON object in a model's answer (a code fence or a sentence around it is tolerated, and logged raw)."""
    s = answer.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", s, re.S)
    if fence:
        s = fence.group(1)
    start = s.find("{")
    if start < 0:
        raise ValueError("no JSON object in the answer")
    obj, _ = json.JSONDecoder().raw_decode(s[start:])
    return obj


def fill(template: str, **values: str) -> str:
    """One pass over the template's {name} slots, so a link's own text is never scanned for slots."""
    return re.sub(r"\{(\w+)\}", lambda m: values.get(m.group(1), m.group(0)), template)


def body_of(prompt: str) -> str:
    """The text between the prompt's <<< and >>> fences: the task statement, or the link text."""
    a = prompt.rindex("<<<\n") + 4
    return prompt[a:prompt.index("\n>>>", a)]


def slug(s: str) -> str:
    return ID.sub("-", str(s).lower()).strip("-")[:60] or "x"


# ---------- drafter ----------
def drafter_prompt(task: str, version: str = "v1") -> str:
    return fill(DRAFTER, task=task, request=json.dumps({"role": "drafter"}), v2_rule=DRAFTERS[version][1])


def record_from_draft(draft: Dict[str, Any], task: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, str]]:
    """Library commitments (SPEC §1.2) from the drafter's answer: one commitment per typed field, so that each field is
    checked on its own; the main act as one more commitment with no typed field. Returns (commitments, dropped, quotes)."""
    from as_agreed.commitment import Commitment  # the library's own validation is the schema check
    commitments: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []
    quotes: Dict[str, str] = {}
    act = " ".join(str(draft.get("act") or "").split()) or "do the task as stated"
    if draft.get("act_quote") and quoted(draft["act_quote"], task):
        quotes["task"] = draft["act_quote"]
    main = {"commitment_id": "task", "act": act, "obligor": OBLIGOR, "obligee": OBLIGEE, "modality": "MUST"}
    Commitment.from_mapping(main)
    commitments.append(main)
    seen = {"task"}
    for item in draft.get("fields") or []:
        why = None
        if not isinstance(item, dict):
            why = "not an object"
        elif item.get("type") not in TYPES:
            why = f"type {item.get('type')!r} is not one of {', '.join(TYPES)}"
        elif not quoted(item.get("quote"), task):
            why = "its quote is not in the task statement"
        if why:
            dropped.append({"field": item, "why": why})
            continue
        cid = slug(item.get("id") or item.get("type"))
        while cid in seen:
            cid += "-2"
        rec: Dict[str, Any] = {"commitment_id": cid, "act": " ".join(str(item.get("act") or act).split()),
                               "obligor": OBLIGOR, "obligee": OBLIGEE, "modality": item.get("modality") or "MUST"}
        carried: Dict[str, str] = {}
        if item.get("limit"):
            rec["limit"] = {slug(k).replace("-", "_"): v for k, v in dict(item["limit"]).items()}
            carried.update({f"limit.{k}": k for k in rec["limit"]})
        elif item.get("deadline"):
            rec["deadline"] = item["deadline"]
            carried["deadline"] = "deadline"
        elif isinstance(item.get("criterion"), dict) and item["criterion"].get("key"):
            key = slug(item["criterion"]["key"]).replace("-", "_")
            rec["acceptance_criteria"] = [{"criterion_id": key, "text": item["criterion"].get("text") or key,
                                           "verification": "machine_checkable", "field": key}]
        else:
            dropped.append({"field": item, "why": "no limit, deadline or criterion"})
            continue
        if carried:
            rec["carried_by"] = carried
        try:
            Commitment.from_mapping(rec)
        except (ValueError, TypeError, OverflowError) as e:  # OverflowError: the library's number() on a huge int
            dropped.append({"field": item, "why": f"refused by the record schema: {type(e).__name__}: {e}"})
            continue
        seen.add(cid)
        commitments.append(rec)
        quotes[cid] = item["quote"]
    return commitments, dropped, quotes


def typed_paths(rec: Dict[str, Any]) -> List[str]:
    """The typed field paths of one library commitment: what tier 1 can decide when a link carries a value."""
    out = [f"limit.{k}" for k in (rec.get("limit") or {})]
    if rec.get("deadline"):
        out.append("deadline")
    out += [f"acceptance_criteria.{c['criterion_id']}" for c in rec.get("acceptance_criteria") or []]
    return out


def output_key(rec: Dict[str, Any], path: str) -> str:
    if path.startswith("acceptance_criteria."):
        cid = path.split(".", 1)[1]
        return next(c["field"] for c in rec["acceptance_criteria"] if c["criterion_id"] == cid)
    return (rec.get("carried_by") or {})[path]


def shape_of(rec: Dict[str, Any], path: str) -> str:
    if path.startswith("limit."):
        bound = rec["limit"][path.split(".", 1)[1]]
        if isinstance(bound, str):
            return "the limit as the link words it (text)"
        kind = next(k for k in bound if k != "unit")
        unit = f', "unit": "{bound["unit"]}"' if bound.get("unit") else ""
        return (f'a bound of the same kind, {{"{kind}": ...{unit}}}, as the link states or enforces it; or a single '
                f'value the link delivers for it, as a JSON number or string')
    if path == "deadline":
        return 'a date "YYYY-MM-DD"'
    return "true if what this link delivers meets the criterion, false if it delivers the artifact and it does not"


# ---------- reader ----------
def reader_prompt(escalations: List[Any], rec_by_id: Dict[str, Dict[str, Any]], quotes: Dict[str, str],
                  link_id: str, sender: str, kind: str, read_no: int = 1, extra: Optional[Dict[str, Any]] = None,
                  version: str = "v2") -> str:
    """The reader-v2 prompt over these escalations. read_no 2 is the second, independent read (D-42): the same prompt
    over the fields whose first read fell below the threshold, marked only in the request block so that its hash
    differs; it carries nothing of the first answer."""
    lines, req_fields = [], []
    for e in escalations:
        rec = rec_by_id[e.commitment.commitment_id]
        key = output_key(rec, e.field)
        agreed = e.agreed if not e.field.startswith("acceptance_criteria.") else {"criterion": e.agreed}
        lines.append(f"- field `{e.commitment.commitment_id}:{e.field}` ({e.commitment.modality}: {e.commitment.act}); "
                     f"agreed: {json.dumps(agreed, ensure_ascii=False)}; the task's words: \"{quotes.get(e.commitment.commitment_id, '')}\"; "
                     f"answer shape: {shape_of(rec, e.field)}")
        req_fields.append({"field": f"{e.commitment.commitment_id}:{e.field}", "key": key})
    text = escalations[0].link_text
    req: Dict[str, Any] = {"role": "reader", "link": link_id, "fields": req_fields}
    if read_no != 1:  # pass 1 keeps the request of the first run byte for byte, so its stored answers are reused
        req["read"] = read_no
    if extra:  # e.g. {"confirm": "loss"}: the second read of a loss read at or above the threshold (D-44)
        req.update(extra)
    return fill(READER, fields="\n".join(lines), link_id=link_id, sender=str(sender), kind=str(kind), text=text,
                request=json.dumps(req, ensure_ascii=False), v3_rules=READERS[version][1])


def parse_reads(answer: str, escalations: List[Any], link_text: str) -> List[Dict[str, Any]]:
    """One read per escalation: the model's answer, checked. `used` says whether tier 1 gets it, `why` when not."""
    try:
        got = {str(r.get("field")): r for r in parse_json(answer).get("reads", []) if isinstance(r, dict)}
        error = None
    except (ValueError, AttributeError) as e:
        got, error = {}, f"answer not parsed: {e}"
    out = []
    for e in escalations:
        name = f"{e.commitment.commitment_id}:{e.field}"
        r = got.get(name) or got.get(e.field) or {}
        status = r.get("status")
        try:
            conf = float(r.get("confidence"))
        except (TypeError, ValueError):
            conf = None
        read = {"field": name, "status": status, "value": r.get("value"), "confidence": conf, "quote": r.get("quote", "")}
        why = error
        if not why and not r:
            why = "no read for this field in the answer"
        elif not why and status not in ("carried", "not_carried", "not_addressed"):
            why = f"status {status!r} unknown"
        elif not why and status != "not_addressed" and (conf is None or not 0 <= conf <= 1):
            why = "confidence not a number from 0 to 1"
        elif not why and status != "not_addressed" and conf < THRESHOLD:
            why = f"confidence {conf} below the threshold {THRESHOLD}"
        elif not why and status != "not_addressed" and not quoted(read["quote"], link_text):
            why = "its quote is not in the link text"
        elif not why and status == "carried" and read["value"] is None:
            why = "carried with no value"
        read["used"] = why is None and status != "not_addressed"
        # a read refused only for its confidence stands as a proposal for tier 3 (SPEC §4, K25)
        read["proposal"] = bool(why and why.startswith("confidence ") and "below the threshold" in why)
        if why:
            read["why_not_used"] = why
        out.append(read)
    return out


def delivered(read: Dict[str, Any], path: str) -> Any:
    """The value written under the field's output key at this link: tier 1 reads it. A criterion not carried is not
    met (false); a bound or a date not carried is absent (null, which tier 1 reads as DROPPED)."""
    if read["status"] == "not_carried":
        return False if path.startswith("acceptance_criteria.") else None
    return read["value"]
