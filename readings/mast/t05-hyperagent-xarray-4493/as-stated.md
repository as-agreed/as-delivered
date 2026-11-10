# Task-as-stated proxy: Dataset.update loses chunking; constructor computes

Used for: t05-hyperagent-xarray-4493 · Written on the night of 2026-10-30 to 31 (Moscow time) by Opus 5.5 (claude-opus-5-5), from the task statement alone; the run was not seen. MAST-Data records no agreement for any run; this proxy stands in for one. Source: MAST-Data (huggingface.co/datasets/mcemri/MAST-Data, CC BY 4.0), text scrubbed of paths.

## Task statement (verbatim)
> [cut: the task statement, which is the text of link L00 in links.jsonl (2280 chars, sha256 9f18299894b39d8d0e920995cd056c024cfb8bee7f5fa92da7cd3e329b98cff2), quoted here line by line]

## Terms
| id | type | term | rests on (words of the statement) |
|---|---|---|---|
| M1 | question | Two deliverables: a `Dataset.update` that keeps a chunked array chunked, and an answer to whether, and why, the `Dataset` constructor computes a `DataArray` paired with dimension names. | "[cut 74 chars, sha256 85b595bf58e2]"; "[cut 137 chars, sha256 73a2df108268]"; "[cut 24 chars, sha256 a111a96fcf3c]" |
| M2 | object | The library's `Dataset`, through its `update` method and its constructor, each handed a chunked `DataArray`. | "DataSet.update"; "[cut 34 chars, sha256 e86ba752d3ea]" |
| M3 | criterion | After the update, the chunked `DataArray` is still chunked. | "[cut 62 chars, sha256 531dd915fde3]" |
| M4 | premise | Reproduction: a `DataArray` chunked with `.chunk()` is put in a `Dataset`; a slice of it, paired with dimension names in an update dict, is still chunked; then `ds.update(update_dict)` is called. | `[cut 26 chars, sha256 3546fd4bce79]`; `[cut 34 chars, sha256 5a3142845c0a]`; `[cut 45 chars, sha256 f1a427b5448a]`; `ds.update(update_dict)` |
| M5 | premise | As reported, the update evaluates the array's values eagerly: afterwards it is no longer chunked. | "[cut 74 chars, sha256 85b595bf58e2]"; "[cut 51 chars, sha256 2287ebcf941a]"; `[cut 30 chars, sha256 9e7e5437c5c7]` |
| M6 | premise | Building a `Dataset` from a lazily backed `DataArray` paired with dimension names computes it into an in-memory array, while the same `DataArray` given on its own stays lazy. | "[cut 113 chars, sha256 9cca717333ef]"; `[cut 57 chars, sha256 5932bf0cc3e9]`; `dask.array.core.Array`; `[cut 43 chars, sha256 4ecf4bc3c38b]`; `numpy.ndarray` |
| M7 | criterion | The `Dataset` constructor leaves a `DataArray` paired with dimension names uncomputed: required, the title reporting the computation as an issue, or not required, the text only asking whether it is intended (two readings). | "[cut 55 chars, sha256 c4be9479aad6]"; "Is it intentional" |

## Implicit, not counted
- The work ends in a change to the library's code; the issue text does not say so in words.
- The update still does its job: afterwards the dataset holds the new values.
- Behaviour that works today keeps working.

## Left open by the statement
- Where in the code the change goes, and how it keeps the array from being computed.
- Whether to add tests, and which.
- Which versions the change targets: the environment block records the reporter's setup, and neither issue rests on it.
- How the second issue's question is answered: through the change itself, in a comment or in a message.
