# Day 8 Lab Log - SAP Joule & Joule Studio

**Skill vs agent:** Today I built skills (`check_supplier`, `create_po`, `route_to_manager`, `validate_invoice`) that each do one small rule-based action the same way every time, and I built agents (the requisition agent and the invoice pipeline) that decide which skills to call, choose auto vs human for each case, and log the reason, so skills do, agents plan, and a human approves where the risk is.

## What I built
- 3 agent designs on the template: P2P requisition, O2C credit check, leave request (`designs.md`, PDF). Partner review: pending.
- Requisition agent (code path, no Joule Studio tenant): 3 auto POs, 2 to manager, 7 tests pass.
- Capstone 2: 5 invoices validated through an MCP tool, 3 clean, 2 exceptions with reasons, 8 tests pass.

## Not done yet
- ABAP + AI level-up (explain, obsolete statements, ABAP Unit tests) - needs my Phase 1 ABAP code.
- Partner sign-off on the 3 designs.
