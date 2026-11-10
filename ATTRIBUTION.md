# Attribution

## The source

"MAST-Data" by Cemri, Pan, Yang and others ("Why Do Multi-Agent LLM Systems Fail?", NeurIPS 2025), https://huggingface.co/datasets/mcemri/MAST-Data, revision `95118ac951421753cf1deb87ddea3b01e693c41b`, config `default`, split `train`, licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Changed: see below. Nothing here implies that the dataset's authors endorse these files.

MAST's 14 failure-mode labels in each row are the dataset's annotation. Its card says: "Annotations are produced by an LLM judge, not by human labelling." These files compare with them and do not treat them as ground truth.

## The tasks inside the runs

- ProgramDev: task statements as MAST-Data's runs carry them. The task-list file of the MAST code repository states no licence; it is not used and not in this set.
- SWE-bench Lite (runs t05 to t07): GitHub issues of public projects, as MAST-Data's rows carry them. The card at https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite states no licence (read 2026-10-30 and 2026-11-04). Their texts are cut; only their sha256 and length are here.
- OlympiadBench (runs t08 to t10): the card at https://huggingface.co/datasets/Hothan/OlympiadBench states apache-2.0. The problem texts are cut as well.

## The changes

1. Each run is split into links, one hand-off each, by `build/extract.py`, which also scrubs home-path user names, e-mail addresses, user-at-host prompts and token shapes.
2. Each run is read against a task-as-stated proxy and annotated: `as-stated.md`, `reading.md`, `fates.csv`, `flow.svg` (one run, read by a model, no second rater; each file names the model and the date).
3. Every third-party text is cut and replaced by its sha256 and its length: each link's text in `links.jsonl` (130), each task statement in `as-stated.md` (10), and each quote of 4 or more words found in a run's texts (218). `build/cut.py` and each folder's `cuts.jsonl` say where each one was.
4. The word "meaning" of the files of 2026-10-31 is printed "term" (689 places, none inside a quote). `build/cut.py restore` undoes changes 3 and 4 and checks each file against its sha256 of 2026-10-31.

5. The replay entry (`replay/mast-ten/`, 2026-11-07) adds, for the same ten runs, a record of what was agreed drafted by a model from the task text, two models' reads of each hand-off, and the verdicts the library gives on them. Every third-party text in those files is cut the same way (`cuts.jsonl` per run) and comes back with `build/cut.py restore`. The maps show counts and step names, no values. The drafted records and the reads are a model's work, not the source's.

## The rows, as fetched

Each row is one response of the dataset server's rows API. That service takes no revision: it serves the current one. On 2026-10-30, 2026-11-04 (row 30) and 2026-11-06 (all ten) it served trajectories with the sha256 below (the sha256 of `trace.trajectory` as UTF-8).

URL: `https://datasets-server.huggingface.co/rows?dataset=mcemri/MAST-Data&config=default&split=train&offset=<row>&length=1`

| folder | row (offset) | framework | benchmark | trajectory chars | sha256 of the trajectory |
|---|---|---|---|---|---|
| `t01-chatdev-checkers/` | 0 | ChatDev | ProgramDev | 345,536 | `8af11f42b1afe38165b65744585f51809e96bddf48d49e738ab5255ec1033d9d` |
| `t02-metagpt-checkers/` | 30 | MetaGPT | ProgramDev | 8,157 | `1658259d3e20163834204f54497f146f890d59bd290e9e2cb49fb9d7e0cd39d7` |
| `t03-chatdev-sudoku/` | 1 | ChatDev | ProgramDev | 316,737 | `ee9f14a34a1c17aa01d90c77536cf83a37edb4a2267bac366cca29d73b948180` |
| `t04-metagpt-sudoku/` | 31 | MetaGPT | ProgramDev | 8,863 | `108cb8094676ad1dd4cc761fd1cafe45b3165e50eaf7b74078b25b8ca3cd4e90` |
| `t05-hyperagent-xarray-4493/` | 180 | HyperAgent | SWE-Bench-Lite | 60,013 | `6353286d6d398c8c9eeb2420a0746adbef7f42e2e4fbbec918818f5ad3864b76` |
| `t06-hyperagent-matplotlib-25433/` | 181 | HyperAgent | SWE-Bench-Lite | 47,957 | `6f99194cd51e884946abd0fe4a6cf8bf9162ac81b922ee7670fb75a09fa04efa` |
| `t07-hyperagent-matplotlib-18869/` | 182 | HyperAgent | SWE-Bench-Lite | 68,953 | `b5e721bc1b73833aff6dee403ad83288c3518d2b8af408a4f6f9d8ff7e58cea9` |
| `t08-ag2-olympiad-0/` | 571 | AG2 | Olympiad | 4,109 | `9187efc1079cc6eff854371c9132a68d6f4d27d634332270236ba587a34bb488` |
| `t09-ag2-olympiad-1/` | 572 | AG2 | Olympiad | 17,577 | `de146fa6bb2c0c350740b14659ee79309b3340838ed20881db8d5c54a5885da2` |
| `t10-ag2-olympiad-2/` | 573 | AG2 | Olympiad | 5,767 | `5283fe4e150a04c6250c1e7253e0fbcca36e4a63afc5bce393eb8f3170a55fec` |

## This set

The files of this set, apart from the source texts above, are licensed under CC BY 4.0 (`LICENSE`). Credit them as: "As-Agreed, `as-delivered`, the public set of results, copyright BizBuilder, Inc., https://github.com/as-agreed/as-delivered, CC BY 4.0".
