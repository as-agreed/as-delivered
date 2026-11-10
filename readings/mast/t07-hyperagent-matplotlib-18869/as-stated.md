# Task-as-stated proxy: Comparable version info at top level

Used for: t07-hyperagent-matplotlib-18869 · Written on the night of 2026-10-30 to 31 (Moscow time) by Opus 5.5 (claude-opus-5-5), from the task statement alone; the run was not seen. MAST-Data records no agreement for any run; this proxy stands in for one. Source: MAST-Data (huggingface.co/datasets/mcemri/MAST-Data, CC BY 4.0), text scrubbed of paths.

## Task statement (verbatim)
> [cut: the task statement, which is the text of link L00 in links.jsonl (1679 chars, sha256 7dd8362fb8c82bea71e6c8f2b93b063accc07b500b5293bae113d3db190a583a), quoted here line by line]

## Terms
| id | type | term | rests on (words of the statement) |
|---|---|---|---|
| M1 | question | Add version information that is easy to compare, for quick version checks, to the library's top level. | "[cut 46 chars, sha256 28efedc61d22]"; "[cut 24 chars, sha256 3550909a8022]" |
| M2 | object | The version information the library exposes at its top level. | "version info"; "exposes `__version__`" |
| M3 | premise | The library currently exposes only `__version__`. | "[cut 48 chars, sha256 f29f4494886a]" |
| M4 | premise | Comparing version strings works in practice until version 3.10 or 4.10, which is not expected soon, but the reporter finds it unclean. | "[cut 161 chars, sha256 73abbb64cb74]" |
| M5 | criterion | The new information is a `version_info` tuple that compares with other tuples, or a `LooseVersion` instance that compares properly with strings; either only these two forms count, or they are proposals for any easily comparable form (two readings). | "[cut 161 chars, sha256 4a4eab8d8012]" |
| M6 | criterion | The new information is reachable at the library's top level. | "to toplevel" |

## Implicit, not counted
- The work ends in a change to the library's code.
- The new information gives the same version as `__version__`.
- `__version__` stays as it is.

## Left open by the statement
- Which of the two forms, or both: the reporter slightly prefers `LooseVersion`, notes that the tuple is more common and perhaps simpler, and expects this point to be argued over.
- What the `LooseVersion` attribute is called; the statement names only the tuple, `version_info`.
- What the tuple holds: how many parts, and how a pre-release or development version shows in it.
- How the information is derived from the version string, and where in the code.
- Tests and documentation.
