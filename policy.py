import os
import re
import sys
from pathlib import Path

import anthropic

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("pypdf is not installed. Run: python -m pip install pypdf")

if hasattr(sys.stdout, "reconfigure"):  # avoid Unicode errors on Windows consoles
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
MODEL = "claude-haiku-5-5"
PDF_NAME = "HR_policy_doc.pdf"

STOP = set("""a an the of to in on for and or is are be do does can i my me you your
what how when who which with at by from it this that as if will many much get""".split())

SYSTEM_PROMPT = (
    "Answer ONLY from the policy text provided. Never use outside knowledge, "
    "even if you know the answer. "
    "After each fact, cite the section exactly like [Section 4]. "
    "If the answer is not in the text, reply exactly: Not in policy."
)

# Matches headings such as "4. Leave Policy" or "Section 4. Leave Policy"
HEADING_RE = re.compile(r"(?m)^[ \t]*(?:Section\s+)?(\d{1,2})\s*[.:)\-]\s+([^\n]+)$")


def find_policy_file():
    """Look for HR_policy_doc.pdf in the usual places."""
    candidates = []
    env_path = os.environ.get("HR_POLICY_FILE")
    if env_path:
        candidates.append(Path(env_path))
    candidates += [
        Path(__file__).resolve().parent / PDF_NAME,
        Path.cwd() / PDF_NAME,
        Path.home() / "Downloads" / PDF_NAME,
        Path.home() / "Desktop" / PDF_NAME,
        Path.home() / "Documents" / PDF_NAME,
    ]
    for p in candidates:
        if p.is_file():
            return p
    tried = "\n  ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        f"Could not find {PDF_NAME}. Put it next to this script, or set the "
        f"HR_POLICY_FILE environment variable. Looked in:\n  {tried}"
    )


def load_text(path=None):
    """Read all text from the PDF (or from a .txt file)."""
    path = Path(path) if path else find_policy_file()
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            reader.decrypt("")  # works for PDFs with an empty password
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    else:
        text = path.read_text(encoding="utf-8-sig")
    text = text.replace("\r", "").replace("\xa0", " ")
    if not text.strip():
        raise ValueError(
            f"No text found in {path}. It may be a scanned PDF (images only)."
        )
    return text


def words(text):
    """Lowercase keywords of a text, without stop words, with a crude plural fix."""
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP:
            continue
        if len(w) > 3 and w.endswith("s"):  # days -> day
            w = w[:-1]
        out.add(w)
    return out


def split_sections(path=None):
    """Split the policy into one chunk per numbered heading (1, 2, 3, ...)."""
    text = load_text(path)

    # Accept a heading only if its number is the next one in sequence.
    # This ignores stray numbered lines inside a section.
    matches = []
    expected = 1
    for m in HEADING_RE.finditer(text):
        if int(m.group(1)) == expected:
            matches.append(m)
            expected += 1

    sections = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append({
            "num": m.group(1),
            "title": m.group(2).strip(),
            "text": text[m.start():end].strip(),
        })

    if not sections:
        raise ValueError(
            "No numbered sections found. Headings must look like "
            "'1. Purpose and Scope' or 'Section 1. Purpose and Scope'."
        )
    return sections


def top3(question, sections):
    """Return the 3 sections that share the most keywords with the question."""
    q = words(question)
    scored = []
    for s in sections:
        score = len(q & words(s["text"])) + len(q & words(s["title"]))  # title counts double
        scored.append((score, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:3]]


def ask(question, chunks):
    """Send the chosen chunks and the question to Claude Haiku."""
    context = "\n\n".join(chunks)
    msg = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"POLICY:\n{context}\n\nQ: {question}"}],
    )
    return msg.content[0].text


def answer(question, sections):
    picked = top3(question, sections)
    text = ask(question, [s["text"] for s in picked])
    return text, [s["num"] for s in picked]


# (question, correct section, acceptable key facts separated by |)
# Use None as the section for questions that are NOT in the policy.
TESTS = [
    ("How long is the probation period?", "2", "six|6"),
    ("How many hours is the standard working day?", "3", "nine|9"),
    ("When is a medical certificate required for sick leave?", "4",
     "2 consecutive|two consecutive|more than 2|more than two"),
    ("How many days in advance must I apply for earned leave?", "4", "7 days|seven"),
    ("Can I do freelance SAP work on the side?", "5", "disclos|approv"),
    ("How quickly must I report a suspected data leak or loss of a device?", "6", "immediately"),
    ("What is the notice period for resignation after confirmation?", "11", "60|sixty"),
    ("Does the company provide a gym membership?", None, ""),
    ("How many days a week can I work from home?", None, ""),
    ("What is the monthly salary of an SAP ABAP Developer?", None, ""),
]


def run_tests():
    sections = split_sections()
    print(f"Loaded {len(sections)} sections.\n")
    passed = 0
    for i, (q, sec, facts) in enumerate(TESTS, 1):
        text, used = answer(q, sections)
        low = text.lower()
        if sec is None:
            ok = "not in policy" in low
        else:
            ok = (
                sec in used
                and f"section {sec}" in low
                and any(f in low for f in facts.split("|"))
            )
        passed += ok
        print(f"{i:>2}. {'PASS' if ok else 'FAIL'}  {q}")
        if not ok:
            print(f"      sections used: {used} | answer: {text}")
    print(f"\n{passed}/{len(TESTS)} passed")


def chat():
    sections = split_sections()
    print(f"Loaded {len(sections)} sections.")
    while True:
        q = input("\nQuestion (or 'quit'): ").strip()
        if q.lower() == "quit":
            break
        if not q:
            continue
        text, used = answer(q, sections)
        print(f"Sections used: {used}")
        print(text)


if __name__ == "__main__":
    # python policy.py        -> ask questions interactively
    # python policy.py test   -> run the 10 test questions
    if len(sys.argv) > 1 and sys.argv[1].lower() == "test":
        run_tests()
    else:
        chat()