"""Requisition agent: rules + a human gate.
Known good supplier AND amount <= INR 25 lakh -> create PO.
New / poor / unknown supplier, OR amount > INR 25 lakh -> route to manager.
Every decision is logged with a reason in decision_log.jsonl."""
import json, os, sys
from datetime import datetime
import tools

def decide(req: dict, base: str = None) -> dict:
    sup = tools.check_supplier(req["supplier"], base)
    reasons = []
    if sup["status"] != "good":
        reasons.append(f"supplier status is '{sup['status']}' (not a known good supplier)")
    if req["amount"] > tools.LIMIT:
        reasons.append(f"amount INR {req['amount']:,} is above the INR 25,00,000 limit")
    if reasons:
        reason = "; ".join(reasons)
        tools.route_to_manager(req["id"], req["supplier"], req["amount"], reason, base)
        decision, result = "MANAGER", "sent to procurement manager"
    else:
        reason = f"known good supplier and amount INR {req['amount']:,} is within the INR 25,00,000 limit"
        po = tools.create_po(req["id"], req["supplier"], req["amount"], base)
        decision, result = "AUTO", f"PO created: {po['po_number']}"
    entry = {"time": datetime.now().isoformat(timespec="seconds"), "requisition": req["id"],
             "supplier": req["supplier"], "amount": req["amount"],
             "supplier_status": sup["status"], "decision": decision,
             "result": result, "reason": reason}
    with open(tools._path("decision_log.jsonl", base), "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

def main(base: str = None):
    base = base or tools.BASE
    for f in ("po_created.json", "manager_queue.json", "decision_log.jsonl"):
        if os.path.exists(tools._path(f, base)): os.remove(tools._path(f, base))
    reqs = json.load(open(tools._path("requisitions.json", base)))
    print(f"{'ID':<5}{'SUPPLIER':<16}{'AMOUNT (INR)':>13}  {'DECISION':<8} REASON")
    print("-" * 100)
    for r in reqs:
        e = decide(r, base)
        print(f"{e['requisition']:<5}{e['supplier']:<16}{e['amount']:>13,}  {e['decision']:<8} {e['reason']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
