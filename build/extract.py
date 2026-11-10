#!/usr/bin/env python3
"""Split one MAST-Data row into its task statement and its links, scrub it, and count status
markers per link. Deterministic, standard library only, no model.

    python3 -I -B extract.py <row.json> <trace-dir> <scratch-dir>

<row.json> is one response of the Hugging Face dataset server's rows API (offset=N, length=1)
for mcemri/MAST-Data. Writes <trace-dir>/links.jsonl (first line: the trace's metadata; then
one line per link, scrubbed text and marker counts) and, in <scratch-dir>, the scrubbed task
statement, the scrubbed whole trajectory and, for SWE-bench rows, the reference block the
system did not see. Nothing is fetched; nothing in the row is executed (AG2 messages are
read with ast.literal_eval, which evaluates literals only).

A link is one hand-off artifact (README, "Links"):
  MetaGPT     the human requirement, then each role message after a "NEW MESSAGES:" line
  ChatDev     each role message: a phase's opening instruction ("[Start Chat]") and each reply
              ("A<->B on : Phase, turn N"); system, HTTP, code-update and execution entries are
              not links (they stay in the scrubbed trajectory)
  HyperAgent  the issue, each planner response (an instruction to a child) and each child's
              report to the planner ("X->Planner"); a child's inner steps are counted, not links
  AG2         each message of the two-agent chat
The marker counts use the claim-ledger lexicon (sentences(), markers()), frozen beside this script as
lexicon.py, so the counts rebuild from this folder alone.
"""
import argparse, ast, hashlib, json, os, re, sys

ROLE_MG = re.compile(r"^(SimpleCoder|SimpleTester|SimpleReviewer|Human):\s?(.*)$")
CD_ENTRY = re.compile(r"^\[\d{4}-\d\d-\d\d \d\d:\d\d:\d\d INFO\] ?(.*)$")
CD_ROLE = re.compile(r"^([A-Z][A-Za-z ]+?): \*\*(\[Start Chat\]|(.+?)<->(.+?) on : (\w+), turn (\d+))\*\*")
HA_LINE = re.compile(r"^\s*HyperAgent_\S+ - INFO - (.*)$")
HA_PLANNER = re.compile(r"^Planner's Response:\s?(.*)$")
HA_REPORT = re.compile(r"^(\w+)->Planner:\s?(.*)$")
HA_INNER = re.compile(r"^Inner-(\w+)-Assistant's Response:\s?(.*)$")

HOME = re.compile(r"(/home/|/Users/|[A-Za-z]:\\\\?Users\\\\?)([A-Za-z0-9._-]+)")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PROMPT = re.compile(r"\b([A-Za-z0-9._-]+)@([A-Za-z0-9._-]+):")
SECRET = re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b")
GENERIC_USERS = {"root", "user", "ubuntu", "runner", "app", "admin", "shared", "<user>"}


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class Scrubber:
    """Replaces home-path user segments, e-mail addresses, user@host prompts and token shapes,
    then any standalone occurrence of a user name first seen in a home path."""

    def __init__(self, text):
        self.users = sorted({m.group(2) for m in HOME.finditer(text)} - GENERIC_USERS, key=len, reverse=True)
        self.counts = {"home_path": 0, "email": 0, "user_at_host": 0, "secret": 0, "user_name": 0}

    def __call__(self, s):
        def home(m):
            if m.group(2) in GENERIC_USERS:
                return m.group(0)
            self.counts["home_path"] += 1
            return m.group(1) + "<user>"
        s = HOME.sub(home, s)
        s, n = EMAIL.subn("<email>", s); self.counts["email"] += n
        s, n = PROMPT.subn("<user>@<host>:", s); self.counts["user_at_host"] += n
        s, n = SECRET.subn("<secret>", s); self.counts["secret"] += n
        for u in self.users:
            s, n = re.subn(r"(?<![A-Za-z0-9_])" + re.escape(u) + r"(?![A-Za-z0-9_])", "<user>", s)
            self.counts["user_name"] += n
        return s


def load_ledger():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import lexicon as L  # the frozen copy beside this script
    return L, os.path.join(here, "lexicon.py"), "build/lexicon.py (frozen copy of the claim-ledger lexicon)"


