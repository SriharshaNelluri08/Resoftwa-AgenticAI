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

## Project explanation

I haven't changed any files. This explains the current sales_report.abap, including the IF go_salv IS BOUND guard on lines 50–54.

1. What the program does for the user

The user runs report ZSHN_SALES_ORDER_DATA in SAP. A smalge of sales order numbers. The user can leave it empty toget all orders. After they run it, SAP shows a table with one row per sales order item. Each row has the order's header information and that item's details. In the table the user can sort, filter, and export.

2. Code walkthrough, in order

Setup (lines 6–23)
- Line 6: REPORT zshn_sales_order_data. names the program.
- Lines 8–20: ty_final defines one output row, with 7 heawr, waerk, vkorg, vtweg, spart) and 4 item fields (posnr,matnr, kwmeng, vrkme).
- Lines 22–23: gt_final is the list of rows in memory. gw

Selection screen (lines 25–27)
- Line 25 opens a framed box with the title from text symbol TEXT-001.
- Line 26: SELECT-OPTIONS s_vbeln FOR gw_final-vbeln creates the from/to order-number input. gw_final is only there to supply the data type.
- Line 27 closes the box.

Data selection (lines 29–45)
- Line 29: START-OF-SELECTION is where processing begins, after the user runs the screen.
- Lines 31–41 list the fields to read. The a~ prefix means the field comes from the header table, and b~ means the item table.
- Lines 41–43: join header (vbak AS a) to items (vbap AS tch.
- Line 44: put the results into gt_final.
- Line 45: keep only order numbers inside the user's rang

Display (lines 46–54)
- Lines 46–49: build the ALV grid inside a TRY ... CATCH. The CATCH on line 48 is empty, so errors are ignored.
- Line 50: IF go_salv IS BOUND only continues if the grid object was created.
- Line 51: auto-size the columns.
- Line 52: switch on all the standard toolbar buttons.
- Line 53: show the grid.

3. Tables, classes, and methods                                                                                                               
┌──────────────────┬────────────────────────────────┬───────────────────────────────────────────────────────────────────────────────────────┐     Item       │              Type              │           Purpose                                        │
├──────────────────┼────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤ AK             │ Database table                 │ Sale, net value, currency, sales org, channel, division) │
├──────────────────┼────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤
│ VBAP             │ Database table                 │ Sales document items (item number, material, quantity, unit)                          │ ───────────────┼────────────────────────────────┼──────────────────────────────────────────────────────────┤
│ CL_SALV_TABLE    │ Class                          │ SAP's standard tool for building an ALV grid                                          │
├──────────────────┼────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤ ctory( )       │ Static method of CL_SALV_TABLE │ Cre internal table                                       │
├──────────────────┼────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤
│ get_columns( )   │ Method                         │ Returns the grid's column settings                                                    │ ───────────────┼────────────────────────────────┼──────────────────────────────────────────────────────────┤
│ set_optimize( )  │ Method of the columns object   │ Auto-fits column widths                                                               │
├──────────────────┼────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤ t_functions( ) │ Method                         │ Retngs                                                   │
├──────────────────┼────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤
│ set_all( )       │ Method of the functions object │ Turns on every standard toolbar function                                              │ ───────────────┼────────────────────────────────┼──────────────────────────────────────────────────────────┤
│ display( )       │ Method                         │ Shows the grid on screen                                                              │
├──────────────────┼────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤ _SALV_MSG      │ Exception class                │ Rait                                                     │
└──────────────────┴────────────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────┘ 
4. What I'm not sure about                                                                                                                    
- TEXT-001: I can't see its content, because it lives in the SAP system and not in the file. It may be missing or have a different title than expected.                                                                                                                                   havior I haven't run: I haven't run this code or seenut what the user sees comes from reading the code and myABAP knowledge.
- Field meanings: My descriptions of the VBAK and VBAP fields come from standard SAP knowledge. Your training system could differ.            w order: There's no ORDER BY, so the order is whateveuld look sorted by accident.
- Empty range: I assume an empty selection returns all orders, which is standard ABAP behavior. On a large system that could be slow.
- Authorizations: The code has no authority checks, and I don't know whether your system requires any.                     

