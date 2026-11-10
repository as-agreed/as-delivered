# The seller's lines for the ten MAST runs

A seller's reading of each run (D-54): for one unit of each run (two for t01), the loss in the task's own terms, what a hold at that link would have done, and the opportunity. It is a reading of one run by a model, not a measured figure, and no rate is claimed. The status of each unit is its D-44 status in the replay: a finding needs two readers of different models at 0.8 or above with the same loss; this replay has none, so each entry names a proposal (both readers read the loss, one or both below 0.8) or a split that the hand check resolved to a loss. The lines of t02 repeat those of 2026-11-06, one word changed; the others were written on 2026-11-07 for this bundle. `cards.py` shows each entry on the card of the run, link and field it names.

## Chunk 1 · the ten MAST runs, replayed from the stored reads

- **Business value** (D-54; a seller's reading of each run, no measured figure; no rate is claimed):
  - `t01-chatdev-checkers` L08 `prompt_moves_in_notation`: the move prompt lost with the game loop (a proposal: both readers at 0.70 and 0.75)
    - loss: The buyer asked for a checkers game that asks each player for a move in notation. The code the programmer hands to review at L08 has the board and its moves, but its main file holds one command and no game loop, so the program never asks anyone for a move.
    - hold: A hold at L08 would have sent the code back before the review rounds began, with the missing field named: the move prompt.
    - opportunity: The team can show at which hand-off the playable game was lost: the code went to review with board logic and no way to play it.
  - `t01-chatdev-checkers` L19 `standard_capture_rules`: the capture rule never closed by the review rounds (a split the hand check resolved to a loss)
    - loss: The buyer asked for the standard capture rules. After several review rounds the code at L19 allows a second jump but never forces a capture, so a player may skip a capture that the rules make compulsory.
    - hold: A hold at L19 would have kept the revised code from passing as done until the forced capture was in it.
    - opportunity: The team sees that the review rounds circled the capture rule and none of them closed it, and can stop paying for rounds that do not move the field.
  - `t02-metagpt-checkers` L01 `standard_capture_rules`: the capture rules lost at the first hand-off (a proposal, not a finding: two readers at 0.80 and 0.60)
    - loss: The buyer asked for a checkers game with the standard capture rules. The first agent wrote one jump that a player may skip. Every later agent tested or reviewed that code, and none rewrote it. The buyer would have paid for a game that does not play by the rules.
    - hold: A hold at that first hand-off would have stopped the chain. No agent would have tested or reviewed the broken code.
    - opportunity: The team can now prove where the rule was lost. It was the first hand-off, the coder's own code, not a later test or review.
  - `t03-chatdev-sudoku` L07 `digit_max`: the digit bound dropped from the first code (a proposal: both readers at 0.65 and 0.75)
    - loss: The buyer asked for a Sudoku whose cells hold digits from 1 to 9. The first code, at L07, asks the player for a number from 1 to 9 and then checks only that it does not clash in its row, column or box; no line keeps the number inside 1 to 9. Both readers read the bound dropped there and at the later code links, below 0.8.
    - hold: A hold at L07 would have named the missing bound before the code went to review, so one input check would have been added once instead of missed in every round.
    - opportunity: The team can show that the bound was lost in the first code and never came back, whatever the review rounds changed.
  - `t04-metagpt-sudoku` L01 `check_for_mistakes`: a mistake check that does not check (a split the hand check resolved to a loss)
    - loss: The buyer asked for a Sudoku that catches the player's wrong entries and confirms a finished puzzle. In the first code, at L01, the hand check reads the row and column test as not working as a test, and the completion check calls it, so a wrong entry is not caught and a finished grid is not confirmed on sound grounds.
    - hold: A hold at L01 would have sent the code back to its writer before the tester and the reviewer spent their turns on it.
    - opportunity: The team can show that the defect came in with the first code, and that the later review named it without handing over code that fixed it.
  - `t05-hyperagent-xarray-4493` L08 `chunked_after_update`: a patch that says it keeps the chunks and does not (a split the hand check resolved to a loss)
    - loss: The issue asked that a chunked dask array stays chunked after a dataset update. The patch the editor reports at L08 writes no chunk handling, while its message says the chunks are kept; the code the editor hands over at L10 calls a dask function that, by the hand check's knowledge (not run), does not exist.
    - hold: A hold at L08 would have checked the patch, not the message about it, against the agreed behaviour and sent it back before the run went on.
    - opportunity: The maintainers get a patch whose agreed behaviour was checked at the hand-off, not an editor's statement that it holds.
  - `t06-hyperagent-matplotlib-25433` L07 `rangeslider_on_changed_like_button_on_clicked`: the asked behaviour missing from the brief (a proposal: both readers at 0.40 and 0.55)
    - loss: The issue asked that redrawing the figure inside a range slider's callback leaves the widgets usable, as it does for a button. At L07 the planner briefs the editor with a change to how the callback fires; both readers read the asked behaviour as not carried in that brief, below 0.8, and the hand check could not settle the editor's next change from the text.
    - hold: A hold at L07 would have asked for the issue's own case, a click on a widget after the redraw, to be run before the change went on.
    - opportunity: A fix goes out with the run that shows the issue's case passing, not on the word of the agent that wrote it.
  - `t07-hyperagent-matplotlib-18869` L16 `toplevel_comparable_version_info`: the run's own test shows the feature missing (a proposal: two readers at 0.80 and 0.75)
    - loss: The issue asked for version information that code can compare, on the package itself. At L16 the executor's run reports the attribute missing; both readers read the request as not met there, one at 0.80 and one at 0.75, so it is a proposal, not a finding.
    - hold: A hold at L16 would have kept the run from going on as if the feature existed, with the failed run as the reason.
    - opportunity: A maintainer sees the failed check beside the patch, instead of finding the missing attribute later.
  - `t08-ag2-olympiad-0` L01 `closed_form_even_minus_odd_weight`: an answer announced before the code ran (a split the hand check resolved to a loss)
    - loss: The task asked for a closed form of a difference of two counts, and told the solver to wait for the results of its code. The first reply, at L01, boxes 0 and says the code will show 0 before any code has run; the hand check's count by script gives -2.
    - hold: A hold at L01 would have kept the answer open until the code's own output came back, as the task's rules ask.
    - opportunity: The team sees that the wrong number was written before the check that should have produced it.
  - `t09-ag2-olympiad-1` L09 `largest_cardinality_no_tight_subcollection`: a wrong general answer handed in (a split the hand check resolved to a loss)
    - loss: The task asked for the largest size of a family of subsets with a stated property, for any n. The run's code found 15 for n = 4 only, at L06, and the final reply at L09 boxes 2^{n-1}, which the hand check reads as wrong. Reader 1 read it as carried; reader 2, a different model, read it as lost; the hand check sides with reader 2.
    - hold: A hold at L09 would have stopped the boxed answer before it was handed in as the result.
    - opportunity: An answer goes out only when it meets the task, and the card shows where the readers did not agree that it did.
  - `t10-ag2-olympiad-2` L02 `largest_number_of_dominoes`: a wrong number from the code's run, repeated in the final reply (a split the hand check resolved to a loss)
    - loss: The task asked for the most dominoes a board of m rows and 2n columns can take under stated rules. The code's run at L02 returns 9 for m = n = 3, and the final reply at L03 repeats it; by the hand check's knowledge of the problem (not run), the answer is 8.
    - hold: A hold at L02 would have read the computed number against the task before the final reply repeated it.
    - opportunity: The team can show that the wrong number came from the code's run, not from the last reply, and fix the step that made it.
