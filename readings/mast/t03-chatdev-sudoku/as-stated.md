# Task-as-stated proxy: Sudoku puzzle game

Used for: t03-chatdev-sudoku, t04-metagpt-sudoku · Written on the night of 2026-10-30 to 31 (Moscow time) by Opus 5.5 (claude-opus-5-5), from the task statement alone; the run was not seen. MAST-Data records no agreement for any run; this proxy stands in for one. Source: MAST-Data (huggingface.co/datasets/mcemri/MAST-Data, CC BY 4.0), text scrubbed of paths.

## Task statement (verbatim)
> [cut: the task statement, which is the text of link L00 in links.jsonl (276 chars, sha256 6dc2b590dc350ceb8089121f508086eb7d6ae4fb20515669e8b8843200fead98), quoted here line by line]

## Terms
| id | type | term | rests on (words of the statement) |
|---|---|---|---|
| M1 | question | Develop a classic Sudoku puzzle game. | "[cut 36 chars, sha256 14aa41d947fd]" |
| M2 | object | A program in which a player fills in a classic Sudoku puzzle. | "[cut 26 chars, sha256 4201770afe0d]"; "[cut 35 chars, sha256 9acd8c499b52]" |
| M3 | criterion | The grid is 9 by 9. | "[cut 15 chars, sha256 edce6eb03031]" |
| M4 | criterion | The game's rule: every row, every column and every 3 by 3 subgrid must contain each digit from 1 to 9 exactly once. | "[cut 83 chars, sha256 ec95ba572466]" |
| M5 | criterion | The player can enter a value into a cell of their choice. | "[cut 51 chars, sha256 369b1adcc343]" |
| M6 | criterion | The program checks for mistakes, a mistake being either an entry that breaks the row, column or subgrid rule, or an entry that differs from the puzzle's solution (two readings). | "check for mistakes" |
| M7 | criterion | The program confirms when the puzzle is completed, completed term either every cell filled, or every cell filled so that the rule holds (two readings). | "[cut 36 chars, sha256 a8852578adac]" |

## Implicit, not counted
- The program starts and runs without crashing.
- The grid is shown to the player, with the values entered so far.
- The game starts from a puzzle: a grid with some cells already filled, for the player to complete.
- Entries outside the grid, or other than the digits 1 to 9, are refused.

## Left open by the statement
- Programming language, platform and number of files.
- The interface (text console or graphical window) and how the player names a cell and a value.
- Where the puzzle comes from (built in, generated or loaded), how many puzzles there are and how hard they are.
- Whether the given cells are protected, and whether an entry can be changed or erased.
- When the mistake check and the completion confirmation run: on their own after each entry, or when the player asks; the sentence "[cut 113 chars, sha256 620c4d0cdf06]" allows both.
- How a mistake is shown to the player.
- Features beyond those named, such as hints, a timer or saving.
