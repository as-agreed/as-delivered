"""Model callers for the trace bench: each is a callable prompt -> text, and every call is logged.

Three modes, chosen in bench.py:
  api       the Claude API through the `anthropic` package, when it is installed and ANTHROPIC_API_KEY is set
  exchange  a folder: a prompt with no answer yet is written to <exchange>/pending/<role>/<sha>.txt and the run stops
            at that call; an answer is read from <exchange>/answers/<sha>.txt (and the answering model's exact id
            from <sha>.model when present). This lets any model (a subagent, a person) answer, and a rerun resumes.
  dry-run   fixtures, no model: the hand-written t03 record and the walkthrough's static probe (block 7), so the
            pipeline is testable without a model. Its output says "dry-run" on every row.
The library ships no model client (SPEC §4); this module lives beside it, in the study, never in the package.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any, Callable, Dict, Optional


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Pending(Exception):
    """The answer to a prompt is not in the exchange folder yet."""


class Caller:
    mode = "base"

    def __init__(self, role: str, model: str):
        self.role, self.model = role, model
        self.version = model  # the exact id that answered, when the mode can tell

    def __call__(self, prompt: str) -> str:
        raise NotImplementedError


class ApiCaller(Caller):
    mode = "api"

    def __init__(self, role: str, model: str, max_tokens: int = 8000):
        super().__init__(role, model)
        import anthropic  # only here: the study runs without it
        self.client = anthropic.Anthropic()
        self.max_tokens = max_tokens

    def __call__(self, prompt: str) -> str:
        msg = self.client.messages.create(model=self.model, max_tokens=self.max_tokens,
                                          messages=[{"role": "user", "content": prompt}])
        self.version = getattr(msg, "model", self.model)
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


class ExchangeCaller(Caller):
    mode = "exchange"

    def __init__(self, role: str, model: str, folder: str):
        super().__init__(role, model)
        self.folder = folder

    def __call__(self, prompt: str) -> str:
        h = sha(prompt)
        ans = os.path.join(self.folder, "answers", h + ".txt")
        if os.path.exists(ans):
            meta = os.path.join(self.folder, "answers", h + ".model")
            self.version = open(meta, encoding="utf-8").read().strip() if os.path.exists(meta) else self.model
            self.answered_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(ans)))
            return open(ans, encoding="utf-8").read()
        pend = os.path.join(self.folder, "pending", self.role)
        os.makedirs(pend, exist_ok=True)
        with open(os.path.join(pend, h + ".txt"), "w", encoding="utf-8") as f:
            f.write(prompt)
        raise Pending(h)


REQUEST = re.compile(r"<request>\s*(\{.*\})\s*</request>\s*$", re.S)


def request_of(prompt: str) -> Dict[str, Any]:
    """The machine-readable block every bench prompt ends with."""
    m = REQUEST.search(prompt)
    return json.loads(m.group(1)) if m else {}


HERE = os.path.dirname(os.path.abspath(__file__))
# block 7 of plans/2026-11-04-see-it-work/WALKTHROUGH.md: the static probe written after the reading (post hoc)
RANGE_PROBE = re.compile(r"<=\s*9|in range\(1,\s*10\)|>\s*9|<\s*1\b|not in range|range\(1,\s*10\)")


class DryRunCaller(Caller):
    """No model. Drafter: the t03 fixture record when the task statement is t03's, else a record with no typed field.
    Reader: the walkthrough's post-hoc regex probe for the fixture's one field at code links, else not addressed."""
    mode = "dry-run"

    def __init__(self, role: str):
        super().__init__(role, "dry-run-fixture")
        with open(os.path.join(HERE, "fixtures", "t03-record.json"), encoding="utf-8") as f:
            self.fixture = json.load(f)

    def __call__(self, prompt: str) -> str:
        from prompts import body_of
        req = request_of(prompt)
        if self.role == "drafter":
            task = body_of(prompt)
            if " ".join(task.split()) == " ".join(self.fixture["task_statement"].split()):
                return json.dumps(self.fixture["draft"])
            first = " ".join(task.split()[:12]) or "do the task"
            return json.dumps({"act": first, "act_quote": first, "fields": [], "untyped": []})
        reads = []
        for f in req.get("fields", []):
            hit = None
            text = body_of(prompt)
            if f.get("key") == "digit_range_checked" and "def " in text:
                m = RANGE_PROBE.search(text)
                line = next(ln for ln in text.splitlines() if "def " in ln).strip()
                hit = {"field": f["field"], "status": "carried", "value": bool(m), "confidence": 1.0,
                       "quote": m.group(0) if m else line}
            reads.append(hit or {"field": f["field"], "status": "not_addressed", "value": None, "confidence": 1.0,
                                 "quote": ""})
        return json.dumps({"reads": reads})


class CallLog:
    """calls.jsonl: one line per call, with mode, role, model, version, date, prompt and raw answer."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def wrap(self, caller: Caller) -> Callable[[str], str]:
        def call(prompt: str) -> str:
            ts = now()
            try:
                answer = caller(prompt)
            except Pending:
                self.write({"ts": ts, "mode": caller.mode, "role": caller.role, "model": caller.model,
                            "prompt_sha256": sha(prompt), "status": "pending"})
                raise
            rec = {"ts": ts, "mode": caller.mode, "role": caller.role, "model": caller.model,
                   "version": caller.version, "prompt_sha256": sha(prompt), "status": "answered",
                   "prompt": prompt, "answer": answer}
            if getattr(caller, "answered_at", None):  # exchange: when the answer file was written
                rec["answered_at"] = caller.answered_at
            self.write(rec)
            return answer
        return call

    def write(self, rec: Dict[str, Any]) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def make_caller(mode: str, role: str, model: str, exchange: Optional[str] = None) -> Caller:
    if mode == "api":
        return ApiCaller(role, model)
    if mode == "exchange":
        if not exchange:
            raise ValueError("--exchange <folder> is needed in exchange mode")
        return ExchangeCaller(role, model, exchange)
    if mode == "dry-run":
        return DryRunCaller(role)
    raise ValueError(f"unknown mode {mode!r}")


def api_available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True
