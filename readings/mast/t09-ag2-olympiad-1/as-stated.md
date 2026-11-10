# Task-as-stated proxy: Largest collection with no tight subcollection

Used for: t09-ag2-olympiad-1 · Written on the night of 2026-10-30 to 31 (Moscow time) by Opus 5.5 (claude-opus-5-5), from the task statement alone; the run was not seen. MAST-Data records no agreement for any run; this proxy stands in for one. Source: MAST-Data (huggingface.co/datasets/mcemri/MAST-Data, CC BY 4.0), text scrubbed of paths.

## Task statement (verbatim)
> [cut: the task statement, which is the text of link L00 in links.jsonl (1742 chars, sha256 0858e649a41bdd806325834782165ba8059398b7befdb9dd47d39153f712285f), quoted here line by line]

## Terms
| id | type | term | rests on (words of the statement) |
|---|---|---|---|
| M1 | question | (problem) Find the largest number of sets in a collection of proper non-empty subsets of X none of whose non-empty subcollections is tight. | "[cut 126 chars, sha256 8a9bb1f5ad64]" |
| M2 | object | (problem) Collections of subsets of a set X with n elements, for any integer n greater than 1. | "[cut 71 chars, sha256 19a3cc6043c5]" |
| M3 | premise | (problem) A non-empty collection of subsets of X is tight when its union is a proper subset of X and no element of X lies in exactly one of its sets. | "[cut 202 chars, sha256 f9a03c510789]" |
| M4 | premise | (problem) A subset is proper when it is not X itself, and the sets in a collection are distinct. | "[cut 97 chars, sha256 47f2f25f16ba]" |
| M5 | premise | (problem) The whole collection counts as one of its subcollections, so it must not be tight itself. | "[cut 54 chars, sha256 d6285dad98b2]" |
| M6 | frame | (standing instruction) Code, when written, is in the language named in the first line, set in the fenced block shown, and shows its output with `print`. | "[cut 41 chars, sha256 5fc53f54e8c1]"; "[cut 53 chars, sha256 735d34037e61]"; "[cut 57 chars, sha256 c88062884433]" |
| M7 | frame | (standing instruction) Numbers are given as fractions or radicals, not decimals, either in the code's output only or in every number including the final answer (two readings). | "[cut 47 chars, sha256 54dcb6b168a0]" |
| M8 | frame | (standing instruction) The solver first states the key idea for solving the problem. | "[cut 46 chars, sha256 e471d784079b]" |
| M9 | criterion | (standing instruction) Under Case 3, the solver works step by step without over-dividing, takes calculations out as code queries, and waits for the other party to give the results. | "[cut 65 chars, sha256 6f8e3202ba9e]"; "[cut 56 chars, sha256 56d5dfb5a633]"; "[cut 35 chars, sha256 65b752321b79]" |
| M10 | criterion | (standing instruction) Under Case 3, the solver goes on when a result looks correct, and corrects the query or the reasoning when a result is invalid or unexpected. | "[cut 127 chars, sha256 e42648d5b9af]" |
| M11 | frame | (standing instruction) Once all queries are run and the answer is reached, the answer is put in \boxed{}. | "[cut 81 chars, sha256 b60c35454fea]" |

## Implicit, not counted
- Code sent as a query runs and computes what the solver says it computes.
- The chat ends with one final answer.

## Left open by the statement
- Which of the three ways to work: Case 1 (a program that solves the problem), Case 2 (reasoning alone) or Case 3 (steps with code queries); the solver may choose.
- Whether to use helper packages (one is named as an example) and whether to enumerate arrangements.
- How much justification to give: the order asks for the key idea first and the boxed answer, and asks for no proof.
- How the answer is written as an expression in n, among equal forms.
