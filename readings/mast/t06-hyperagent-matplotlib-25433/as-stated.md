# Task-as-stated proxy: Range slider callback blocks widget input

Used for: t06-hyperagent-matplotlib-25433 · Written on the night of 2026-10-30 to 31 (Moscow time) by Opus 5.5 (claude-opus-5-5), from the task statement alone; the run was not seen. MAST-Data records no agreement for any run; this proxy stands in for one. Source: MAST-Data (huggingface.co/datasets/mcemri/MAST-Data, CC BY 4.0), text scrubbed of paths.

## Task statement (verbatim)
> [cut: the task statement, which is the text of link L00 in links.jsonl (1743 chars, sha256 24436ac63cb7d17f518f974a13e8bc6d25f001322d10455e0a52d73952ed5b87), quoted here line by line]

## Terms
| id | type | term | rests on (words of the statement) |
|---|---|---|---|
| M1 | question | Remove the block on widget input that follows clearing the figure, adding new widgets and redrawing inside a range slider's `on_changed` callback. | "[cut 92 chars, sha256 1173d7b1f277]" |
| M2 | object | The plotting library's range slider and button widgets, their callbacks, and mouse input to the widgets of a figure. | "[cut 32 chars, sha256 7bbf555db019]"; "[cut 30 chars, sha256 d9cbf66ff579]"; "input to widgets" |
| M3 | criterion | The range slider's `on_changed` behaves as the button's `on_clicked` does: after the same clear, re-add and redraw, the widgets take mouse input. | "[cut 88 chars, sha256 91b3dbeee201]" |
| M4 | premise | Reproduction: a script builds a range slider and a button whose callbacks both clear the figure, re-add the two widgets and redraw, then shows the figure. | "Code for reproduction"; `pyplot.clf()`; `addElements()`; `pyplot.draw()`; `slider.on_changed(onchanged)`; `button.on_clicked(onclick)`; `pyplot.show()` |
| M5 | premise | As reported, after the redraw inside the slider's callback no widget in the figure receives mouse clicks. | "[cut 116 chars, sha256 c0a6d266ffb9]"; "[cut 55 chars, sha256 048180577964]" |
| M6 | premise | The same steps inside the button's `on_clicked` cause no problem. | "[cut 77 chars, sha256 fd654ec00fe2]"; "[cut 41 chars, sha256 577318d03368]" |
| M7 | premise | The problem appears on two operating systems with two different interactive backends, both at library version 3.6.2. | "[cut 42 chars, sha256 64457dc45a61]"; "Matplotlib backend: QtAgg"; "Windows 10"; "TkAgg"; "Matplotlib version: 3.6.2" |

## Implicit, not counted
- The work ends in a change to the library's code.
- The range slider still works as a slider: moving it still runs its callback with the new values.
- Widgets that work today, the button among them, keep working.

## Left open by the statement
- Where in the code the change goes, and how it restores input.
- Whether and how to test it; the behaviour involves mouse clicks in a window.
- Which backends the change is tried on.
