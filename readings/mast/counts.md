# Ten MAST-Data traces: the counts (task-as-stated proxy)

[C] read by Opus 5.5 (claude-opus-5-5) on the night of 2026-10-30 to 31, one model instance per two runs, no second rater; [D] counted by `build/extract.py` on 2026-10-31; this table built by `build/tables.py`. Data: MAST-Data, CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), changes marked in `README.md`.

Ten of MAST-Data's 1,642 traces, chosen by the rule in `README.md`; counts only, every count with its denominator; no rate is computed, because ten chosen traces estimate nothing about the 1,642. Tags: [D] counted by the scripts in `build/` from the scrubbed links, no model; [C] one run, read by a model, no second rater, reconciled against the task-as-stated proxy written before the run was read; MAST's label is the dataset's own annotation, made by an LLM judge (dataset card: "Annotations are produced by an LLM judge, not by human labelling."). Built by `build/tables.py` from each trace's `links.jsonl` and `fates.csv`.

## 1. Links and status markers, by script, independent of the task-as-stated proxy [D]

| trace | shape | framework (model) | links | roles | sentences | hedged | not found | strengthened | sourced | dated |
|---|---|---|---|---|---|---|---|---|---|---|
| t01-chatdev-checkers | line | ChatDev (GPT-4o) | 26 | 7 | 2025 | 26 of 2025 | 0 of 2025 | 0 of 2025 | 62 of 2025 | 0 of 2025 |
| t02-metagpt-checkers | line | MetaGPT (GPT-4o) | 6 | 4 | 105 | 1 of 105 | 0 of 105 | 0 of 105 | 0 of 105 | 0 of 105 |
| t03-chatdev-sudoku | line | ChatDev (GPT-4o) | 26 | 7 | 1772 | 27 of 1772 | 0 of 1772 | 2 of 1772 | 63 of 1772 | 0 of 1772 |
| t04-metagpt-sudoku | line | MetaGPT (GPT-4o) | 6 | 4 | 155 | 1 of 155 | 0 of 155 | 0 of 155 | 1 of 155 | 0 of 155 |
| t05-hyperagent-xarray-4493 | star | HyperAgent (Claude) | 14 | 5 | 337 | 12 of 337 | 0 of 337 | 0 of 337 | 15 of 337 | 0 of 337 |
| t06-hyperagent-matplotlib-25433 | star | HyperAgent (Claude) | 14 | 5 | 218 | 14 of 218 | 1 of 218 | 0 of 218 | 12 of 218 | 0 of 218 |
| t07-hyperagent-matplotlib-18869 | star | HyperAgent (Claude) | 20 | 5 | 387 | 15 of 387 | 0 of 387 | 2 of 387 | 8 of 387 | 0 of 387 |
| t08-ag2-olympiad-0 | two-agent chat | AG2 (GPT-4o) | 4 | 2 | 43 | 2 of 43 | 0 of 43 | 1 of 43 | 0 of 43 | 0 of 43 |
| t09-ag2-olympiad-1 | two-agent chat | AG2 (GPT-4o) | 10 | 2 | 218 | 11 of 218 | 0 of 218 | 1 of 218 | 0 of 218 | 0 of 218 |
| t10-ag2-olympiad-2 | two-agent chat | AG2 (GPT-4o) | 4 | 2 | 59 | 1 of 59 | 0 of 59 | 1 of 59 | 0 of 59 | 0 of 59 |
| **line: 4 traces** | | | 64 | | 4057 | 55 of 4057 | 0 of 4057 | 2 of 4057 | 126 of 4057 | 0 of 4057 |
| **star: 3 traces** | | | 48 | | 942 | 41 of 942 | 1 of 942 | 2 of 942 | 35 of 942 | 0 of 942 |
| **two-agent chat: 3 traces** | | | 18 | | 320 | 14 of 320 | 0 of 320 | 3 of 320 | 0 of 320 | 0 of 320 |
| **all: 10 traces** | | | 130 | | 5319 | 110 of 5319 | 1 of 5319 | 7 of 5319 | 161 of 5319 | 0 of 5319 |

A sentence is counted once per marker class it carries (the claim-ledger lexicon; `README.md`, "The deterministic tier"). HyperAgent's inner steps inside a child agent are not links: t05-hyperagent-xarray-4493 23, t06-hyperagent-matplotlib-25433 23, t07-hyperagent-matplotlib-18869 34 [D].

