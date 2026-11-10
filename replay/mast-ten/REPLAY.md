# Replay the ten MAST runs

The bench that read these runs, run again on the reads it stored: no model is called. The sequence below fetches the ten public rows, rebuilds each run's links, puts back every text this folder cuts, and runs the bench (`../bin/bench.py`, whose only change is the text of two table headers) on the `as-agreed` package installed from PyPI, each model prompt answered with the read stored for it. It prints tier 1's verdicts on the reads, other than PRESERVED, run by run, and checks that the replay gives what this folder holds. Python 3.9 or later, `curl`, and a network for two things only: one GET per row to the dataset server (a neutral User-Agent, nothing sent but the URL) and `pip install` from PyPI.

## Run it

Paste into a terminal at the root of this repository (the folder that holds `LICENSE` and `replay/`). Set `PY` to the Python you want to test.

```bash
PY=python3
R=$(pwd); W=$(mktemp -d)
$PY -m venv $W/venv && $W/venv/bin/pip install -q --disable-pip-version-check as-agreed==0.0.1
mkdir -p $W/public-readings/mast && cp -R replay/bin $W/bin && cp -R build $W/public-readings/mast/
cd $W && venv/bin/python -I -B bin/convert_mast.py dl runs 0 30 1 31 180 181 182 571 572 573
venv/bin/python -I -B bin/cut_replay.py restore $R/replay/mast-ten runs full
venv/bin/python -I -B bin/replay.py $R/replay/mast-ten runs full out
```

- Done when the last line reads `replay: bench exit 0; every check passed` (about two minutes).
- Then open `$W/out/cards/<run>.html`: the same cards as each `card.html` here, with the quotes in place. `$W/out/maps/<run>.svg` is each `flow.svg`.
- Stop if a line says `DIFFERS`: the dataset server serves another trajectory for that row (the rows API takes no revision), and its texts cannot be put back.

## What each line does

1. A new virtual environment with `as-agreed` 0.0.1 from PyPI, the version this folder was replayed on, and no other package. A later version may class a read differently.
2. The bench's files and the collection's `build/` go into the temporary folder, where `convert_mast.py` looks for the extractor (`../public-readings/mast/build/extract.py`) and `cut_replay.py` for `cut.py`.
3. `convert_mast.py` fetches the ten rows (`curl -q -f`, one GET each), prints whether each trajectory's sha256 is the one in `../../ATTRIBUTION.md`, and rebuilds each run's `links.jsonl` with `build/extract.py`.
4. `cut_replay.py restore` puts back every cut text from the rebuilt links and the scrubbed trajectory, checks each text and each whole file against its sha256 in `cuts.jsonl`, and checks that the rebuilt `links.jsonl` cuts to the public one byte for byte. One line per run.
5. `replay.py` runs the bench as chunk 1, its first batch of runs (2026-11-05), ran it (`--mode exchange --drafter-version v1 --reader-version v2 --second-reader --second-rule d44`, each record reused as drafted). Reader 1 answers from `reads.jsonl`, matched by run, link and fields; reader 2 from `second-reads.jsonl`, matched by run and the sha256 of the prompt. The bench's clock reads the stored reads' date, so its rows carry the day the reads were made. Per run it prints tier 1's verdicts other than PRESERVED, the run's result after the hand check (`hand-check.md`), and four checks:
   - `verdict lines as the stored ledger's`: every line of the report `as_agreed.report.build` makes from the new ledger is the line it makes from this folder's `ledger.jsonl`, byte for byte (a ledger's run id and times differ from run to run, its lines do not);
   - `reads as stored`: the `reads.jsonl` and `second-reads.jsonl` the bench writes are the stored ones, byte for byte;
   - `map as flow.svg`: `as_agreed.report.redraw(ledger, svg)` draws `flow.svg`, byte for byte: the shareable map, counts and step names, no value (the cards carry the values and the quotes);
   - `card as card.html`: the run's cards, drawn by `cards.py` from the bench's rows and cut by this folder's own cuts, are `card.html`, byte for byte.

## The files in `../bin/`

