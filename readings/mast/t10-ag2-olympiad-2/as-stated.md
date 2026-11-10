# Task-as-stated proxy: Dominoes on an m by 2n board

Used for: t10-ag2-olympiad-2 · Written on the night of 2026-10-30 to 31 (Moscow time) by Opus 5.5 (claude-opus-5-5), from the task statement alone; the run was not seen. MAST-Data records no agreement for any run; this proxy stands in for one. Source: MAST-Data (huggingface.co/datasets/mcemri/MAST-Data, CC BY 4.0), text scrubbed of paths.

## Task statement (verbatim)
> [cut: the task statement, which is the text of link L00 in links.jsonl (1657 chars, sha256 fc76cc214928517be3bf878b9635b309d1d00b662e81a2d9ed89bcdfab7dcd40), quoted here line by line]

## Terms
| id | type | term | rests on (words of the statement) |
|---|---|---|---|
| M1 | question | (problem) Find the largest number of dominoes that can be placed on the board so that conditions (i) to (iv) all hold. | "[cut 40 chars, sha256 9233ebc2dbf8]"; "[cut 41 chars, sha256 7636893e0d43]"; "so that:" |
| M2 | object | (problem) A rectangular board of m rows and 2n columns of unit cells, and dominoes that are 1 by 2 or 2 by 1 rectangles. | "[cut 97 chars, sha256 8f9e9718a048]"; "[cut 50 chars, sha256 8193803baea3]" |
| M3 | premise | (problem) m and n are positive integers with n at least m, and the answer is for any such pair. | "[cut 42 chars, sha256 0956411700f0]" |
| M4 | criterion | (problem) Each domino covers exactly two adjacent cells of the board, and no two dominoes overlap. | "[cut 63 chars, sha256 66ab455fae9e]"; "[cut 29 chars, sha256 0399781249e0]" |
| M5 | criterion | (problem) No two dominoes together form a 2 by 2 square. | "[cut 44 chars, sha256 26be686294cc]" |
| M6 | criterion | (problem) The bottom row of the board is completely covered by n dominoes. | "[cut 71 chars, sha256 297fb1f6f4b4]" |
| M7 | frame | (standing instruction) Code, when written, is in the language named in the first line, set in the fenced block shown, and shows its output with `print`. | "[cut 41 chars, sha256 5fc53f54e8c1]"; "[cut 53 chars, sha256 735d34037e61]"; "[cut 57 chars, sha256 c88062884433]" |
| M8 | frame | (standing instruction) Numbers are given as fractions or radicals, not decimals, either in the code's output only or in every number including the final answer (two readings). | "[cut 47 chars, sha256 54dcb6b168a0]" |
| M9 | frame | (standing instruction) The solver first states the key idea for solving the problem. | "[cut 46 chars, sha256 e471d784079b]" |
| M10 | criterion | (standing instruction) Under Case 3, the solver works step by step without over-dividing, takes calculations out as code queries, and waits for the other party to give the results. | "[cut 65 chars, sha256 6f8e3202ba9e]"; "[cut 56 chars, sha256 56d5dfb5a633]"; "[cut 35 chars, sha256 65b752321b79]" |
| M11 | criterion | (standing instruction) Under Case 3, the solver goes on when a result looks correct, and corrects the query or the reasoning when a result is invalid or unexpected. | "[cut 127 chars, sha256 e42648d5b9af]" |
| M12 | frame | (standing instruction) Once all queries are run and the answer is reached, the answer is put in \boxed{}. | "[cut 81 chars, sha256 b60c35454fea]" |

## Implicit, not counted
- Code sent as a query runs and computes what the solver says it computes.
- The chat ends with one final answer.

## Left open by the statement
- Which of the three ways to work: Case 1 (a program that solves the problem), Case 2 (reasoning alone) or Case 3 (steps with code queries); the solver may choose.
- Whether to use helper packages (one is named as an example) and whether to enumerate arrangements.
- How much justification to give: the order asks for the key idea first and the boxed answer, and asks for no proof.
- How the answer is written as an expression in m and n, among equal forms.
