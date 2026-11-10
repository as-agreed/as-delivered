# Results on public traces

Public results on traces of multi-agent runs.

In a multi-agent system, agents give work to agents. At each hand-off, a term of the order can change. Each result in this set shows the step where a term or the status of a claim changed. Each result has its type of change, its location and its tag. It tells no person that they caused the error.

## What is in it

- `replay/mast-ten/`: the first part of the set. It has 10 runs from `MAST-Data`, with the reads of 2 models.
- With `replay/bin/`, you run the check again on these reads, with no model. `replay/mast-ten/README.md` tells what is in it.
- `readings/mast/`: the same 10 runs, read before by 1 model, with 1 folder for each run.
- In each folder of `readings/mast/`: the order and its terms (`as-stated.md`), and each hand-off (`links.jsonl`).
- Also in each folder: the result (`reading.md`, `fates.csv`) and its map (`flow.svg`).
- `readings/mast/counts.md`: 130 hand-offs `[D]`, and 83 terms and 49 claims across the 10 runs `[C]`.
- `build/`: the code that makes the hand-offs, counts each status, cuts the external text and makes the maps.

The tags: `[D]` is a count that a tool made, with no model. `[C]` is "one run, read by a model, no second rater".

## The standard for each result

1. Each external text is cut: the text of each hand-off, each task, and each long part that a result copies.
2. Each cut text is replaced by its `sha256` and its count of `chars`.
3. `readings/mast/REBUILD.md` and `replay/mast-ten/REPLAY.md` give the procedure that gets the public source and makes the full files again.
4. `build/cut.py` puts back each cut text and compares each `sha256` with the full file.
5. The full texts stay on the computer that does the checks.

In this set, 358 texts are cut, and `build/cut.py` puts back all 358 from the public source.

## Licence

The results are under `CC BY 4.0`, in `LICENSE`. The source data is `MAST-Data`, also under `CC BY 4.0`. `ATTRIBUTION.md` gives the source, its rows with their `sha256`, and each change. To refer to this set, use `CITATION.cff`.

## Limits

In `readings/mast/`, each `[C]` result is "one run, read by a model, no second rater". 10 runs give counts, not rates. One model made these results on 2026-10-31. The results in `replay/mast-ten/` come from 2 models, and they do not agree with the first results on each point. Where they do not agree, use `replay/mast-ten/`.

## Where this goes

This set starts with 10 runs of `MAST-Data` that you can run again with no model. Each run that a team sends with consent and a licence goes in by the same standard. Its texts are cut, and its reads are kept with the code that runs the check again. The tool that makes the maps is As-Agreed: https://github.com/as-agreed/as-agreed
