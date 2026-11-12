# Capstone 2 - Invoice Validation Agent (draft spec, built Day 8)

> Assumption: I did not have my original spec.md in this session, so this reconstructs it from the Day 8 lab line:
> "Validation through your MCP tool - summary for clean invoices - exception list with reasons."
> Replace the rules/thresholds below with your own if they differ.

## Flow
invoices.json -> for each invoice call MCP tool `validate_invoice` -> clean? add to summary : add to exceptions (with reasons)

## Validation rules
1. Required fields present  2. No duplicate invoice number  3. GSTIN is 15 characters, valid format
4. Vendor is an approved (good) supplier  5. Line items = subtotal; GST = 18%; total = subtotal + GST (tolerance INR 1)
6. Date not in the future  7. PO exists, belongs to same vendor, subtotal <= remaining PO balance

## DONE WHEN
- [x] 5 invoices processed end to end through the MCP tool
- [x] Clean invoices -> summary (count, subtotal, GST, payable, by vendor)  -> clean_summary.json
- [x] Invalid invoices -> exception list, each with one or more reasons     -> exceptions.csv
- [x] Agent never pays or posts anything; exceptions wait for a human
- [x] 8 tests pass (test_capstone2.py)

## Human gate
Every exception goes to an AP clerk / finance reviewer. The agent never fixes or overrides an invoice.
