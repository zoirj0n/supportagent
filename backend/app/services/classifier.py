from __future__ import annotations
import re
from typing import Optional


def classify_email(subject: str, body: str) -> str:
    s = f"{subject or ''} {body or ''}".lower()
    if any(k in s for k in ["refund", "return my money", "money back"]):
        return "refund"
    if any(k in s for k in ["how", "what", "when", "where", "why", "question", "help"]):
        return "question"
    return "other"


_ORD_RE = re.compile(r"\bORD[\s\-#]?(\d{4,10})\b", re.I)
_AFTER_LABEL_RE = re.compile(
    r"(?:order\s*(?:id|number|no\.?)\s*[:#]?\s*)(ORD[\s\-#]?\d{4,10}|\d{4,10})",
    re.I,
)
_QUOTE_START_RE = re.compile(
    r"^(On .+ wrote:|From:|Sent:|Subject:|To:|-----Original Message-----)",
    re.I,
)


def _strip_quoted_text(text: str) -> str:
    """
    Remove quoted sections so we don't read our own previous message
    (which may contain examples like 'e.g., ORD-34567').
    - Drops lines starting with '>'
    - Stops at 'On ... wrote:' or common forwarded headers
    - Stops at '-----Original Message-----'
    """
    if not text:
        return ""
    lines = text.splitlines()
    out = []
    for ln in lines:
        l = ln.lstrip()
        if l.startswith(">"):
            continue
        if _QUOTE_START_RE.match(l):
            break  # everything after is quoted
        out.append(ln)
    return "\n".join(out)


def _remove_example_spans(text: str) -> str:
    """
    Remove/neutralize example phrases that often carry fake IDs (e.g., 'e.g., ORD-34567').
    """
    return re.sub(
        r"\b(?:e\.g\.|eg|for example|such as)\b[^.\n]*",
        " ",
        text,
        flags=re.I,
    )


def extract_order_id(raw_text: str) -> Optional[str]:
    """
    Extracts an order id like ORD-12345 from the *new* user content only.
    Ignores quoted history and example snippets.
    """
    s = _strip_quoted_text(raw_text or "")
    s = _remove_example_spans(s)

    m = _ORD_RE.search(s)
    if m:
        return f"ORD-{m.group(1)}"
    m2 = _AFTER_LABEL_RE.search(s)
    if m2:
        digits = re.search(r"\d{4,10}", m2.group(1)).group(0)
        return f"ORD-{digits}"

    return None