## 2. The order's terms at the commit (task-as-stated proxy) [C]

| trace | commit | terms | intact | narrowed | substituted | absent | restored |
|---|---|---|---|---|---|---|---|
| t01-chatdev-checkers | L19 | 8 | 4 of 8 | 1 of 8 | 0 of 8 | 0 of 8 | 3 of 8 |
| t02-metagpt-checkers | L01 | 8 | 7 of 8 | 1 of 8 | 0 of 8 | 0 of 8 | 0 of 8 |
| t03-chatdev-sudoku | L19 | 7 | 6 of 7 | 1 of 7 | 0 of 7 | 0 of 7 | 0 of 7 |
| t04-metagpt-sudoku | L01 | 7 | 2 of 7 | 5 of 7 | 0 of 7 | 0 of 7 | 0 of 7 |
| t05-hyperagent-xarray-4493 | L10 | 7 | 1 of 7 | 3 of 7 | 1 of 7 | 2 of 7 | 0 of 7 |
| t06-hyperagent-matplotlib-25433 | L08 | 7 | 4 of 7 | 1 of 7 | 2 of 7 | 0 of 7 | 0 of 7 |
| t07-hyperagent-matplotlib-18869 | L18 | 6 | 3 of 6 | 0 of 6 | 0 of 6 | 0 of 6 | 3 of 6 |
| t08-ag2-olympiad-0 | L03 | 10 | 8 of 10 | 0 of 10 | 1 of 10 | 0 of 10 | 1 of 10 |
| t09-ag2-olympiad-1 | L09 | 11 | 9 of 11 | 1 of 11 | 1 of 11 | 0 of 11 | 0 of 11 |
| t10-ag2-olympiad-2 | L03 | 12 | 9 of 12 | 1 of 12 | 0 of 12 | 1 of 12 | 1 of 12 |
| **line: 4 traces** |  | 30 | 19 of 30 | 8 of 30 | 0 of 30 | 0 of 30 | 3 of 30 |
| **star: 3 traces** |  | 20 | 8 of 20 | 4 of 20 | 3 of 20 | 2 of 20 | 3 of 20 |
| **two-agent chat: 3 traces** |  | 33 | 26 of 33 | 2 of 33 | 2 of 33 | 1 of 33 | 2 of 33 |
| **all: 10 traces** |  | 83 | 53 of 83 | 14 of 83 | 5 of 83 | 3 of 83 | 8 of 83 |

Three of the 22 terms lost at the commit depend on a choice between two readings that the proxy itself names (t01 M5 and t02 M5, "standard capture"; t05 M7, the constructor question); each trace file says which reading it counted (section 6). Read the other way, 19 of 83. The 83 count terms per run: two statements ran through two pipelines each, so the eight statements hold 68 distinct terms.


## 3. Claims followed, their status at the run's last link (task-as-stated proxy) [C]

