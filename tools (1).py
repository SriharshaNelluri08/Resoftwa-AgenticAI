"""Three small skills for the requisition agent. Pure Python, no network.
create_po ONLY writes to po_created.json - never to a real SAP system."""
import csv, json, os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
LIMIT = 2_500_000  # INR 25 lakh

def _path(name, base=None):
    return os.path.join(base or BASE, name)

def check_supplier(supplier: str, base: str = None) -> dict:
    """Skill 1: look up supplier status in suppliers.csv -> good / new / poor / unknown."""
    with open(_path("suppliers.csv", base), newline="") as f:
        for row in csv.reader(f):
            if row and row[0].strip().lower() == supplier.strip().lower():
                return {"supplier": supplier, "status": row[1].strip().lower()}
    return {"supplier": supplier, "status": "unknown"}

def create_po(req_id: str, supplier: str, amount: int, base: str = None) -> dict:
    """Skill 2: write a PO to po_created.json (sandbox file only)."""
    p = _path("po_created.json", base)
    pos = json.load(open(p)) if os.path.exists(p) else []
    po = {"po_number": f"PO-{len(pos)+1:04d}", "requisition": req_id,
          "supplier": supplier, "amount": amount,
          "created_at": datetime.now().isoformat(timespec="seconds")}
    pos.append(po)
    json.dump(pos, open(p, "w"), indent=2)
    return po

def route_to_manager(req_id: str, supplier: str, amount: int, reason: str, base: str = None) -> dict:
    """Skill 3: put the requisition in the procurement manager's queue with the reason."""
    p = _path("manager_queue.json", base)
    q = json.load(open(p)) if os.path.exists(p) else []
    item = {"requisition": req_id, "supplier": supplier, "amount": amount,
            "reason": reason, "status": "waiting for approval"}
    q.append(item)
    json.dump(q, open(p, "w"), indent=2)
    return item