def marker_counts(L, text):
    sents = L.sentences(text)
    c = {"sentences": len(sents), "hedged": 0, "not_found": 0, "strengthened": 0, "sourced": 0, "dated": 0}
    for s in sents:  # one count per marker class a sentence carries; "not found" is both a hedge and a not-found
        m = L.markers(s)
        if m["epistemic"] and L.WEAK.search(m["epistemic"]):
            c["hedged"] += 1
        if m["existential"] in ("not_found", "unknown_stated"):
            c["not_found"] += 1
        if m["epistemic"] and L.STRONG.search(m["epistemic"]) and not L.WEAK.search(m["epistemic"]):
            c["strengthened"] += 1
        if m["provenance"] != "none stated":
            c["sourced"] += 1
        if m["temporal"]:
            c["dated"] += 1
    return c


def split_metagpt(traj):
    lines = traj.splitlines()
    task = re.search(r"CONTENT:\n(.*?)\n-{10,}", traj, re.S).group(1).strip()
    links = [{"from": "Human", "to": "all", "kind": "order", "phase": "UserRequirement", "start": 3, "text": task}]
    cur = None
    for i, ln in enumerate(lines):
        if re.match(r"^\[\d{4}-\d\d-\d\d [\d:]+\] NEW MESSAGES:", ln) or ln.startswith("=== Communication Log Ended"):
            if cur:
                links.append(cur); cur = None
            continue
        m = ROLE_MG.match(ln)
        if m and m.group(1) != "Human":
            if cur:
                links.append(cur)
            cur = {"from": m.group(1), "to": "team", "kind": "message", "phase": m.group(1), "start": i, "text": m.group(2)}
        elif cur is not None:
            cur["text"] += "\n" + ln
    if cur:
        links.append(cur)
    return task, links, {}


def split_chatdev(traj):
    lines = traj.splitlines()
    task = re.search(r"^\*\*task_prompt\*\*: (.*)$", traj, re.M).group(1).strip()
    links = [{"from": "Human", "to": "ChatDev", "kind": "order", "phase": "task_prompt", "start": 0, "text": task}]
    cur = None
    for i, ln in enumerate(lines):
        e = CD_ENTRY.match(ln)
        if e:
            if cur:
                links.append(cur); cur = None
            m = CD_ROLE.match(e.group(1))
            if m:
                if m.group(2) == "[Start Chat]":
                    cur = {"from": m.group(1), "to": None, "kind": "instruction", "phase": None, "start": i, "text": ""}
                else:
                    a, b, phase, turn = m.group(3), m.group(4), m.group(5), int(m.group(6))
                    other = b if m.group(1) == a else a
                    cur = {"from": m.group(1), "to": other, "kind": "reply", "phase": phase, "turn": turn, "start": i, "text": ""}
            continue
        if cur is not None:
            cur["text"] += ("\n" if cur["text"] else "") + ln
    if cur:
        links.append(cur)
    for k, l in enumerate(links):  # an opening instruction takes the phase and addressee of the next reply
        if l["kind"] == "instruction":
            nxt = next((x for x in links[k + 1:] if x["kind"] == "reply"), None)
            if nxt:
                l["phase"] = nxt["phase"]; l["to"] = nxt["from"] if nxt["from"] != l["from"] else nxt["to"]
    return task, links, {}