| trace | claims | kept | softened | hardened | dropped | inverted | still as made | made after the commit | status changed after the commit | correct: yes | no | unknown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| t01-chatdev-checkers | 4 | 4 of 4 | 0 of 4 | 0 of 4 | 0 of 4 | 0 of 4 | 0 of 4 | 0 of 4 | 0 of 4 | 2 of 4 | 2 of 4 | 0 of 4 |
| t02-metagpt-checkers | 4 | 2 of 4 | 0 of 4 | 2 of 4 | 0 of 4 | 0 of 4 | 0 of 4 | 4 of 4 | 2 of 4 | 2 of 4 | 2 of 4 | 0 of 4 |
| t03-chatdev-sudoku | 6 | 5 of 6 | 0 of 6 | 1 of 6 | 0 of 6 | 0 of 6 | 0 of 6 | 0 of 6 | 0 of 6 | 2 of 6 | 3 of 6 | 1 of 6 |
| t04-metagpt-sudoku | 3 | 2 of 3 | 0 of 3 | 0 of 3 | 1 of 3 | 0 of 3 | 0 of 3 | 2 of 3 | 1 of 3 | 1 of 3 | 2 of 3 | 0 of 3 |
| t05-hyperagent-xarray-4493 | 4 | 1 of 4 | 0 of 4 | 1 of 4 | 1 of 4 | 1 of 4 | 0 of 4 | 0 of 4 | 3 of 4 | 1 of 4 | 3 of 4 | 0 of 4 |
| t06-hyperagent-matplotlib-25433 | 7 | 1 of 7 | 0 of 7 | 4 of 7 | 2 of 7 | 0 of 7 | 0 of 7 | 2 of 7 | 4 of 7 | 3 of 7 | 4 of 7 | 0 of 7 |
| t07-hyperagent-matplotlib-18869 | 7 | 3 of 7 | 2 of 7 | 1 of 7 | 1 of 7 | 0 of 7 | 0 of 7 | 0 of 7 | 1 of 7 | 2 of 7 | 5 of 7 | 0 of 7 |
| t08-ag2-olympiad-0 | 3 | 3 of 3 | 0 of 3 | 0 of 3 | 0 of 3 | 0 of 3 | 0 of 3 | 0 of 3 | 0 of 3 | 1 of 3 | 1 of 3 | 1 of 3 |
| t09-ag2-olympiad-1 | 7 | 3 of 7 | 0 of 7 | 1 of 7 | 0 of 7 | 0 of 7 | 3 of 7 | 0 of 7 | 0 of 7 | 2 of 7 | 5 of 7 | 0 of 7 |
| t10-ag2-olympiad-2 | 4 | 1 of 4 | 0 of 4 | 2 of 4 | 0 of 4 | 0 of 4 | 1 of 4 | 0 of 4 | 0 of 4 | 1 of 4 | 3 of 4 | 0 of 4 |
| **line: 4 traces** | 17 | 13 of 17 | 0 of 17 | 3 of 17 | 1 of 17 | 0 of 17 | 0 of 17 | 6 of 17 | 3 of 17 | 7 of 17 | 9 of 17 | 1 of 17 |
| **star: 3 traces** | 18 | 5 of 18 | 2 of 18 | 6 of 18 | 4 of 18 | 1 of 18 | 0 of 18 | 2 of 18 | 8 of 18 | 6 of 18 | 12 of 18 | 0 of 18 |
| **two-agent chat: 3 traces** | 14 | 7 of 14 | 0 of 14 | 3 of 14 | 0 of 14 | 0 of 14 | 4 of 14 | 0 of 14 | 0 of 14 | 4 of 14 | 9 of 14 | 1 of 14 |
| **all: 10 traces** | 49 | 25 of 49 | 2 of 49 | 12 of 49 | 5 of 49 | 1 of 49 | 4 of 49 | 8 of 49 | 11 of 49 | 17 of 49 | 30 of 49 | 2 of 49 |

Claims are counted at the last link of the run, where the run's own last word sits; each trace file's section 3 counts them at the commit. The two differ where a claim is made after the commit (column 9) or its status changes after it (column 10: a softening, hardening, dropping or inversion at a link after the commit). "Still as made": a claim in the state it was born in, either born at the last link or never carried on to a link that relies on it. "Correct" is judged by the run's own evidence (execution output, the problem's data; for the GitHub issues also the fix the project merged, which the system never saw).


## 4. Where the first loss of each unit sat, and MAST's label (task-as-stated proxy) [C]

