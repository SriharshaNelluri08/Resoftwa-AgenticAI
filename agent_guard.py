"""Rules in code. The agent (LLM) may only suggest. This code decides."""
import json, re, datetime, os

AMOUNT_LIMIT = 10_00_000          # Rs 10 lakh: above this a person must look
GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")  # 15 chars
INJECTION_WORDS = ("ignore all", "ignore previous", "approve me", "system prompt", "disregard")

def _audit(audit_path, run_id, step, result, reason=""):
    line = {"time": datetime.datetime.utcnow().isoformat(), "run_id": run_id,
            "step": step, "result": result, "reason": reason}
    with open(audit_path, "a", encoding="utf-8") as f:       # append only
        f.write(json.dumps(line) + "\n")

def _exception(audit_path, run_id, reason):
    _audit(audit_path, run_id, "decision", "exception", reason)
    return {"status": "exception", "reason": reason, "run_id": run_id}

def process_invoice(path, po_db, seen_ids, audit_path):
    run_id = os.path.basename(path)
    _audit(audit_path, run_id, "start", "ok")
    try:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return _exception(audit_path, run_id, "file is empty or missing")
        with open(path, encoding="utf-8") as f:
            inv = json.loads(f.read())
    except Exception as e:
        return _exception(audit_path, run_id, f"file cannot be read: {type(e).__name__}")

    need = ["invoice_id", "po_number", "vendor", "gstin", "invoice_date",
            "due_date", "amount", "lines"]
    missing = [k for k in need if k not in inv]
    if missing:
        return _exception(audit_path, run_id, f"missing fields: {missing}")

    text_blob = json.dumps(inv).lower()
    if any(w in text_blob for w in INJECTION_WORDS):
        return _exception(audit_path, run_id, "instruction text found inside invoice")

    if inv["invoice_id"] in seen_ids:
        return _exception(audit_path, run_id, "duplicate invoice")

    po = po_db.get(inv["po_number"])
    if po is None:
        return _exception(audit_path, run_id, "PO number does not exist")

    if inv["vendor"].strip().lower() != po["vendor"].strip().lower():
        return _exception(audit_path, run_id, "vendor name differs from PO vendor")

    if not GSTIN_RE.match(str(inv["gstin"])):
        return _exception(audit_path, run_id, "GSTIN is not valid (must be 15 characters)")

    try:
        d1 = datetime.date.fromisoformat(inv["invoice_date"])
        d2 = datetime.date.fromisoformat(inv["due_date"])
    except ValueError:
        return _exception(audit_path, run_id, "date format is wrong")
    if d2 < d1:
        return _exception(audit_path, run_id, "due date is before invoice date")

    try:
        amount = float(inv["amount"])
        line_sum = sum(float(l["amount"]) for l in inv["lines"])
    except Exception:
        return _exception(audit_path, run_id, "amount fields are not numbers")
    if abs(amount - line_sum) > 0.001:
        return _exception(audit_path, run_id, "total is not equal to sum of line items")
    if abs(amount - float(po["amount"])) > 0.001:
        return _exception(audit_path, run_id, "amount differs from PO amount")
    if amount > AMOUNT_LIMIT:
        return _exception(audit_path, run_id, "amount above limit, human must review")

    seen_ids.add(inv["invoice_id"])
    # Even a clean invoice is never posted here. A person approves first.
    _audit(audit_path, run_id, "decision", "waiting_for_approval", "all checks passed")
    return {"status": "waiting_for_approval", "reason": "all checks passed", "run_id": run_id}
