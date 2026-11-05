"""Minimal agent loop. No framework. Tools -> loop while Claude asks for tools -> stop when done or 10 steps."""
import json, os, sys, datetime as dt

TODAY = dt.date(2026, 11, 5)
MAX_STEPS = 10

POS = [
 {"po":"PO-1001","supplier":"Acme Steel","due":"2026-10-20","status":"OPEN","amount":12400},
 {"po":"PO-1002","supplier":"Bolt & Co","due":"2026-11-12","status":"OPEN","amount":3100},
 {"po":"PO-1003","supplier":"Nova Plastics","due":"2026-10-30","status":"OPEN","amount":8750},
 {"po":"PO-1004","supplier":"Acme Steel","due":"2026-10-01","status":"RECEIVED","amount":5200},
 {"po":"PO-1005","supplier":"Zenith Metals","due":"2026-11-02","status":"OPEN","amount":19800},
]
CONTACTS = {"Acme Steel":"sales@acmesteel.example","Nova Plastics":"orders@novaplastics.example",
            "Zenith Metals":"ar@zenithmetals.example","Bolt & Co":"hello@boltco.example"}

# ---- tools -------------------------------------------------------------
def list_purchase_orders(): return POS
def get_supplier_contact(supplier): return {"supplier":supplier,"email":CONTACTS.get(supplier)}
def save_email_draft(to, subject, body):
    os.makedirs("drafts", exist_ok=True)
    fn = f"drafts/{subject.split()[0]}_{to.split('@')[0]}.txt"
    open(fn,"w").write(f"To: {to}\nSubject: {subject}\n\n{body}\n"); return {"saved":fn}
FUNCS = {"list_purchase_orders":list_purchase_orders,"get_supplier_contact":get_supplier_contact,"save_email_draft":save_email_draft}
TOOLS = [
 {"name":"list_purchase_orders","description":"List all purchase orders with due date and status.","input_schema":{"type":"object","properties":{}}},
 {"name":"get_supplier_contact","description":"Get supplier email.","input_schema":{"type":"object","properties":{"supplier":{"type":"string"}},"required":["supplier"]}},
 {"name":"save_email_draft","description":"Save an email draft.","input_schema":{"type":"object","properties":{"to":{"type":"string"},"subject":{"type":"string"},"body":{"type":"string"}},"required":["to","subject","body"]}},
]

# ---- model: real API, or offline stub with identical interface ----------
class B:  # tiny content-block stand-in
    def __init__(s, **k): s.__dict__.update(k)
class R:
    def __init__(s, stop, content): s.stop_reason, s.content = stop, content

def stub_model(messages):
    results = [b for m in messages if m["role"]=="user" and isinstance(m["content"],list) for b in m["content"]]
    n = len([m for m in messages if m["role"]=="assistant"])
    if n == 0:
        return R("tool_use",[B(type="text",text="I'll start by pulling all purchase orders."),
                 B(type="tool_use",id="t0",name="list_purchase_orders",input={})])
    pos = json.loads(results[0]["content"])
    late = [p for p in pos if p["status"]=="OPEN" and dt.date.fromisoformat(p["due"]) < TODAY]
    if n == 1:
        return R("tool_use",[B(type="text",text=f"{len(late)} POs are open and past due. Fetching supplier contacts."),
                 *[B(type="tool_use",id=f"c{i}",name="get_supplier_contact",input={"supplier":p["supplier"]}) for i,p in enumerate(late)]])
    if n == 2:
        contacts = {json.loads(r["content"])["supplier"]:json.loads(r["content"])["email"] for r in results[1:]}
        blocks=[B(type="text",text="Drafting a chase email for each late PO.")]
        for i,p in enumerate(late):
            d=(TODAY-dt.date.fromisoformat(p["due"])).days
            blocks.append(B(type="tool_use",id=f"d{i}",name="save_email_draft",input={
              "to":contacts[p["supplier"]],"subject":f"{p['po']} overdue by {d} days",
              "body":f"Hi {p['supplier']} team,\n\n{p['po']} (${p['amount']:,}) was due {p['due']} and is now {d} days late. "
                     f"Please confirm the ship date today.\n\nThanks,\nProcurement"}))
        return R("tool_use",blocks)
    return R("end_turn",[B(type="text",text=f"Done. Found {len(late)} late POs and saved {len(late)} drafts in ./drafts.")])

def call_model(messages):
    if os.getenv("ANTHROPIC_API_KEY") and "--offline" not in sys.argv:
        import anthropic
        return anthropic.Anthropic().messages.create(model="claude-sonnet-4-6",max_tokens=1500,tools=TOOLS,messages=messages,
            system=f"Today is {TODAY}. Find late open POs, then draft a chase email per late PO.")
    return stub_model(messages)

# ---- the loop ------------------------------------------------------------
def run(task):
    messages=[{"role":"user","content":task}]
    for step in range(1, MAX_STEPS+1):
        resp = call_model(messages)
        for b in resp.content:
            if b.type=="text": print(f"[step {step}] claude: {b.text}")
        if resp.stop_reason != "tool_use":
            print(f"[step {step}] stop: end_turn"); return
        messages.append({"role":"assistant","content":[
            {"type":"text","text":b.text} if b.type=="text" else {"type":"tool_use","id":b.id,"name":b.name,"input":b.input}
            for b in resp.content]})
        results=[]
        for b in resp.content:
            if b.type=="tool_use":
                print(f"[step {step}] tool  : {b.name}({json.dumps(b.input)[:70]})")
                results.append({"type":"tool_result","tool_use_id":b.id,"content":json.dumps(FUNCS[b.name](**b.input))})
        messages.append({"role":"user","content":results})
    print(f"[halt] reached {MAX_STEPS} steps")

if __name__=="__main__":
    run("Find the late POs and draft the emails.")
