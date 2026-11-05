"""Agent loop, no framework. Read-only tools + human y/n gate on send_email. Max 10 steps. Everything audited."""
import json, os, sys, datetime as dt

TODAY, MAX_STEPS, AUDIT = dt.date(2026,11,5), 10, "audit.jsonl"
POS = [
 {"po":"PO-1001","supplier":"Acme Steel","due":"2026-10-20","status":"OPEN","amount":12400},
 {"po":"PO-1002","supplier":"Bolt & Co","due":"2026-11-12","status":"OPEN","amount":3100},
 {"po":"PO-1003","supplier":"Nova Plastics","due":"2026-10-30","status":"OPEN","amount":8750},
 {"po":"PO-1004","supplier":"Acme Steel","due":"2026-10-01","status":"RECEIVED","amount":5200},
 {"po":"PO-1005","supplier":"Zenith Metals","due":"2026-11-02","status":"OPEN","amount":19800}]
CONTACTS = {"Acme Steel":"sales@acmesteel.example","Nova Plastics":"orders@novaplastics.example",
            "Zenith Metals":"ar@zenithmetals.example","Bolt & Co":"hello@boltco.example"}

def audit(**rec):                      # append-only, flushed per call
    rec = {"ts": dt.datetime.now().isoformat(timespec="seconds"), **rec}
    with open(AUDIT,"a") as f: f.write(json.dumps(rec)+"\n")

# ---- read-only tools ----
def list_purchase_orders(): return POS
def get_supplier_contact(supplier): return {"supplier":supplier,"email":CONTACTS.get(supplier)}
# ---- the only side-effect tool: gated ----
def send_email(to, subject, body):
    print(f"\n   ┌ SEND EMAIL? to={to}\n   │ subject: {subject}\n   └ {body.splitlines()[2][:70]}...")
    print("   approve [y/n]: ", end="", flush=True)
    ans = sys.stdin.readline().strip().lower(); print(ans or "(empty)")
    if ans != "y": return {"error":"REFUSED by human","sent":False}, "refused"
    return {"sent":True,"note":"simulated send"}, "approved"

FUNCS = {"list_purchase_orders":list_purchase_orders,"get_supplier_contact":get_supplier_contact,"send_email":send_email}
TOOLS = [
 {"name":"list_purchase_orders","description":"Read-only. List POs.","input_schema":{"type":"object","properties":{}}},
 {"name":"get_supplier_contact","description":"Read-only. Supplier email.","input_schema":{"type":"object","properties":{"supplier":{"type":"string"}},"required":["supplier"]}},
 {"name":"send_email","description":"Send email. Requires human approval; may be refused.","input_schema":{"type":"object","properties":{"to":{"type":"string"},"subject":{"type":"string"},"body":{"type":"string"}},"required":["to","subject","body"]}}]

class B:
    def __init__(s, **k): s.__dict__.update(k)
class R:
    def __init__(s, stop, content): s.stop_reason, s.content = stop, content

def stub_model(messages):              # offline stand-in, same interface as the SDK response
    res = [b for m in messages if m["role"]=="user" and isinstance(m["content"],list) for b in m["content"]]
    n = len([m for m in messages if m["role"]=="assistant"])
    if n==0: return R("tool_use",[B(type="text",text="Pulling all purchase orders."),B(type="tool_use",id="t0",name="list_purchase_orders",input={})])
    pos=json.loads(res[0]["content"]); late=[p for p in pos if p["status"]=="OPEN" and dt.date.fromisoformat(p["due"])<TODAY]
    if n==1: return R("tool_use",[B(type="text",text=f"{len(late)} late POs. Getting contacts."),
        *[B(type="tool_use",id=f"c{i}",name="get_supplier_contact",input={"supplier":p["supplier"]}) for i,p in enumerate(late)]])
    if n==2:
        em={json.loads(r["content"])["supplier"]:json.loads(r["content"])["email"] for r in res[1:]}
        bl=[B(type="text",text="Proposing a chase email per late PO (needs human approval).")]
        for i,p in enumerate(late):
            d=(TODAY-dt.date.fromisoformat(p["due"])).days
            bl.append(B(type="tool_use",id=f"s{i}",name="send_email",input={"to":em[p["supplier"]],"subject":f"{p['po']} overdue by {d} days",
              "body":f"Hi {p['supplier']} team,\n\n{p['po']} (${p['amount']:,}) was due {p['due']}, now {d} days late. Please confirm ship date.\n\nProcurement"}))
        return R("tool_use",bl)
    sent=sum('"sent": true' in r["content"] for r in res if "sent" in r["content"]); ref=sum("REFUSED" in r["content"] for r in res)
    return R("end_turn",[B(type="text",text=f"Done. {sent} email(s) sent, {ref} refused by human.")])

def call_model(messages):
    if os.getenv("ANTHROPIC_API_KEY") and "--offline" not in sys.argv:
        import anthropic
        return anthropic.Anthropic().messages.create(model="claude-sonnet-4-6",max_tokens=1500,tools=TOOLS,messages=messages,
            system=f"Today is {TODAY}. Find late open POs and email suppliers. If an email is refused, do not retry.")
    return stub_model(messages)

def run(task):
    messages=[{"role":"user","content":task}]
    for step in range(1,MAX_STEPS+1):
        resp=call_model(messages)
        for b in resp.content:
            if b.type=="text": print(f"[step {step}] claude: {b.text}")
        if resp.stop_reason!="tool_use": print(f"[step {step}] stop: end_turn"); return
        messages.append({"role":"assistant","content":[{"type":"text","text":b.text} if b.type=="text" else
            {"type":"tool_use","id":b.id,"name":b.name,"input":b.input} for b in resp.content]})
        results=[]
        for b in resp.content:
            if b.type!="tool_use": continue
            print(f"[step {step}] tool  : {b.name}")
            try:
                out=FUNCS[b.name](**b.input); decision="auto"
                if b.name=="send_email": out,decision=out
            except Exception as e: out,decision={"error":str(e)},"error"
            audit(step=step,tool=b.name,input=b.input,decision=decision,result=out)
            results.append({"type":"tool_result","tool_use_id":b.id,"content":json.dumps(out)})
        messages.append({"role":"user","content":results})
    print(f"[halt] reached {MAX_STEPS} steps"); audit(step=MAX_STEPS,tool="-",decision="halt",result="max steps")

if __name__=="__main__": run("Find the late POs and email the suppliers.")
