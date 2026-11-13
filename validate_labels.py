"""Proof 1: the labels agree with the real rule code (src/agent_guard.py)."""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from agent_guard import process_invoice
MAP = [("instruction text","injection"),("duplicate","duplicate"),("po number does not exist","po_missing"),
       ("vendor","vendor_mismatch"),("gstin","gstin_invalid"),("due date","date_error"),
       ("sum of line items","total_mismatch"),("differs from po amount","amount_mismatch"),
       ("above limit","over_limit"),("empty","empty_file")]
def code_of(res):
    if res["status"] == "waiting_for_approval": return "none"
    r = res["reason"].lower()
    return next((c for k, c in MAP if k in r), "other")
labels = json.load(open(os.path.join(HERE, "labels.json")))
cfg = json.load(open(os.path.join(HERE, "po_db.json")))
seen = set(cfg["already_processed"]); audit = os.path.join(tempfile.mkdtemp(), "a.log"); bad = 0
for name, lab in sorted(labels.items()):
    r = process_invoice(os.path.join(HERE, "invoices", name), cfg["po_db"], seen, audit)
    got = (r["status"], code_of(r)); want = (lab["decision"], lab["code"])
    ok = got == want; bad += (not ok)
    print(f"{name}  label={want[1]:<16} rules_say={got[1]:<16} {'OK' if ok else 'MISMATCH'}")
print(f"\n{len(labels)-bad} of {len(labels)} labels agree with the rule code")
sys.exit(1 if bad else 0)
