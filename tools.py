"""Day 5 warm-up: the 4 role-play tools as plain Python functions over pos.json."""
import json
import uuid
from datetime import date
from pathlib import Path

POS_FILE = Path(__file__).with_name("pos.json")
TODAY = date(2026, 10, 24)          # role-play date from the goal card
_DRAFTS = {}                        # draft_id -> {"vendor":..., "text":...}


def _load_pos():
    with open(POS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _is_late(po):
    """Late = due date passed AND not fully delivered (computed vs TODAY)."""
    due = date.fromisoformat(po["dueDate"])
    return due < TODAY and po["deliveredQty"] < po["orderedQty"]


def _status_text(po):
    if po["deliveredQty"] == 0:
        return "not delivered"
    if po["deliveredQty"] < po["orderedQty"]:
        return "partly delivered"
    return "fully delivered"


# ---------- Tool 1 ----------
def list_open_pos():
    """All POs that still have pending quantity."""
    return [
        {
            "po_number": p["poNumber"],
            "vendor_name": p["vendor_name"],
            "due_date": p["dueDate"],
            "ordered_qty": p["orderedQty"],
            "delivered_qty": p["deliveredQty"],
        }
        for p in _load_pos()
        if p["deliveredQty"] < p["orderedQty"]
    ]


# ---------- Tool 2 ----------
def get_po_status(po_number):
    """Status of one PO. Returns {'error': ...} if not found."""
    for p in _load_pos():
        if p["poNumber"] == str(po_number):
            days_late = max((TODAY - date.fromisoformat(p["dueDate"])).days, 0)
            return {
                "po_number": p["poNumber"],
                "vendor_name": p["vendor_name"],
                "status": _status_text(p),
                "qty": f'{p["deliveredQty"]}/{p["orderedQty"]}',
                "due_date": p["dueDate"],
                "is_late": _is_late(p),
                "days_late": days_late if _is_late(p) else 0,
            }
    return {"error": f"PO {po_number} not found"}


# ---------- Tool 3 ----------
def draft_email(vendor, text):
    """Create a draft only. Nothing is sent."""
    if not vendor or not text:
        return {"error": "vendor and text are required"}
    draft_id = "D-" + uuid.uuid4().hex[:6]
    _DRAFTS[draft_id] = {"vendor": vendor, "text": text}
    return {"draft_id": draft_id, "vendor": vendor, "status": "drafted"}


# ---------- Tool 4 ----------
def send_email(draft_id):
    """Simulated send (risky step - Human approval is added in the Level-up)."""
    draft = _DRAFTS.get(draft_id)
    if draft is None:
        return {"error": f"draft {draft_id} not found"}
    return {"draft_id": draft_id, "vendor": draft["vendor"], "status": "sent (simulated)"}
