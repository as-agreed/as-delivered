# Run it again: 10 MAST runs

You can run the check again on 10 public runs.

This folder is the first part of the set. It holds 10 runs of `MAST-Data`, the reads of 2 models, and what the check made from them. With the code in `../bin/`, you run the same check again on the same reads, with no model. The check then gives the same result for each field, the same maps and the same `card.html` files.

## What is in it

1 folder for each run. In each folder:

- `commitments.json`: the record of what was agreed. A model made it only from the text of the task `[C]`.
- `links.jsonl`: each hand-off of the run, with its text cut.
- `reads.jsonl`: what the first model read at each hand-off, for each field `[C]`.
- `second-reads.jsonl`: what the other model read `[C]`. A field goes to the other model when the number of the first model is under 0.8. It also goes there when the first model gives a change.
- `ledger.jsonl`: the result of each field at each step, as `as_agreed` writes it.
- `flow.svg`: the map of the run, with its counts and step names and no value. `card.html` gives the values and the text that the models read.
- `card.html`: for each field with a change, its type of result and the 3 lines for a buyer.
- `cuts.jsonl`: for each cut text, its `sha256`, its count of `chars`, and its location in the public source.

Also in this folder:

- `hand-check.md`: for each "SPLIT", a model read the text of the run and gives its result `[C]`.
- `seller-lines.md`: for 1 field of each run, the "loss", what a hold at that step can do, and the "opportunity".
- `REPLAY.md`: the procedure that runs the check again, and its output on 2 versions of Python.

`../bin/` holds the code. `bench.py`, `models.py`, `prompts.py`, `cards.py` and `convert_mast.py` are the check as we run it. Only the text of 2 lines in `bench.py` is changed, and `REPLAY.md` tells which. `replay.py` and `cut_replay.py` are new. `replay.py` gives each kept read to the check. `cut_replay.py` cuts the texts and puts them back.

## The types of result

The 2 models are different models. Each model gives a number from 0 to 1 that tells how sure it is.

- "FINDING": the 2 models give the same change to the field, and each number is 0.8 or more.
- "PROPOSAL": the 2 models give the same change, and 1 number or 2 numbers are under 0.8.
- "SPLIT": the 2 models give different results, and 1 of them gives a change.

When the 2 models agree, this does not show that the result is correct.

## The standard for each result

1. Each external text is cut: the text of each hand-off, and each part of it that a file copies.
2. Each cut text is replaced by its `sha256` and its count of `chars`.
3. `REPLAY.md` gets the public source, puts back each cut text, and compares each `sha256` with the full file.
4. The full texts stay on the computer that runs the check.

## Limits

Each record of what was agreed is a "proxy" that a model made `[C]`. No person accepted it. Each read is the read of a model `[C]`, and `hand-check.md` is also the work of a model. This set gives no rate and no total.

## Licence

The files here are under `CC BY 4.0`, in `../../LICENSE`. The source data is `MAST-Data`, also under `CC BY 4.0`. It is at https://huggingface.co/datasets/mcemri/MAST-Data. `../../ATTRIBUTION.md` gives the source, its rows with their `sha256`, and each change. In this folder, `convert_mast.py` makes the hand-offs of each run, and 2 models read them. The check gives a result for each field. Then each external text is cut.
