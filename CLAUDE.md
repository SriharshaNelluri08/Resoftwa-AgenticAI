# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Project: Phase 1 ABAP training programs
Language: ABAP
System: SAP training system (S/4HANA )
Files: .abap copies of program

## What this repo is

A single SAP ABAP executable report, `sales_report.abap`, which defines the program `ZSHN_SALES_ORDER_DATA`. There is no build system, package manifest, test suite, or linter in the repo. Nothing here can be compiled or run from the command line.

## Commands
- No build or npm commands. Code lives in the SAP system.
- Tests: ABAP Unit, run inside ADT (Eclipse) with Ctrl+Shift+F10
- Local files here are copies exported for review

- Activate and run: import the source into program `ZSHN_SALES_ORDER_DATA` in SE38 or ABAP Development Tools (Eclipse), activate it, then execute (F8).
- Run a single selection: the only input is the `S_VBELN` select-option (sales document number range). Use it to narrow the result.
- Syntax check: done by the ABAP compiler on activation in the SAP system. There is no local equivalent.

Do not invent test or lint commands. If tests or tooling are added later, document them here.

## Code architecture

The whole program runs in two events:

1. **Selection screen**: a single `SELECT-OPTIONS s_vbeln FOR gw_final-vbeln`, inside a framed block `b1`. The `gw_final` work area is used only to borrow the `VBAK-VBELN` type.
2. **`START-OF-SELECTION`**: one inner join of `VBAK` (sales document header) with `VBAP` (sales document items) on `VBELN`, filtered by `S_VBELN`. Results go into `GT_FINAL`, a standard table of `TY_FINAL`. That type is a flat row combining header fields (`VBELN`, `AUART`, `NETWR`, `WAERK`, `VKORG`, `VTWEG`, `SPART`) and item fields (`POSNR`, `MATNR`, `KWMENG`, `VRKME`). So there is one output row per sales order item.
3. **Display**: `CL_SALV_TABLE=>FACTORY` builds an ALV grid over `GT_FINAL`. The code then optimizes column widths and enables all toolbar functions before `DISPLAY`.

Data flows in one direction: selection input → one SQL join → one internal table → ALV output. There are no subroutines, classes, or modules.

## Known issues in the current code

- The `TRY ... CATCH cx_salv_msg` block has an empty handler. If `FACTORY` fails, `GO_SALV` stays unbound and the next line (`get_columns`) raises a runtime error. Any change to this block should handle the exception or stop cleanly.
- The `SELECT` has no `ORDER BY`, so row order is not defined.
- `TEXT-001` (the frame title) is referenced but must be maintained as a text symbol in the SAP system; it is not defined in the source.

## Rules
- Never edit files outside this folder
- Do not change any code until I approve a plan
- Explain every change in simple English
- Ask before adding or deleting any file
- Flag obsolete statements (MOVE, header lines, OCCURS, SELECT *)
- Use only trainer samples or my own training code. Never real client data
