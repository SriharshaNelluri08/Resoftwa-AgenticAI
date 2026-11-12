# Day 8 – Joule Agent Designs (designs.md)
---
## Design 1 – P2P Requisition Agent (from class pair exercise / core lab)
- **AGENT NAME:** Requisition-to-PO Agent
- **GOAL (1 line):** Turn an approved purchase requisition into a PO, or route it to a human when risky.
- **STARTS WHEN:** A new requisition is created or released.
- **SKILLS:**
  1. check_supplier – look up supplier status (good / new / poor) in suppliers.csv
  2. check_amount – compare amount to the ₹25 lakh limit
  3. create_po – write PO to po_created.json (never a real system)
  4. route_to_manager – send to procurement manager with a reason
  5. write_log – log decision + reason
- **AUTO WHEN:** Supplier is "good" AND amount <= ₹25 lakh → create PO.
- 🔴 **HUMAN WHEN:** Supplier is new or poor, OR amount > ₹25 lakh.
- **ESCALATE TO:** Procurement manager (if no reply in 2 working days → Head of Procurement).
- **LOG THESE:** requisition id, supplier, amount, supplier status, rule applied, decision (auto/manager), reason, timestamp.

## Design 2 – O2C Credit Check Agent
- **AGENT NAME:** Order Credit-Check Agent
- **GOAL (1 line):** Decide if a sales order can be released or must be held for credit review.
- **STARTS WHEN:** A sales order is saved and the credit check flags it (or on order creation).
- **SKILLS:**
  1. get_customer_credit – read credit limit, open items, overdue invoices
  2. calc_exposure – open orders + open invoices + this order vs. limit
  3. check_payment_history – any payments overdue > 30 days?
  4. release_order – remove the credit block (simulated: write to released_orders.json)
  5. route_to_credit_manager – hold the order and send it with the reason
- **AUTO WHEN:** Exposure <= credit limit AND no payment overdue > 30 days → release order.
- 🔴 **HUMAN WHEN:** Exposure > limit, OR overdue > 30 days, OR new customer with no history, OR order value > ₹10 lakh.
- **ESCALATE TO:** Credit manager (Finance); above ₹50 lakh → Finance Controller + Sales Head.
- **LOG THESE:** order id, customer, credit limit, exposure, overdue days, decision, reason, approver name (if human), timestamp.

## Design 3 – Leave Request Agent
- **AGENT NAME:** Leave Request Agent
- **GOAL (1 line):** Approve simple leave requests automatically and send the tricky ones to the manager.
- **STARTS WHEN:** An employee submits a leave request.
- **SKILLS:**
  1. check_leave_balance – does the employee have enough days?
  2. check_team_calendar – how many teammates are already off those dates?
  3. check_blackout_dates – year-end close, go-live, audit weeks
  4. approve_leave – record approval and update balance
  5. route_to_manager – send with reason and notify employee
- **AUTO WHEN:** Balance is enough AND <= 3 days AND team coverage >= 70% AND no blackout date → approve.
- 🔴 **HUMAN WHEN:** Balance is short, OR > 3 days, OR dates clash with team absence / blackout period, OR leave type is sensitive (medical, maternity, unpaid).
- **ESCALATE TO:** Line manager; if no action in 2 days → HR partner.
- **LOG THESE:** request id, employee id, dates, days, balance before/after, coverage %, decision, reason, approver, timestamp. (Do not log medical details.)

---
## Partner review (to be filled by the reviewing partner)
| Design | Reviewer | Date | Risk found / missed | Result |
|---|---|---|---|---|
| 1 P2P Requisition | | | | |
| 2 O2C Credit Check | | | | |
| 3 Leave Request | | | | |