| trace | units (terms + claims) | units with a loss | design | source | seam | sink | MAST codes set, of 14 per trace (their judge) | of them seen here | loss events here under no set code | codes left at 0 that this reading would set | MAST label and this reading |
|---|---|---|---|---|---|---|---|---|---|---|---|
| t01-chatdev-checkers | 12 | 4 of 12 | 0 of 4 | 1 of 4 | 3 of 4 | 0 of 4 | 0 of 14 | 0 of 0 | 4 of 4 | 3 of 14 | disagree |
| t02-metagpt-checkers | 12 | 3 of 12 | 2 of 3 | 1 of 3 | 0 of 3 | 0 of 3 | 1 of 14 | 1 of 1 | 1 of 3 | 1 of 13 | partly |
| t03-chatdev-sudoku | 13 | 2 of 13 | 1 of 2 | 1 of 2 | 0 of 2 | 0 of 2 | 0 of 14 | 0 of 0 | 2 of 2 | 2 of 14 | disagree |
| t04-metagpt-sudoku | 10 | 6 of 10 | 0 of 6 | 5 of 6 | 0 of 6 | 1 of 6 | 4 of 14 | 3 of 4 | 2 of 6 | 1 of 10 | partly |
| t05-hyperagent-xarray-4493 | 11 | 9 of 11 | 0 of 9 | 5 of 9 | 2 of 9 | 2 of 9 | 3 of 14 | 3 of 3 | 8 of 10 | 4 of 11 | partly |
| t06-hyperagent-matplotlib-25433 | 14 | 9 of 14 | 0 of 9 | 5 of 9 | 3 of 9 | 1 of 9 | 2 of 14 | 2 of 2 | 5 of 9 | 4 of 12 | partly |
| t07-hyperagent-matplotlib-18869 | 13 | 7 of 13 | 0 of 7 | 4 of 7 | 1 of 7 | 2 of 7 | 12 of 14 | 10 of 12 | 0 of 12 | 1 of 2 | partly |
| t08-ag2-olympiad-0 | 13 | 2 of 13 | 0 of 2 | 2 of 2 | 0 of 2 | 0 of 2 | 0 of 14 | 0 of 0 | 2 of 2 | 2 of 14 | disagree |
| t09-ag2-olympiad-1 | 18 | 3 of 18 | 0 of 3 | 2 of 3 | 0 of 3 | 1 of 3 | 4 of 14 | 3 of 4 | 0 of 4 | 2 of 10 | partly |
| t10-ag2-olympiad-2 | 16 | 5 of 16 | 0 of 5 | 4 of 5 | 1 of 5 | 0 of 5 | 4 of 14 | 4 of 4 | 1 of 6 | 1 of 10 | partly |
| **line: 4 traces** | 47 | 15 of 47 | 3 of 15 | 8 of 15 | 3 of 15 | 1 of 15 | 5 of 56 | 4 of 5 | 9 of 15 | 7 of 51 | agree 0, partly 2, disagree 2 |
| **star: 3 traces** | 38 | 25 of 38 | 0 of 25 | 14 of 25 | 6 of 25 | 5 of 25 | 17 of 42 | 15 of 17 | 13 of 31 | 9 of 25 | agree 0, partly 3, disagree 0 |
| **two-agent chat: 3 traces** | 47 | 10 of 47 | 0 of 10 | 8 of 10 | 1 of 10 | 1 of 10 | 8 of 42 | 7 of 8 | 3 of 12 | 5 of 34 | agree 0, partly 2, disagree 1 |
| **all: 10 traces** | 132 | 50 of 132 | 3 of 50 | 30 of 50 | 10 of 50 | 7 of 50 | 30 of 140 | 26 of 30 | 25 of 58 | 21 of 110 | agree 0, partly 7, disagree 3 |

A unit's first loss is the first link where a term left `intact` or a claim's status changed; its site is one of design, source, seam, sink (`README.md`, "Method"). Later losses of the same unit are described in its trace file, not counted here. "MAST label and this reading" is agree when every code MAST set is seen here and no loss found here falls outside them; disagree when none of them is seen, or MAST set none and a loss is found; partly otherwise.


## 5. Every loss event, by site, as each trace file lists it (task-as-stated proxy) [C]

