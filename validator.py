"""Invoice validation rules (the logic behind the MCP tool `validate_invoice`).
Pure Python, no network. Thresholds are training assumptions - see spec.md."""
import csv, json, os, re
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
GST_RATE = 0.18
TOLERANCE = 1  # INR
GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
REQUIRED = ["invoice_no", "vendor", "gstin", "date", "lines", "subtotal", "gst", "total"]

def _vendors():
    with open(os.path.join(BASE, "suppliers.csv"), newline="") as f:
        return {r[0].strip().lower(): r[1].strip().lower() for r in csv.reader(f) if r}

def _pos():
    return {p["po_number"]: p for p in json.load(open(os.path.join(BASE, "purchase_orders.json")))}

def validate_invoice(invoice: dict, po_billed: dict = None, seen_numbers: set = None) -> dict:
    """Return {"invoice_no", "valid": bool, "reasons": [str]}.
    po_billed: INR already invoiced per PO (cumulative check); seen_numbers: invoice numbers already processed."""
    po_billed = po_billed if po_billed is not None else {}
    seen_numbers = seen_numbers if seen_numbers is not None else set()
    r = []
    missing = [k for k in REQUIRED if invoice.get(k) in (None, "", [])]
    if missing:
        r.append(f"missing required field(s): {', '.join(missing)}")
    no = invoice.get("invoice_no", "?")
    if no in seen_numbers:
        r.append(f"duplicate invoice number {no}")
    if invoice.get("gstin") and not GSTIN_RE.match(invoice["gstin"]):
        r.append(f"invalid GSTIN format '{invoice['gstin']}' (needs 15 characters)")
    # vendor
    status = _vendors().get(str(invoice.get("vendor", "")).lower(), "unknown")
    if status != "good":
        r.append(f"vendor '{invoice.get('vendor')}' is not an approved supplier (status: {status})")
    # arithmetic
    lines = invoice.get("lines") or []
    line_sum = sum(l["qty"] * l["rate"] for l in lines)
    if lines and abs(line_sum - invoice.get("subtotal", 0)) > TOLERANCE:
        r.append(f"line items add up to INR {line_sum:,} but subtotal says INR {invoice['subtotal']:,}")
    sub = invoice.get("subtotal", 0)
    exp_gst = round(sub * GST_RATE)
    if abs(exp_gst - invoice.get("gst", 0)) > TOLERANCE:
        r.append(f"GST should be INR {exp_gst:,} (18% of {sub:,}) but invoice shows INR {invoice.get('gst', 0):,}")
    if abs(sub + invoice.get("gst", 0) - invoice.get("total", 0)) > TOLERANCE:
        r.append(f"total INR {invoice.get('total', 0):,} does not equal subtotal + GST")
    # date
    try:
        if date.fromisoformat(invoice.get("date", "")) > date.today():
            r.append("invoice date is in the future")
    except ValueError:
        r.append("invoice date is not a valid YYYY-MM-DD date")
    # PO match (cumulative)
    po_no = invoice.get("po_number")
    if not po_no:
        r.append("no purchase order reference")
    else:
        po = _pos().get(po_no)
        if not po:
            r.append(f"PO {po_no} not found")
        else:
            if po["supplier"].lower() != str(invoice.get("vendor", "")).lower():
                r.append(f"PO {po_no} belongs to {po['supplier']}, not {invoice.get('vendor')}")
            remaining = po["amount"] - po_billed.get(po_no, 0)
            if sub > remaining:
                r.append(f"subtotal INR {sub:,} exceeds remaining balance INR {remaining:,} on {po_no} (PO INR {po['amount']:,})")
    return {"invoice_no": no, "valid": not r, "reasons": r}
