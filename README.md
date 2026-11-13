# Capstone 2 - Safe Invoice Agent

An invoice-reading agent that checks supplier invoices against purchase orders (PO), and never posts anything without a named person approving it.

## What it does
- Reads an invoice file.
- Checks it with rules written in code: empty file, instruction text inside the invoice, duplicate, PO exists, vendor matches, GSTIN has 15 characters, dates make sense, total equals the line items, amount equals the PO, amount is under the limit.
- A bad invoice goes to the exception list with a reason.
- A good invoice goes to "waiting_for_approval". It is never posted by the agent.
- A person approves or rejects. Only an approved invoice can be posted.
- Every step is written to an audit log that can be replayed and checked for tampering.

## The 4 guardrails and where they live
- Human in the loop: `src/approval_gate.py`. The agent can only submit. Approve needs a real name. Post needs approval.
- Least privilege: the agent code only has read, check and submit. It has no post function. Post is in the gate, run by a person's command.
- Audit trail: `src/audit.py`. One JSON line per step. Each line holds the hash of the line before it, so an edit or a deleted line is found by `verify`.
- Boss and workers: the model only suggests (see `eval/run_eval.py`). Code (`src/agent_guard.py`) decides. Checks run as small separate steps in a fixed order.

## Folder map
- `src/agent_guard.py` - the rules
- `src/approval_gate.py` - submit, approve, reject, post
- `src/audit.py` - audit log and verify
- `src/cli.py` - commands for a person
- `tests/test_attacks.py` - 10 attack tests
- `tests/test_gate_and_audit.py` - 7 gate and audit tests
- `eval/` - 20 labelled invoices and the Haiku 5.5 vs Sonnet 5.5 comparison
- `demo.py` - the 3-minute demo
- `DEMO_SCRIPT.md`, `rehearsal_log.md`, `DEMO_READY.md` - demo material

## How to run (SAP Business Application Studio terminal)
- Run all tests: `python3 -m unittest discover -s tests -v`
- Run the demo: `python3 demo.py`
- See what waits for approval: `python3 src/cli.py pending`
- Approve: `python3 src/cli.py approve INV-3001 "Your Name"`
- Post: `python3 src/cli.py post INV-3001`
- Replay one invoice: `python3 src/cli.py replay inv_01.json`
- Check the log: `python3 src/cli.py verify`
- Model comparison: `export ANTHROPIC_API_KEY=...` then `python3 eval/run_eval.py`

## Known limits (what would stop me going to production)
- Posting is simulated. It does not call a real SAP system yet.
- The approval state and the audit log are files. Production needs a database and a protected log store.
- The hash chain shows tampering but does not stop it. Keep a copy in a separate store.
- Approver names are typed, not checked against a login. Production needs SAP roles or XSUAA.
- The invoice is JSON. Real invoices are PDF or images and need a reading step first.
- Rules cover the 10 known attacks only. New attack types need new tests.
- Use a dev or training system only. Never production.