| trace | loss events | at links | term losses: design | source | seam | sink | claim changes: design | source | seam | sink |
|---|---|---|---|---|---|---|---|---|---|---|
| t01-chatdev-checkers | 4 | 2 of 26 | 0 of 4 | 1 of 4 | 3 of 4 | 0 of 4 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 |
| t02-metagpt-checkers | 3 | 2 of 6 | 0 of 1 | 1 of 1 | 0 of 1 | 0 of 1 | 2 of 2 | 0 of 2 | 0 of 2 | 0 of 2 |
| t03-chatdev-sudoku | 2 | 2 of 26 | 0 of 1 | 1 of 1 | 0 of 1 | 0 of 1 | 1 of 1 | 0 of 1 | 0 of 1 | 0 of 1 |
| t04-metagpt-sudoku | 6 | 2 of 6 | 0 of 5 | 5 of 5 | 0 of 5 | 0 of 5 | 0 of 1 | 0 of 1 | 0 of 1 | 1 of 1 |
| t05-hyperagent-xarray-4493 | 10 | 5 of 14 | 0 of 7 | 6 of 7 | 1 of 7 | 0 of 7 | 0 of 3 | 0 of 3 | 1 of 3 | 2 of 3 |
| t06-hyperagent-matplotlib-25433 | 9 | 6 of 14 | 0 of 3 | 2 of 3 | 1 of 3 | 0 of 3 | 0 of 6 | 3 of 6 | 2 of 6 | 1 of 6 |
| t07-hyperagent-matplotlib-18869 | 12 | 5 of 20 | 0 of 6 | 6 of 6 | 0 of 6 | 0 of 6 | 0 of 6 | 3 of 6 | 1 of 6 | 2 of 6 |
| t08-ag2-olympiad-0 | 2 | 1 of 4 | 0 of 2 | 2 of 2 | 0 of 2 | 0 of 2 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 |
| t09-ag2-olympiad-1 | 4 | 2 of 10 | 0 of 3 | 3 of 3 | 0 of 3 | 0 of 3 | 0 of 1 | 0 of 1 | 0 of 1 | 1 of 1 |
| t10-ag2-olympiad-2 | 6 | 3 of 4 | 0 of 3 | 3 of 3 | 0 of 3 | 0 of 3 | 0 of 3 | 2 of 3 | 1 of 3 | 0 of 3 |
| **line: 4 traces** | 15 | 8 of 64 | 0 of 11 | 8 of 11 | 3 of 11 | 0 of 11 | 3 of 4 | 0 of 4 | 0 of 4 | 1 of 4 |
| **star: 3 traces** | 31 | 16 of 48 | 0 of 16 | 14 of 16 | 2 of 16 | 0 of 16 | 0 of 15 | 6 of 15 | 4 of 15 | 5 of 15 |
| **two-agent chat: 3 traces** | 12 | 6 of 18 | 0 of 8 | 8 of 8 | 0 of 8 | 0 of 8 | 0 of 4 | 2 of 4 | 1 of 4 | 1 of 4 |
| **all: 10 traces** | 58 | 30 of 130 | 0 of 35 | 30 of 35 | 5 of 35 | 0 of 35 | 3 of 23 | 8 of 23 | 5 of 23 | 7 of 23 |

A unit can lose more than once (narrowed, then absent; dropped, then hardened); section 4 counts each unit's first loss, this section every loss, each with the site its trace file gives (section 4 of each `reading.md`). One event at one link is counted once for each term or claim it touches, so a single decision can count several times (t04 L01: 5 terms; t05 L01: 4); "at links" counts the distinct links that carry a loss. At L01, the first link after the order: line 6 of 15, star 5 of 31, two-agent chat 7 of 12 loss events (in the chat runs L01 is the solver's first answer). Three of the ten seam events are one file-writing step of the framework that stored a shell command as the program's main file (t01 L08); the reader filed them as seam and noted that design is arguable.


## 6. Claims: correct by the run's own evidence, against what happened to their status (all ten, pooled; task-as-stated proxy) [C]

| correct by the run's own evidence | claims | status unchanged at the last link | hardened | softened | dropped | inverted |
|---|---|---|---|---|---|---|
| no | 30 of 49 | 18 of 30 | 9 of 30 | 2 of 30 | 0 of 30 | 1 of 30 |
| yes | 17 of 49 | 10 of 17 | 2 of 17 | 0 of 17 | 5 of 17 | 0 of 17 |
| unknown | 2 of 49 | 1 of 2 | 1 of 2 | 0 of 2 | 0 of 2 | 0 of 2 |

| marker at birth | claims | correct: yes | no | unknown |
|---|---|---|---|---|
| flat | 37 of 49 | 16 of 37 | 20 of 37 | 1 of 37 |
| hedged | 8 of 49 | 1 of 8 | 6 of 8 | 1 of 8 |
| strengthened | 4 of 49 | 0 of 4 | 4 of 4 | 0 of 4 |

Claims dropped at some link, whatever their last state: 7 of 49; of them correct by the run's own evidence: 5 of 7.

The claims are the ones each reader chose to follow: at most eight per run, those a later step relied on or that reached the commit or a decision. These counts describe those 49 claims, not claims in general. "Status unchanged" is kept, or still as made, at the last link.

