# Check it yourself: 10 MAST runs

Don't take our word for it. Run the check yourself.

What you agreed is what arrives. That is what a team of agents owes you. Your agents report done. Today no part of your system checks that report against what was agreed. As-Agreed checks each step of a pipeline against what was agreed. It stops the last step if a must term changed.

Here you can watch that work on 10 public runs from `MAST-Data`. This folder holds the reads of 2 models and all that the check made from them. With the code in `../bin/`, you run the same check on the same reads. No model is called. The check gives the same result for each field, the same maps and the same `card.html` files.

Start with `REPLAY.md`. It takes about two minutes.

## What each run holds

One folder for each run. The record is a file on your disk. So is the rest:

- `commitments.json`: the record of what was agreed. A model drafted it from the text of the task alone `[C]`.
- `links.jsonl`: each hand-off of the run, with its text cut out.
- `reads.jsonl`: what the first model read at each hand-off, field by field `[C]`.
- `second-reads.jsonl`: what the other model read `[C]`. A field goes to the other model when the first model's number is under 0.8. It also goes there when the first model reports a change.
- `ledger.jsonl`: the result for each field at each step, as `as_agreed` writes it.
- `flow.svg`: the map of the run. It shows counts and step names, and no value. The values, and the text the models read, are in `card.html`.
- `card.html`: each field with a change, its type of result, and the 3 lines for a buyer.
- `cuts.jsonl`: for each cut text, its `sha256`, its length in `chars`, and its place in the public source.

Beside the run folders:

- `hand-check.md`: for each "SPLIT", a model read the text of the run and gives its result `[C]`.
- `seller-lines.md`: for 1 field of each run, the "loss", what a hold at that step can do, and the "opportunity".
- `REPLAY.md`: the commands that run the check again, and their output on 2 versions of Python.

## The code

`../bin/` holds the code. `bench.py`, `models.py`, `prompts.py`, `cards.py` and `convert_mast.py` are the check as we run it. In `bench.py`, the text of 2 lines changed, and nothing else. `REPLAY.md` names them. Two files are new. `replay.py` hands each stored read to the check. `cut_replay.py` cuts the texts out and puts them back.

## Two readers, three results

One model's read is an opinion. So a second, different model reads the same hand-off. Each model gives a number from 0 to 1 for how sure it is.

- "FINDING": the 2 models report the same change, and each number is 0.8 or more.
- "PROPOSAL": the 2 models report the same change, and 1 number or both are under 0.8.
- "SPLIT": the 2 models give different results, and 1 of them reports a change.

Two models can agree and both be wrong. Agreement does not show that a result is correct.

## Why the texts are cut out

These runs are other people's words, and some of the tasks inside them come from a third source. So the set carries their hashes, and your machine puts the words back:

1. Each external text is cut: the text of each hand-off, and each part of it that a file copies.
2. In its place sit its `sha256` and its length in `chars`.
3. `REPLAY.md` fetches the public source, puts each cut text back, and compares each `sha256` with the full file.
4. The full texts stay on the computer that runs the check.

## Limits

Each record of what was agreed is a "proxy" that a model drafted `[C]`. No person accepted it. Each read is a model's read `[C]`, and `hand-check.md` is a model's work too. This set gives no rate and no total.

Here you see one record for each run. Later, the As-Agreed service keeps the same record for all your runs and teams, over time.

## Licence

Our files are under `CC BY 4.0`, in `../../LICENSE`. The source data is `MAST-Data`, also under `CC BY 4.0`, at https://huggingface.co/datasets/mcemri/MAST-Data

`../../ATTRIBUTION.md` gives the source, its rows with their `sha256`, and each change. The order of work in this folder: `convert_mast.py` makes the hand-offs of each run, and 2 models read them. The check gives a result for each field. Then each external text is cut.
