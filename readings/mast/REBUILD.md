# Rebuild the ten MAST runs

These folders hold no third-party text. Each cut text is kept as its sha256 and its length, in the file and in the folder's `cuts.jsonl`. This page gives the commands that fetch the public rows, rebuild the full `links.jsonl`, and put every cut text back, checking each sha256. Python 3.9 or later, standard library only; no model, no account.

## What is cut, and what stays

- `links.jsonl`: each link's `text` (130 links). The record keeps `chars` and gains `text_sha256`; the first line, the run's metadata, gains a `cut` note.
- `as-stated.md`: the task statement under "Task statement (verbatim)" (10), which is the text of link L00.
- `as-stated.md`, `reading.md`: each quote of 4 or more words, in double quotes or in code font, found in the run's links, its scrubbed trajectory or its reference block (218), printed as `[cut <chars> chars, sha256 <first 12>]`. Shorter quotes stay, as do the names of MAST's failure modes and quotes of the proxy itself.
- In every file, the word "meaning" of 2026-10-31 is printed "term" (689 places, none inside a quote).
- `fates.csv`, `flow.svg`, `counts.md`, `counts.csv` hold no third-party text.

## Rebuild one run, then all ten

From the root of this repository. The fetch is one GET per row; the row and everything rebuilt from it stay in a temporary folder.

```bash
W=$(mktemp -d)
rebuild() {  # $1 = folder, $2 = row
  curl -q -sS -A "Mozilla/5.0" -o "$W/$1.json" "https://datasets-server.huggingface.co/rows?dataset=mcemri/MAST-Data&config=default&split=train&offset=$2&length=1"
  python3 -I -B build/extract.py "$W/$1.json" "$W/rebuilt/$1" "$W/scratch/$1" > /dev/null
  python3 -I -B build/cut.py restore "readings/mast/$1" "$W/rebuilt/$1" "$W/scratch/$1" "$W/full/$1"
}
rebuild t02-metagpt-checkers 30
```

Expected:

```text
links.jsonl: rebuilt sha256 matches; cuts to the public file byte for byte
as-stated.md: 10 texts put back; sha256 matches the original 7591efebf159
reading.md: 6 texts put back; sha256 matches the original 4f2af368359a
fates.csv: 0 texts put back; sha256 matches the original 5196f72330c7
flow.svg: 0 texts put back; sha256 matches the original 891b2a5d3377
```

`cut.py` exits 1 on any mismatch. All ten:

```bash
for p in t01-chatdev-checkers:0 t02-metagpt-checkers:30 t03-chatdev-sudoku:1 t04-metagpt-sudoku:31 \
         t05-hyperagent-xarray-4493:180 t06-hyperagent-matplotlib-25433:181 t07-hyperagent-matplotlib-18869:182 \
         t08-ag2-olympiad-0:571 t09-ag2-olympiad-1:572 t10-ag2-olympiad-2:573; do
  echo "${p%%:*}"; rebuild "${p%%:*}" "${p#*:}"
done
python3 -I -B build/cut.py restore readings/mast "$W" "$W" "$W/full"   # counts.md, counts.csv
```

`$W/full/<folder>/` then holds the files of 2026-10-31, and `$W/rebuilt/<folder>/links.jsonl` the full links. The sha256 of `as-stated.md` restored is the one fixed before any run was read (t01 and t02 `7591efeb…`, t03 and t04 `7e051cb5…`, t05 `9ba1cc38…`, t06 `f9a24a85…`, t07 `655c2cf7…`, t08 `3e49137a…`, t09 `d9f02531…`, t10 `91ce3ae6…`; full values in each `cuts.jsonl`). `$W/scratch/<folder>/` holds the scrubbed trajectory, `trace-scrubbed.txt`, which some readings cite by line ("log line N").

## The pinned parts