| file | sha256 | what it is |
|---|---|---|
| `bench.py` | `784653cce5a6a8efdc07f45a8b53e738f5efa0507b9a4328aa61c81a4ac6da6a` | the trace bench, copied from the study on 2026-11-07 with one change: in two table-header strings a person's name reads "the project" (the study's file: `7b1b0e968e890c67b0a704c5766b0aee70735bc7c7660459a91b00dc39259642`); the replay never writes those headers into what it checks |
| `models.py` | `77c3cbc1b42677938045fef0e636b2c55fd8a5b0611d08c03cf34ef05d7afd65` | its model callers (imported by `bench.py`); the replay replaces the caller, not the file |
| `prompts.py` | `f4c56e9a67a6cfd1366d1bf452a3601da4f43ee274f340822faaf87ce6ff2caf` | its prompts and the reader's checks (imported by `bench.py`) |
| `cards.py` | `de8a0ad9b8c00067b99cd7299c7f7b2d6c8723173855945c3aef3442e65c2ee8` | the card renderer, unchanged |
| `convert_mast.py` | `35096c8a3caeafdbba1582c6ba1ef4651d6bbe0692faa50251a9aff682c77571` | the fetch and split of the MAST rows, unchanged |
| `replay.py` | `278f0becc5f04cfcb32e5b80cd94bae1c1dcea963204d83f8561b3fbee103b21` | new: the stored-read caller, the checks, the card page (one run, no tally) |
| `cut_replay.py` | `f2b1c66ea437b7693fa641d9e45c982201e53bf87545ee38353c81e6ed4421d3` | new: cut and restore for the JSON files and the hand check, on top of `build/cut.py` |

The library (`as_agreed`) is the PyPI package, unchanged; `models.py`, `prompts.py`, `cards.py` and `convert_mast.py` are the study's files, unchanged. Nothing in `../bin/` imports anything outside the Python standard library and `as_agreed`.

## Proof, 2026-11-07

The sequence above, taken from this file as it stands and run twice, each time from a fresh copy of this tree in a new temporary folder with its own virtual environment and `as-agreed` 0.0.1 from PyPI: once with `PY=python3` (Python 3.14.6) and once with `PY=/usr/bin/python3` (Python 3.9.6), on macOS. Both exit 0 and end `replay: bench exit 0; every check passed`; every run passes all four checks on both. `diff` of the two outputs:

```text
23c23
< Python 3.14.6; as_agreed 0.0.1
---
> Python 3.9.6; as_agreed 0.0.1
```

The output on Python 3.14.6, whole (the 3.9.6 output is the same but for that line):