## Risks
                                                                                                                                           Here  are the risks in the current sales_report.abap, fromy come from reading the code. I haven't run it.

Functional risks
                                                                                                                                              ilent failure (line 48). The CATCH cx_salv_msg handled on line 50 stops the crash, but if the grid can't bebuilt, the user sees a blank screen with no message. They can't tell an error from "no data".
2. No message when nothing is found. If the join returns no rows, the user gets an empty grid with no explanation.                            ndefined row order (lines 31–45). There's no ORDER BYween runs or databases. That makes results hard tocompare.
4. Missing frame title (line 25). TEXT-001 lives in the SAP system, not in the file. If it isn't maintained, or is lost when the program is   ransported or copied, the frame title is blank.

Performance risks                                                                                                                             
5. Unrestricted read. If the user leaves s_vbeln empty, the join reads every order and item. On a large system that could be slow or use a lot of memory, since everything goes into gt_final at once.                                                                                    o row limit. There's no UP TO n ROWS or any other cap

Security and data risks                                                                                                                       
7. No authority check. The code doesn't check whether the user may see sales data (for example, by sales organization). Anyone who can run theeport sees everything it selects.
8. Real-data exposure. Your CLAUDE.md says to use only training data. If this report ran on a system with real client data, the point above   ould matter much more.

Maintainability risks                                                                                                                         
9. Stale documentation. CLAUDE.md's "Known issues" section still describes the old unguarded code, so it no longer matches the file.
10. No tests in the repo. CLAUDE.md mentions ABAP Unit in ADT, but I found no test code here. If tests exist, they're only in the SAP system, and nothing in the repo shows them.
11. Repo copy can drift. CLAUDE.md says the local files are exported copies, so they can fall out of step with the program in SAP.

Things that are not risks

The file contains none of the obsolete statements from yo OCCURS, SELECT *).

I haven't changed anything. If you want these addressed, pproval. The most valuable fixes are probably an errormessage in the CATCH, an ORDER BY, and an authority check.


Here are the risks in the current sales_report.abap, from most to least important. They come from reading the code. I haven't run it.

Functional risks

1. Silent failure (line 48). The CATCH cx_salv_msg handler is empty. The IS BOUND guard on line 50 stops the crash, but if the grid can't be built, the user sees a blank screen with no message. They can't tell an error from "no data".
2. No message when nothing is found. If the join returns no rows, the user gets an empty grid with no explanation.
3. Undefined row order (lines 31–45). There's no ORDER BY, so the order can change between runs or databases. That makes results hard to compare.
4. Missing frame title (line 25). TEXT-001 lives in the SAP system, not in the file. If it isn't maintained, or is lost when the program is transported or copied, the frame title is blank.

Performance risks

5. Unrestricted read. If the user leaves s_vbeln empty, t item. On a large system that could be slow or use a lotof memory, since everything goes into gt_final at once.
6. No row limit. There's no UP TO n ROWS or any other cap.

Security and data risks

7. No authority check. The code doesn't check whether the user may see sales data (for example, by sales organization). Anyone who can run the report sees everything it selects.
8. Real-data exposure. Your CLAUDE.md says to use only tran on a system with real client data, the point abovewould matter much more.

Maintainability risks

9. Stale documentation. CLAUDE.md's "Known issues" section still describes the old unguarded code, so it no longer matches the file.
10. No tests in the repo. CLAUDE.md mentions ABAP Unit in ADT, but I found no test code here. If tests exist, they're only in the SAP system,
    and nothing in the repo shows them.
11. Repo copy can drift. CLAUDE.md says the local files are exported copies, so they can fall out of step with the program in SAP.

Things that are not risks

The file contains none of the obsolete statements from yo OCCURS, SELECT *).

I haven't changed anything. If you want these addressed, pproval. The most valuable fixes are probably an errormessage in the CATCH, an ORDER BY, and an authority check.