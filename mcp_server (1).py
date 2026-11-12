"""Minimal MCP server (stdio, newline-delimited JSON-RPC 2.0), standard library only.
Implements: initialize, notifications/initialized, tools/list, tools/call, ping.
Tool: validate_invoice(invoice, po_billed?, seen_numbers?)"""
import json, sys
import validator

TOOL = {
  "name": "validate_invoice",
  "description": "Validate one supplier invoice: required fields, duplicate number, GSTIN format, approved vendor, "
                 "line/GST/total arithmetic, date, and PO match with remaining balance. Returns valid + reasons.",
  "inputSchema": {"type": "object", "properties": {
      "invoice": {"type": "object"},
      "po_billed": {"type": "object", "description": "INR already invoiced per PO number"},
      "seen_numbers": {"type": "array", "items": {"type": "string"}}},
    "required": ["invoice"]}}

def reply(id_, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    msg.update({"error": error} if error else {"result": result})
    sys.stdout.write(json.dumps(msg) + "\n"); sys.stdout.flush()

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        req = json.loads(line); m = req.get("method"); id_ = req.get("id")
        if m == "initialize":
            reply(id_, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                        "serverInfo": {"name": "invoice-validator", "version": "1.0"}})
        elif m == "tools/list":
            reply(id_, {"tools": [TOOL]})
        elif m == "tools/call":
            p = req["params"]
            if p["name"] != "validate_invoice":
                reply(id_, error={"code": -32602, "message": "unknown tool"}); continue
            a = p["arguments"]
            res = validator.validate_invoice(a["invoice"], a.get("po_billed"), set(a.get("seen_numbers", [])))
            reply(id_, {"content": [{"type": "text", "text": json.dumps(res)}], "isError": False})
        elif m == "ping":
            reply(id_, {})
        elif id_ is not None:
            reply(id_, error={"code": -32601, "message": f"method not found: {m}"})
        # notifications (no id) get no reply

if __name__ == "__main__":
    main()