```text
0	t01-chatdev-checkers	hash matches the readings
30	t02-metagpt-checkers	hash matches the readings
1	t03-chatdev-sudoku	hash matches the readings
31	t04-metagpt-sudoku	hash matches the readings
180	t05-hyperagent-xarray-4493	hash matches the readings
181	t06-hyperagent-matplotlib-25433	hash matches the readings
182	t07-hyperagent-matplotlib-18869	hash matches the readings
571	t08-ag2-olympiad-0	hash matches the readings
572	t09-ag2-olympiad-1	hash matches the readings
573	t10-ag2-olympiad-2	hash matches the readings
t01-chatdev-checkers: links.jsonl matches; commitments.json matches; reads.jsonl matches; second-reads.jsonl matches; ledger.jsonl matches
t02-metagpt-checkers: links.jsonl matches; commitments.json matches; reads.jsonl matches; second-reads.jsonl matches; ledger.jsonl matches
t03-chatdev-sudoku: links.jsonl matches; commitments.json matches; reads.jsonl matches; second-reads.jsonl matches; ledger.jsonl matches
t04-metagpt-sudoku: links.jsonl matches; commitments.json matches; reads.jsonl matches; second-reads.jsonl matches; ledger.jsonl matches
t05-hyperagent-xarray-4493: links.jsonl matches; commitments.json matches; reads.jsonl matches; second-reads.jsonl matches; ledger.jsonl matches
t06-hyperagent-matplotlib-25433: links.jsonl matches; commitments.json matches; reads.jsonl matches; second-reads.jsonl matches; ledger.jsonl matches
t07-hyperagent-matplotlib-18869: links.jsonl matches; commitments.json matches; reads.jsonl matches; second-reads.jsonl matches; ledger.jsonl matches
t08-ag2-olympiad-0: links.jsonl matches; commitments.json matches; reads.jsonl matches; second-reads.jsonl matches; ledger.jsonl matches
t09-ag2-olympiad-1: links.jsonl matches; commitments.json matches; reads.jsonl matches; second-reads.jsonl matches; ledger.jsonl matches
t10-ag2-olympiad-2: links.jsonl matches; commitments.json matches; reads.jsonl matches; second-reads.jsonl matches; ledger.jsonl matches
hand-check.md: matches
restore: every cut text put back; each file matches its sha256 before the cut
Python 3.14.6; as_agreed 0.0.1
t01-chatdev-checkers
  L07-programmer WEAKENED commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.60: standard_capture_rules = False where True was agreed
  L08-programmer DROPPED commitment player_count limit.players read at 0.50: present upstream, absent downstream
  L08-programmer WEAKENED commitment alternate_turns acceptance_criteria.alternate_turns read at 0.70: alternate_turns = False where True was agreed
  L08-programmer WEAKENED commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.55: standard_capture_rules = False where True was agreed
  L08-programmer WEAKENED commitment prompt_moves acceptance_criteria.prompt_moves_in_notation read at 0.70: prompt_moves_in_notation = False where True was agreed
  L08-programmer WEAKENED commitment update_board acceptance_criteria.update_board_state read at 0.50: update_board_state = False where True was agreed
  L09-code-reviewer restored_equivalent commitment player_count limit.players read at 0.70: same set
  L09-code-reviewer restored_equivalent commitment alternate_turns acceptance_criteria.alternate_turns read at 0.85: alternate_turns = True
  L09-code-reviewer restored_equivalent commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.45: standard_capture_rules = True
  L09-code-reviewer restored_equivalent commitment prompt_moves acceptance_criteria.prompt_moves_in_notation read at 0.85: prompt_moves_in_notation = True
  L09-code-reviewer restored_equivalent commitment update_board acceptance_criteria.update_board_state read at 0.85: update_board_state = True
  L10-code-reviewer WEAKENED commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.55: standard_capture_rules = False where True was agreed
  L11-programmer WEAKENED commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.55: standard_capture_rules = False where True was agreed
  L12-programmer WEAKENED commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.55: standard_capture_rules = False where True was agreed
  L13-code-reviewer WEAKENED commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.45: standard_capture_rules = False where True was agreed
  L14-code-reviewer WEAKENED commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.55: standard_capture_rules = False where True was agreed
  L15-programmer WEAKENED commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.55: standard_capture_rules = False where True was agreed
  L16-programmer WEAKENED commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.55: standard_capture_rules = False where True was agreed
  L17-code-reviewer restored_equivalent commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.55: standard_capture_rules = True
  L18-code-reviewer WEAKENED commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.65: standard_capture_rules = False where True was agreed
  L19-programmer restored_equivalent commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.50: standard_capture_rules = True
  result after the hand check: loss by hand check; verdict lines as the stored ledger's: yes; reads as stored: yes; map as flow.svg: yes; card as card.html: yes
t02-metagpt-checkers
  L01-simplecoder WEAKENED commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.80: standard_capture_rules = False where True was agreed
  L04-simpletester restored_equivalent commitment capture_rules acceptance_criteria.standard_capture_rules read at 0.60: standard_capture_rules = True
  result after the hand check: loss by hand check; verdict lines as the stored ledger's: yes; reads as stored: yes; map as flow.svg: yes; card as card.html: yes
t03-chatdev-sudoku
  L07-programmer DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L07-programmer DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L08-programmer DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L08-programmer DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L10-code-reviewer DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L10-code-reviewer DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L11-programmer DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L11-programmer DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L12-programmer DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L12-programmer DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L13-code-reviewer DROPPED commitment digit_range limit.digit_min read at 0.45: present upstream, absent downstream
  L13-code-reviewer DROPPED commitment digit_range limit.digit_max read at 0.45: present upstream, absent downstream
  L14-code-reviewer DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L14-code-reviewer DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L15-programmer DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L15-programmer DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L16-programmer DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L16-programmer DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L17-code-reviewer DROPPED commitment digit_range limit.digit_min read at 0.50: present upstream, absent downstream
  L17-code-reviewer DROPPED commitment digit_range limit.digit_max read at 0.50: present upstream, absent downstream
  L18-code-reviewer DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L18-code-reviewer DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L19-programmer DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L19-programmer DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L20-chief-technology-officer DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L20-chief-technology-officer DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L22-counselor DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L22-counselor DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L24-chief-executive-officer DROPPED commitment digit_range limit.digit_min read at 0.65: present upstream, absent downstream
  L24-chief-executive-officer DROPPED commitment digit_range limit.digit_max read at 0.65: present upstream, absent downstream
  L25-chief-product-officer restored_equivalent commitment digit_range limit.digit_min read at 0.75: same bound
  L25-chief-product-officer restored_equivalent commitment digit_range limit.digit_max read at 0.75: same bound
  result after the hand check: proposal; verdict lines as the stored ledger's: yes; reads as stored: yes; map as flow.svg: yes; card as card.html: yes
t04-metagpt-sudoku
  L01-simplecoder WEAKENED commitment input_values acceptance_criteria.player_inputs_cell_values read at 0.50: player_inputs_cell_values = False where True was agreed
  L01-simplecoder WEAKENED commitment check_mistakes acceptance_criteria.check_for_mistakes read at 0.50: check_for_mistakes = False where True was agreed
  L01-simplecoder WEAKENED commitment confirm_completion acceptance_criteria.confirm_puzzle_completed read at 0.55: confirm_puzzle_completed = False where True was agreed
  L02-simpletester restored_equivalent commitment input_values acceptance_criteria.player_inputs_cell_values read at 0.70: player_inputs_cell_values = True
  L02-simpletester restored_equivalent commitment check_mistakes acceptance_criteria.check_for_mistakes read at 0.65: check_for_mistakes = True
  L02-simpletester restored_equivalent commitment confirm_completion acceptance_criteria.confirm_puzzle_completed read at 0.70: confirm_puzzle_completed = True
  result after the hand check: loss by hand check; verdict lines as the stored ledger's: yes; reads as stored: yes; map as flow.svg: yes; card as card.html: yes
t05-hyperagent-xarray-4493
  L08-editor WEAKENED commitment stays_chunked acceptance_criteria.chunked_after_update read at 0.50: chunked_after_update = False where True was agreed
  L09-planner restored_equivalent commitment stays_chunked acceptance_criteria.chunked_after_update read at 0.50: chunked_after_update = True
  result after the hand check: loss by hand check; verdict lines as the stored ledger's: yes; reads as stored: yes; map as flow.svg: yes; card as card.html: yes
t06-hyperagent-matplotlib-25433
  L07-planner WEAKENED commitment same_as_button acceptance_criteria.rangeslider_on_changed_like_button_on_clicked read at 0.40: rangeslider_on_changed_like_button_on_clicked = False where True was agreed
  L11-planner restored_equivalent commitment same_as_button acceptance_criteria.rangeslider_on_changed_like_button_on_clicked read at 0.60: rangeslider_on_changed_like_button_on_clicked = True
  result after the hand check: proposal; verdict lines as the stored ledger's: yes; reads as stored: yes; map as flow.svg: yes; card as card.html: yes
t07-hyperagent-matplotlib-18869
  L08-executor WEAKENED commitment comparable_version acceptance_criteria.toplevel_comparable_version_info read at 0.55: toplevel_comparable_version_info = False where True was agreed
  L08-executor DROPPED commitment version_object limit.version_object read at 0.40: present upstream, absent downstream
  L09-planner WEAKENED commitment comparable_version acceptance_criteria.toplevel_comparable_version_info read at 0.55: toplevel_comparable_version_info = False where True was agreed
  L09-planner DROPPED commitment version_object limit.version_object read at 0.55: present upstream, absent downstream
  L13-planner restored_equivalent commitment comparable_version acceptance_criteria.toplevel_comparable_version_info read at 0.60: toplevel_comparable_version_info = True
  L13-planner restored_equivalent commitment version_object limit.version_object read at 0.60: inside the bound: one of LooseVersion, version_info
  L16-executor WEAKENED commitment comparable_version acceptance_criteria.toplevel_comparable_version_info read at 0.80: toplevel_comparable_version_info = False where True was agreed
  L16-executor DROPPED commitment version_object limit.version_object read at 0.50: present upstream, absent downstream
  L17-planner WEAKENED commitment comparable_version acceptance_criteria.toplevel_comparable_version_info read at 0.60: toplevel_comparable_version_info = False where True was agreed
  L17-planner DROPPED commitment version_object limit.version_object read at 0.55: present upstream, absent downstream
  L18-editor restored_equivalent commitment comparable_version acceptance_criteria.toplevel_comparable_version_info read at 0.70: toplevel_comparable_version_info = True
  L18-editor restored_equivalent commitment version_object limit.version_object read at 0.70: inside the bound: one of LooseVersion, version_info
  result after the hand check: proposal; verdict lines as the stored ledger's: yes; reads as stored: yes; map as flow.svg: yes; card as card.html: yes
t08-ag2-olympiad-0
  L01-assistant WEAKENED commitment wait_for_results acceptance_criteria.wait_for_query_results read at 0.70: wait_for_query_results = False where True was agreed
  L03-assistant WEAKENED commitment state_key_idea acceptance_criteria.state_key_idea_first read at 0.55: state_key_idea_first = False where True was agreed
  result after the hand check: loss by hand check; verdict lines as the stored ledger's: yes; reads as stored: yes; map as flow.svg: yes; card as card.html: yes
t09-ag2-olympiad-1
  L01-assistant WEAKENED commitment boxed_answer acceptance_criteria.answer_in_boxed read at 0.50: answer_in_boxed = False where True was agreed
  L01-assistant DROPPED commitment n_bound limit.n read at 0.50: present upstream, absent downstream
  L01-assistant WEAKENED commitment largest_cardinality acceptance_criteria.largest_cardinality_no_tight_subcollection read at 0.65: largest_cardinality_no_tight_subcollection = False where True was agreed
  L03-assistant WEAKENED commitment state_key_idea acceptance_criteria.state_key_idea_first read at 0.50: state_key_idea_first = False where True was agreed
  L03-assistant WEAKENED commitment boxed_answer acceptance_criteria.answer_in_boxed read at 0.50: answer_in_boxed = False where True was agreed
  L03-assistant DROPPED commitment n_bound limit.n read at 0.50: present upstream, absent downstream
  L03-assistant WEAKENED commitment largest_cardinality acceptance_criteria.largest_cardinality_no_tight_subcollection read at 0.65: largest_cardinality_no_tight_subcollection = False where True was agreed
  L05-assistant WEAKENED commitment state_key_idea acceptance_criteria.state_key_idea_first read at 0.50: state_key_idea_first = False where True was agreed
  L05-assistant WEAKENED commitment boxed_answer acceptance_criteria.answer_in_boxed read at 0.50: answer_in_boxed = False where True was agreed
  L05-assistant DROPPED commitment n_bound limit.n read at 0.50: present upstream, absent downstream
  L05-assistant WEAKENED commitment largest_cardinality acceptance_criteria.largest_cardinality_no_tight_subcollection read at 0.65: largest_cardinality_no_tight_subcollection = False where True was agreed
  L07-assistant WEAKENED commitment state_key_idea acceptance_criteria.state_key_idea_first read at 0.55: state_key_idea_first = False where True was agreed
  L07-assistant WEAKENED commitment boxed_answer acceptance_criteria.answer_in_boxed read at 0.60: answer_in_boxed = False where True was agreed
  L07-assistant DROPPED commitment n_bound limit.n read at 0.40: present upstream, absent downstream
  L07-assistant WEAKENED commitment largest_cardinality acceptance_criteria.largest_cardinality_no_tight_subcollection read at 0.50: largest_cardinality_no_tight_subcollection = False where True was agreed
  L08-mathproxyagent restored_equivalent commitment boxed_answer acceptance_criteria.answer_in_boxed read at 0.55: answer_in_boxed = True
  L09-assistant WEAKENED commitment state_key_idea acceptance_criteria.state_key_idea_first read at 0.55: state_key_idea_first = False where True was agreed
  L09-assistant WEAKENED commitment no_over_divide acceptance_criteria.no_over_divided_steps read at 0.40: no_over_divided_steps = False where True was agreed
  L09-assistant DROPPED commitment n_bound limit.n read at 0.40: present upstream, absent downstream
  L09-assistant restored_equivalent commitment largest_cardinality acceptance_criteria.largest_cardinality_no_tight_subcollection read at 0.50: largest_cardinality_no_tight_subcollection = True
  result after the hand check: loss by hand check; verdict lines as the stored ledger's: yes; reads as stored: yes; map as flow.svg: yes; card as card.html: yes
t10-ag2-olympiad-2
  L01-assistant WEAKENED commitment state_key_idea acceptance_criteria.state_key_idea_first read at 0.45: state_key_idea_first = False where True was agreed
  L01-assistant WEAKENED commitment wait_for_results acceptance_criteria.wait_for_query_results read at 0.50: wait_for_query_results = False where True was agreed
  L01-assistant WEAKENED commitment boxed_answer acceptance_criteria.answer_in_boxed read at 0.50: answer_in_boxed = False where True was agreed
  L01-assistant WEAKENED commitment largest_dominoes acceptance_criteria.largest_number_of_dominoes read at 0.60: largest_number_of_dominoes = False where True was agreed
  L01-assistant WEAKENED commitment no_overlap acceptance_criteria.no_domino_overlap read at 0.40: no_domino_overlap = False where True was agreed
  L03-assistant WEAKENED commitment state_key_idea acceptance_criteria.state_key_idea_first read at 0.55: state_key_idea_first = False where True was agreed
  L03-assistant restored_equivalent commitment boxed_answer acceptance_criteria.answer_in_boxed read at 0.90: answer_in_boxed = True
  L03-assistant restored_equivalent commitment largest_dominoes acceptance_criteria.largest_number_of_dominoes read at 0.50: largest_number_of_dominoes = True
  result after the hand check: loss by hand check; verdict lines as the stored ledger's: yes; reads as stored: yes; map as flow.svg: yes; card as card.html: yes
replay: bench exit 0; every check passed
```

