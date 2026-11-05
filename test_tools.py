"""Manual test of each tool - run: python test_tools.py"""
from tools import list_open_pos, get_po_status, draft_email, send_email

print("1) list_open_pos()")
for p in list_open_pos():
    print("  ", p)

print("\n2) get_po_status")
for n in ["4500012", "4500013", "4500014", "4500015", "9999999"]:
    print("  ", n, "->", get_po_status(n))

print("\n3) draft_email")
d = draft_email("Sharma Steels", "PO 4500012 was due 10 Oct. 40 units pending. Please confirm delivery date.")
print("  ", d)
print("   empty text ->", draft_email("Sharma Steels", ""))

print("\n4) send_email")
print("  ", send_email(d["draft_id"]))
print("   bad id ->", send_email("D-nope"))