| part | pin |
|---|---|
| the source | `mcemri/MAST-Data`, revision `95118ac951421753cf1deb87ddea3b01e693c41b`; the rows API takes no revision, so each run is pinned by the sha256 of its trajectory (`../../ATTRIBUTION.md`) |
| the extractor | `build/extract.py`: splits a row into links, scrubs it, counts status markers per link [D] |
| the lexicon | `build/lexicon.py`, the claim-ledger lexicon frozen on 2026-10-31, sha256 `cd8d753835d9ac1c44f41371b9c51a1008c1ec90c1b92ed9c89332314c767eb7` (also in each `links.jsonl` header) |
| the cut | `build/cut.py`: `links` cuts a full `links.jsonl`; `restore` puts every text back; `make` is the authors' step and shows the rule |
| the maps | `build/maps.py <mast-folder> <scratch> <draw_flow.py>` with the renderer `draw_flow.py` of https://github.com/as-agreed/as-agreed (Apache-2.0), sha256 `c7b12133f15c222056ae90a05047f37f9850a9a687833e766d04380f8b3083f8`, redraws all ten `flow.svg` byte for byte from these `fates.csv` (checked 2026-11-06). It writes into the folder it is given: run it on a copy |

## Full links.jsonl, by sha256

| folder | row | sha256 of the full `links.jsonl` |
|---|---|---|
| `t01-chatdev-checkers/` | 0 | `91d1ef03f314e35235274112e429eeeaaf4b5e31be3e5d518a91bf68869ad752` |
| `t02-metagpt-checkers/` | 30 | `0cc3de3e6729ffd04d24b813f0abea612e9f95148a42adfd5164fa2712b7d91d` |
| `t03-chatdev-sudoku/` | 1 | `97fb04ef6874d38c67b64b2a7968db206fad1368016e001e9a5131aa1daf0a82` |
| `t04-metagpt-sudoku/` | 31 | `ea08ab3570d632bb77808c8522d743a6e1789f4b6a87d518806ea180d450d734` |
| `t05-hyperagent-xarray-4493/` | 180 | `782c608134ec04039c700137ac910a510451c84d3437f87c73567cfdfa2b263c` |
| `t06-hyperagent-matplotlib-25433/` | 181 | `aebabc934bfce212e8f99ebbad34d84be3433cfd5b85c200d16fd0dc039dfa9c` |
| `t07-hyperagent-matplotlib-18869/` | 182 | `77442723e4f59c8b30a8f60bea7a641ecfd22397afa58fdc8c1de8376fb46bc9` |
| `t08-ag2-olympiad-0/` | 571 | `21cf26e224e911788d0b3b2073284a459ea34615dfeac1203129734ce1a408b4` |
| `t09-ag2-olympiad-1/` | 572 | `8e6e947554939104ade5164aac365f832127e21a96df1485eeade85acd4ef9c1` |
| `t10-ag2-olympiad-2/` | 573 | `f980bdf51873df12125093214fb22fc9a0b54e35a877a45146f627c72ff3c267` |

## What a rebuild cannot give

It gives back the links and the [D] counts exactly, and the files as they were written. It does not redo the [C] tier: every fate, site and map is one run, read by a model (Opus 5.5, the night of 2026-10-30 to 31), no second rater. To test that tier, give any model or person `as-stated.md`, the links and the protocol in each `reading.md`, and compare the `fates.csv` it writes with these. `counts.md` and `counts.csv` were made from the ten `fates.csv` and the `links.jsonl` headers by a table script that is not in this set.

## What each run folder holds

| file | what it holds | tier |
|---|---|---|
| `as-stated.md` | the task-as-stated proxy, written from the task statement alone before the run was read: its terms, typed (question, object, criterion, premise, frame), and what the statement leaves open | [C], written blind |
| `links.jsonl` | line 1: the row's metadata, MAST's annotation, hashes, scrub counts; then one line per link: from, to, kind, phase, `chars`, `text_sha256`, marker counts | [D] |
| `reading.md` | the reading: terms and claims link by link, losses and their sites, MAST's label against this reading, limits | [C] |
| `fates.csv` | one row per term and per claim, one column per link, then the state at the commit, the first loss and its site; last row the comparison with MAST | [C] |
| `flow.svg` | the map, drawn from `fates.csv` | [C] |
| `cuts.jsonl` | for each file: its sha256 of 2026-10-31, and each cut with its place, its sha256, its length and where its text sits in the rebuilt sources | [D] |
