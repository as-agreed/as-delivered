"""The status-marker lexicon of the claim-ledger instrument, frozen for this reading.

Copied verbatim (lines 44 to 142) from the ledger module of the claim-ledger instrument (tools/claim-ledger/), sha256
acaaa039ae29bb060bbf094d009270b3ee88b3983b32ea9d0de2a3d4c2544a34, on 2026-10-31. The instrument is being changed; this copy keeps the [D] counts of
the MAST reading rebuildable. On the ten runs it gives the same counts as the version of 2026-10-30
(sha256 4c98562093a298cfc8e9fa01425322d1850030f6d5807ce04f60a37973cc0b28). Standard library only.
"""
import hashlib
import re
from typing import Dict, List, Optional

# ---------- lexicon (English part seeded from Zhou et al. 2024 weakeners/strengtheners; Russian added) ----------
WEAKENERS = [
    r"not found", r"could not (?:verify|confirm|find|open)", r"couldn't", r"unverified", r"not (?:confirmed|verified)",
    r"appears?", r"seems?", r"\bmay\b", r"\bmight\b", r"likely", r"unclear", r"no evidence", r"probably", r"possibly",
    r"approximately", r"\babout\b", r"\baround\b", r"estimate[sd]?", r"i think", r"i believe", r"suggests?", r"perhaps",
    r"вероятно", r"возможно", r"похоже", r"кажется", r"предполож\w*", r"не подтвержд\w*", r"не подтвердил\w*",
    r"не удал\w*", r"не наш[её]л\w*", r"не найден\w*", r"не открыл\w*", r"не открыва\w*", r"не провер\w*",
    r"неясно", r"нет данных", r"оценочн\w*", r"по оценке", r"примерно", r"около", r"скорее всего", r"видимо",
    r"не уверен\w*", r"спорн\w*", r"пограничн\w*", r"наверн(?:ое|о)\b",
]
STRENGTHENERS = [
    r"definitely", r"certainly", r"clearly", r"confirmed", r"verified", r"\bproven\b", r"always", r"undoubtedly",
    r"точно", r"подтвержд[её]н\w*", r"проверен\w*", r"однозначно", r"наверняка", r"безусловно", r"несомненно",
]
NOT_FOUND = [r"not found", r"could not find", r"couldn't find", r"no (?:data|record|evidence|mention)", r"did not find",
             r"не найден\w*", r"не наш[её]л\w*", r"нет данных", r"не обнаружен\w*", r"отсутству\w*"]
UNKNOWN = [r"\bunknown\b", r"not known", r"неизвестн\w*", r"не известн\w*"]
NEGATIONS = [r"\bnot\b", r"\bno\b", r"\bnever\b", r"\bне\b", r"\bнет\b", r"\bни\b"]
SOURCE_WORDS = [r"according to", r"source[s]?:?", r"per the", r"from the (?:page|site|report|file|document)",
                r"по данным", r"по справке", r"источник\w*", r"согласно", r"со слов"]
TEMPORAL = [r"\bas of\b", r"\b\d{4}-\d{2}-\d{2}\b", r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b", r"\byesterday\b", r"\btoday\b",
            r"\blast (?:week|month|year)\b", r"\bв \d{4}\b", r"по состоянию на", r"вчера", r"сегодня", r"на \d{1,2}\.\d{1,2}"]

WEAK = re.compile("|".join(WEAKENERS), re.I)
STRONG = re.compile("|".join(STRENGTHENERS), re.I)
NF = re.compile("|".join(NOT_FOUND), re.I)
UNK = re.compile("|".join(UNKNOWN), re.I)
NEG = re.compile("|".join(NEGATIONS), re.I)
SRC = re.compile("|".join(SOURCE_WORDS), re.I)
TEMP = re.compile("|".join(TEMPORAL), re.I)
URL_OR_PATH = re.compile(r"https?://[^\s)\]\"'>]+|(?:[\w.-]+/)+[\w.-]+\.\w{1,5}")
TAG = re.compile(r"\[c:([0-9a-f]{12})\]")
WORD = re.compile(r"[\w-]{4,}", re.U)
STOP = {"which", "about", "there", "these", "those", "would", "could", "should", "that", "this", "with", "from", "have",
        "will", "your", "their", "them", "they", "what", "when", "where", "then", "than", "into", "onto", "each", "every",
        "been", "being", "were", "also", "only", "just", "more", "most", "some", "such", "very", "over", "under",
        "которые", "который", "этого", "поэтому", "только", "нужно", "через", "после", "между", "также", "файле",
        "строк", "строки", "если", "есть", "нет", "когда", "чтобы", "этот", "эта", "это", "того", "тоже", "уже"}
PATHISH = re.compile(r"\S*[/\\]\S*|\b[0-9a-f]{8,}\b|\S+\.(?:md|csv|jsonl?|py|mjs|ts|png|jpg)\b", re.I)


# ---------- text handling ----------
def sentences(text: str) -> List[str]:
    # markdown headings, table rules and fenced-code markers are not claims
    text = "\n".join(ln for ln in text.splitlines()
                     if not ln.lstrip().startswith("#") and not re.match(r"^\s*\|?\s*-{3,}", ln) and not ln.strip().startswith("```"))
    text = TAG.sub(lambda m: f" {m.group(0)} ", text)
    parts = re.split(r"(?<=[.!?;:])\s+|\n+", text)
    out = []
    for p in parts:
        p = p.strip(" -*•\t#>|")
        p = re.sub(r"\s+", " ", p)
        if len(p) > 15:
            out.append(p)
    return out


def content_words(s: str) -> set:
    s2 = PATHISH.sub(" ", TAG.sub(" ", s))
    ws = {w.lower() for w in WORD.findall(s2)}
    marker_words = {m.group(0).lower() for m in WEAK.finditer(s2)} | {m.group(0).lower() for m in STRONG.finditer(s2)}
    return {w for w in ws if w not in STOP and w not in marker_words and not w.isdigit()}


def normalise(s: str) -> str:
    s = TAG.sub("", s).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def claim_id(text: str) -> str:
    return hashlib.sha256(normalise(text).encode("utf-8")).hexdigest()[:12]


def markers(s: str) -> Dict[str, Optional[str]]:
    w = WEAK.search(s)
    st = STRONG.search(s)
    epistemic = w.group(0) if w else (st.group(0) if st else None)
    if NF.search(s):
        existential = "not_found"
    elif UNK.search(s):
        existential = "unknown_stated"
    else:
        existential = "value_present"
    src = URL_OR_PATH.search(s) or SRC.search(s)
    provenance = src.group(0) if src else "none stated"
    t = TEMP.search(s)
    temporal = t.group(0) if t else None
    return {"epistemic": epistemic, "existential": existential, "provenance": provenance, "temporal": temporal}


def origin_class(m: Dict[str, Optional[str]]) -> str:
    if m.get("epistemic") and WEAK.search(m["epistemic"] or ""):
        return "hedged"
    if m.get("existential") in ("not_found", "unknown_stated"):
        return "not_found"
    return "flat"


