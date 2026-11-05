# Day 05 — Lab log

## Goal
Document the agent loop with the real tool names and push the day-05 folder.

## What I built / reviewed
- Loop in `agent.py`: call model -> run requested tools -> append `tool_result` -> repeat.
- Stops on `stop_reason != "tool_use"` or after `MAX_STEPS = 10`.
- Tools: `list_purchase_orders` (read-only), `get_supplier_contact` (read-only),
  `send_email` (only side effect, human y/n gate).
- Every call appended to `audit.jsonl` (see `audit.sample.jsonl`).

## Evidence
- Sample run: 3 late POs found, 2 emails approved, 1 refused. Refusal is logged
  with `decision: "refused"`.
- Diagram: `agent-loop.txt`.

## Observations
- The gate lives in the dispatcher, so the model cannot skip it.
- Parallel `tool_use` blocks in one step are all executed before the next model call.

## Limits / honest notes
- Model in the sample run was an offline stub (no network in sandbox); tools,
  gate, cap and audit log are real code. Live run needs ANTHROPIC_API_KEY.
- PO data is mocked. `send_email` is simulated (no SMTP).

## Next
- Run against live Claude and capture a real transcript.
- Hash-chain the audit log.
