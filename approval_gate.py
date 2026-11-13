"""Approval gate. The agent can only SUBMIT. A named person must APPROVE.
Only then can POST run. Rules are in code, not in the prompt."""
import json, os
import audit

class GateError(Exception):
    pass

class ApprovalGate:
    def __init__(self, store_dir, audit_path):
        os.makedirs(store_dir, exist_ok=True)
        self.file = os.path.join(store_dir, "state.json")
        self.audit = audit_path

    def _load(self):
        if not os.path.exists(self.file):
            return {}
        with open(self.file, encoding="utf-8") as f:
            return json.load(f)

    def _save(self, d):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)

    # ---- used by the agent ----
    def submit(self, run_id, invoice_id, vendor, amount):
        d = self._load()
        d[invoice_id] = {"status": "waiting_for_approval", "run_id": run_id,
                         "vendor": vendor, "amount": amount}
        self._save(d)
        audit.append(self.audit, run_id, "submit", "waiting_for_approval", "sent to a person")

    # ---- used by a person ----
    def approve(self, invoice_id, approver):
        d = self._load(); rec = d.get(invoice_id)
        if not approver or approver.strip().lower() in ("agent", "claude", "ai"):
            raise GateError("a real person's name is required to approve")
        if not rec or rec["status"] != "waiting_for_approval":
            raise GateError("invoice is not waiting for approval")
        rec["status"] = "approved"; rec["approved_by"] = approver
        self._save(d)
        audit.append(self.audit, rec["run_id"], "approve", "approved", f"approved_by={approver}", actor=approver)

    def reject(self, invoice_id, approver, reason):
        d = self._load(); rec = d.get(invoice_id)
        if not rec or rec["status"] != "waiting_for_approval":
            raise GateError("invoice is not waiting for approval")
        rec["status"] = "rejected"; rec["rejected_by"] = approver
        self._save(d)
        audit.append(self.audit, rec["run_id"], "reject", "rejected", f"{approver}: {reason}", actor=approver)

    # ---- the only place that can post ----
    def post(self, invoice_id):
        d = self._load(); rec = d.get(invoice_id)
        if not rec or rec["status"] != "approved":
            audit.append(self.audit, rec["run_id"] if rec else invoice_id, "post", "blocked",
                         "post tried without approval", actor="system")
            raise GateError("blocked: invoice is not approved")
        rec["status"] = "posted"
        self._save(d)
        audit.append(self.audit, rec["run_id"], "post", "posted", f"approved_by={rec['approved_by']}", actor="system")

    def pending(self):
        return {k: v for k, v in self._load().items() if v["status"] == "waiting_for_approval"}

    def all(self):
        return self._load()