## How this folder was made

The authors' step, on the stored results of chunk 1: the ten MAST run folders (`commitments.json`, `reads.jsonl`, `second-reads.jsonl`) and the rows of the ten runs in the chunk's hand check. From the same temporary layout as above, with `<stored>` that folder:

```bash
venv/bin/python -I -B bin/replay.py $R/replay/mast-ten runs <stored> pass1 --write      # the ledgers
venv/bin/python -I -B bin/cut_replay.py make <stored> pass1/chunk-1 runs $R/replay/mast-ten
venv/bin/python -I -B bin/replay.py $R/replay/mast-ten runs <stored> pass2 --write      # flow.svg and card.html
```

Chunk 1 feeds this folder, not the regression of 2026-11-06 (reader-v4, spec draft 9): the regression kept rows and tables only, no per-run reads, so it cannot be replayed. Under chunk 1's rules the replay gives the same units and classes as chunk 1's own rows for all ten runs (checked on 2026-11-07 against the study's `rows.json`, which is not in this folder).

## What a replay cannot give

It replays the stored reads; it does not read again. Every record of what was agreed is a model's proxy, drafted from the task statement alone, and every read is one model's read of one link [C]; the class is tier 1's, deterministic given those reads [D]. Two readers agreeing is not truth, and neither is the hand check. To test the reads, give a model or a person each link and the reader prompt of `prompts.py` (reader-v2), and compare with `reads.jsonl`.
