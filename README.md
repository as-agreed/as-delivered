# Ten runs, read step by step

What you agreed is what arrives. This set shows ten runs where it did not.

The runs are public, from MAST-Data. In each, a team of agents got a task with a few hard terms. An 8 by 8 board. Digits 1 to 9. A version bound. Your agents report done. Today no part of your system checks that report against what was agreed. As-Agreed checks each step of a pipeline against what was agreed. It stops the last step if a must term changed. For each run you see the step where a term changed, and what the last step reported.

## What you can do with it

- Run the check again on your own machine, with no model and no key. It takes about two minutes. It gives these same files, byte for byte. The commands are in `replay/mast-ten/REPLAY.md`.
- Read one run. Open `replay/mast-ten/t02-metagpt-checkers/card.html`. It shows the terms of the task and the step where the capture rule went missing. It shows what a hold at that step would have stopped.
- Compare with the authors' labels. MAST tags each run with 14 failure modes for the whole run. Our reading is per term and per step. The two differ on some runs, and `replay/mast-ten/hand-check.md` says where and why.

## What is here, and what is not

Here, for each run: the record of what was agreed, drafted by a model from the task text. The record is a file on your disk, `commitments.json`. Two models' reads of each hand-off. The library's verdict at each step. A map, a card, and the scripts that made them.

Not here: the runs' own texts. Every task statement, every hand-off and every quote is cut out. In its place sit its sha256 and its length. The replay fetches the rows from their public source and puts the texts back on your machine. 358 texts cut, 358 put back, each checked by hash. A team that sends us a run gets the same treatment. The record and the reads go in. Their texts stay with them.

Later, the As-Agreed service keeps the same record for all your runs and teams, over time. This set is the open form of that: one record per run, in public.

## Limits

Ten runs give counts, not rates. The record of what was agreed is a model's draft from the task text. It is not an agreement the team wrote down. The reads are two models' reads. Where they disagree, the hand check gives a third read over the full text of the run. `readings/mast/` is an earlier pass over the same runs by one model, kept as it was.

## Licence and credit

Our files are CC BY 4.0, copyright BizBuilder, Inc. The source runs are MAST-Data, CC BY 4.0. `ATTRIBUTION.md` lists the rows, their hashes and every change we made. `CITATION.cff` says how to cite this set. The tool is As-Agreed: https://github.com/as-agreed/as-agreed
