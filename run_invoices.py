"""Capstone 2 pipeline: read invoices -> validate each through the MCP tool ->
summary for clean invoices + exception list with reasons."""
import csv, json, os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))

class McpClient:
    def __init__(self):
        self.p = subprocess.Popen([sys.executable, os.path.join(BASE, "mcp_server.py")], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True, cwd=BASE)
        self.n = 0
        self.call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                 "clientInfo": {"name": "capstone2-agent", "version": "1.0"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    def _send(self, m): self.p.stdin.write(json.dumps(m) + "\n"); self.p.stdin.flush()
    def call(self, method, params=None):
        self.n += 1
        self._send({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params or {}})
        resp = json.loads(self.p.stdout.readline())
        if "error" in resp: raise RuntimeError(resp["error"])
        return resp["result"]
    def tool(self, name, args):
        out = self.call("tools/call", {"name": name, "arguments": args})
        return json.loads(out["content"][0]["text"])
    def close(self): self.p.stdin.close(); self.p.wait(timeout=5)

def run(base=BASE, quiet=False):
    invoices = json.load(open(os.path.join(base, "invoices.json")))
    c = McpClient()
    tools = [t["name"] for t in c.call("tools/list")["tools"]]
    clean, exceptions, billed, seen = [], [], {}, []
    for inv in invoices:
        res = c.tool("validate_invoice", {"invoice": inv, "po_billed": billed, "seen_numbers": seen})
        seen.append(inv["invoice_no"])
        if res["valid"]:
            clean.append(inv); billed[inv["po_number"]] = billed.get(inv["po_number"], 0) + inv["subtotal"]
        else:
            exceptions.append({"invoice_no": inv["invoice_no"], "vendor": inv["vendor"], "total": inv["total"],
                               "reasons": res["reasons"]})
    c.close()
    # outputs
    by_vendor = {}
    for i in clean:
        v = by_vendor.setdefault(i["vendor"], {"count": 0, "total": 0}); v["count"] += 1; v["total"] += i["total"]
    summary = {"invoices_received": len(invoices), "clean": len(clean), "exceptions": len(exceptions),
               "clean_subtotal": sum(i["subtotal"] for i in clean), "clean_gst": sum(i["gst"] for i in clean),
               "clean_total_payable": sum(i["total"] for i in clean), "by_vendor": by_vendor,
               "clean_invoices": [i["invoice_no"] for i in clean], "mcp_tools_used": tools}
    json.dump(summary, open(os.path.join(base, "clean_summary.json"), "w"), indent=2)
    with open(os.path.join(base, "exceptions.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["invoice_no", "vendor", "total_inr", "reasons"])
        for e in exceptions: w.writerow([e["invoice_no"], e["vendor"], e["total"], " | ".join(e["reasons"])])
    if not quiet:
        print(f"MCP tools available: {tools}\n")
        print("== CLEAN INVOICES - SUMMARY ==")
        print(f"Received {summary['invoices_received']} | Clean {summary['clean']} | Exceptions {summary['exceptions']}")
        for i in clean: print(f"  {i['invoice_no']}  {i['vendor']:<15} PO {i['po_number']}  total INR {i['total']:>10,}")
        print(f"  Subtotal INR {summary['clean_subtotal']:,} + GST INR {summary['clean_gst']:,} = payable INR {summary['clean_total_payable']:,}")
        print("\n== EXCEPTION LIST (needs a human) ==")
        for e in exceptions:
            print(f"  {e['invoice_no']}  {e['vendor']}  total INR {e['total']:,}")
            for r in e["reasons"]: print(f"      - {r}")
    return summary, exceptions

if __name__ == "__main__":
    run()
