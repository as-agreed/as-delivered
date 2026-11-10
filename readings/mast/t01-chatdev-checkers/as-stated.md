# Task-as-stated proxy: Checkers (Draughts) game

Used for: t01-chatdev-checkers, t02-metagpt-checkers · Written on the night of 2026-10-30 to 31 (Moscow time) by Opus 5.5 (claude-opus-5-5), from the task statement alone; the run was not seen. MAST-Data records no agreement for any run; this proxy stands in for one. Source: MAST-Data (huggingface.co/datasets/mcemri/MAST-Data, CC BY 4.0), text scrubbed of paths.

## Task statement (verbatim)
> [cut: the task statement, which is the text of link L00 in links.jsonl (231 chars, sha256 b93f458ce431f11621809a7fc6f1c6d2805344fd4cd2e2e5f42581bb3c48793c), quoted here line by line]

## Terms
| id | type | term | rests on (words of the statement) |
|---|---|---|---|
| M1 | question | Develop a Checkers (Draughts) game. | "[cut 35 chars, sha256 2af93d6dcee7]" |
| M2 | object | A program for the board game Checkers, which the statement also names Draughts. | "[cut 26 chars, sha256 cced8b1570e1]"; "Prompt for moves"; "[cut 22 chars, sha256 3129f31cdf4e]" |
| M3 | criterion | The board is 8 by 8. | "[cut 16 chars, sha256 a56a728a3b38]" |
| M4 | criterion | Turns alternate between two players. | "[cut 35 chars, sha256 7ac118501c37]" |
| M5 | criterion | Captures follow the standard rules, read either as the jump that removes an opposing piece, or as the whole standard capture rule with compulsory capture and multiple jumps (two readings). | "[cut 40 chars, sha256 e09da79c43a7]" |
| M6 | criterion | Kinging follows the standard rule: a piece that reaches the far row becomes a king, which can then move and capture backward as well. | "[cut 40 chars, sha256 e09da79c43a7]" |
| M7 | criterion | The program prompts for each move, which the player gives in a notation; from-to positions are an example, not a requirement. | "[cut 54 chars, sha256 9fcee4752a88]" |
| M8 | criterion | Each move entered updates the board state to match it. | "[cut 34 chars, sha256 d68a2a93aa3a]" |

## Implicit, not counted
- The program starts and runs without crashing.
- The board is shown to the players, so they can see the position before choosing a move.
- The ordinary rules the statement does not name hold: the starting layout, how plain pieces move, refusal of illegal moves, and an end of the game with a winner.

## Left open by the statement
- Programming language, platform and number of files.
- The interface (text console or graphical window), provided moves are entered in a notation at a prompt.
- The exact notation (numbered squares or letter-and-digit coordinates, and the separator).
- How the board, the pieces and the kings are drawn.
- Which side moves first and what the sides are called.
- Whether both players are people, or one is played by the program; the statement says only "two players".
- Features beyond those named, such as undo, saving or a move history.