def split_hyperagent(traj):
    lines = traj.splitlines()
    ps = re.search(r"^problem_statement:\n(.*?)\n^other_data:", traj, re.S | re.M).group(1)
    task = "\n".join(l[2:] if l.startswith("  ") else l for l in ps.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip()
    ref = re.search(r"^other_data:\n(.*?)\n^trajectory:", traj, re.S | re.M)
    links = [{"from": "Human", "to": "Planner", "kind": "order", "phase": "issue", "start": 1, "text": task}]
    cur, inner = None, 0
    for i, ln in enumerate(lines):
        h = HA_LINE.match(ln)
        if h:
            body = h.group(1)
            p, r, n = HA_PLANNER.match(body), HA_REPORT.match(body), HA_INNER.match(body)
            if p or r:
                if cur:
                    links.append(cur)
                if p:
                    cur = {"from": "Planner", "to": None, "kind": "instruction", "phase": "plan", "start": i, "text": p.group(1)}
                else:
                    cur = {"from": r.group(1), "to": "Planner", "kind": "report", "phase": r.group(1), "start": i, "text": r.group(2)}
                continue
            if n:
                inner += 1
                if cur:
                    links.append(cur); cur = None
                continue
            if cur:
                links.append(cur); cur = None
            continue
        if cur is not None:
            cur["text"] += "\n" + ln
    if cur:
        links.append(cur)
    for k, l in enumerate(links):  # a planner instruction is addressed to the child that reports next
        if l["kind"] == "instruction":
            nxt = next((x for x in links[k + 1:] if x["kind"] == "report"), None)
            l["to"] = nxt["from"] if nxt else None
    return task, links, {"inner_steps": inner, "reference": ref.group(1) if ref else ""}


def split_ag2(traj):
    starts = [m.start() for m in re.finditer(r"\{'content':", traj)]
    msgs = []
    for a, b in zip(starts, starts[1:] + [len(traj)]):
        chunk = traj[a:b].rstrip().rstrip(",").rstrip()
        msgs.append(ast.literal_eval(chunk))
    links = []
    for i, m in enumerate(msgs):
        c = m.get("content")
        text = "\n".join(c) if isinstance(c, list) else str(c)
        name = m.get("name")
        links.append({"from": name, "to": "assistant" if name == "mathproxyagent" else "mathproxyagent",
                      "kind": "order" if i == 0 else "message", "phase": "chat", "start": i, "text": text})
    return links[0]["text"], links, {}


SPLITTERS = {"MetaGPT": split_metagpt, "ChatDev": split_chatdev, "HyperAgent": split_hyperagent, "AG2": split_ag2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("row"); ap.add_argument("trace_dir"); ap.add_argument("scratch_dir")
    a = ap.parse_args()
    d = json.load(open(a.row, encoding="utf-8"))
    r = d["rows"][0]; row = r["row"]; traj = row["trace"]["trajectory"]
    L, lexicon_file, lexicon_name = load_ledger()
    task, links, extra = SPLITTERS[row["mas_name"]](traj)
    scrub = Scrubber(traj)
    out_links = []
    for n, l in enumerate(links):
        text = scrub(l["text"].strip("\n"))
        rec = {"type": "link", "n": n, "from": l["from"], "to": l["to"], "kind": l["kind"], "phase": l["phase"],
               "line": l["start"], "chars": len(text), "markers": marker_counts(L, text), "text": text}
        if "turn" in l:
            rec["turn"] = l["turn"]
        out_links.append(rec)
    meta = {"type": "meta", "row_idx": r["row_idx"], "mas_name": row["mas_name"], "llm_name": row["llm_name"],
            "benchmark_name": row["benchmark_name"], "trace_key": row["trace"]["key"], "trace_index": row["trace"]["index"],
            "trajectory_chars": len(traj), "trajectory_sha256": sha(traj),
            "row_sha256": sha(json.dumps(row, sort_keys=True, ensure_ascii=False)),
            "mast_annotation": row["mast_annotation"],
            "links": len(out_links), "links_by_kind": {k: sum(1 for x in out_links if x["kind"] == k) for k in sorted({x["kind"] for x in out_links})},
            "roles": sorted({x["from"] for x in out_links}),
            "inner_steps": extra.get("inner_steps"),
            "markers_total": {k: sum(x["markers"][k] for x in out_links) for k in out_links[0]["markers"]},
            "scrubbed": scrub.counts,
            "lexicon": {"module": lexicon_name, "sha256": hashlib.sha256(open(lexicon_file, "rb").read()).hexdigest()},
            "source": "huggingface.co/datasets/mcemri/MAST-Data (CC BY 4.0), config default, split train; text scrubbed and split into links by this script"}
    os.makedirs(a.trace_dir, exist_ok=True); os.makedirs(a.scratch_dir, exist_ok=True)
    with open(os.path.join(a.trace_dir, "links.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps(meta, ensure_ascii=False, sort_keys=True) + "\n")
        for rec in out_links:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    open(os.path.join(a.scratch_dir, "task-statement.txt"), "w", encoding="utf-8").write(scrub(task) + "\n")
    open(os.path.join(a.scratch_dir, "trace-scrubbed.txt"), "w", encoding="utf-8").write(scrub(traj))
    if extra.get("reference"):
        open(os.path.join(a.scratch_dir, "reference-not-seen-by-system.txt"), "w", encoding="utf-8").write(scrub(extra["reference"]))
    print(json.dumps({k: meta[k] for k in ("row_idx", "mas_name", "links", "links_by_kind", "inner_steps", "markers_total", "scrubbed")}))


if __name__ == "__main__":
    main()
