def score_importance(text: str) -> str:
    t = (text or "").strip()
    if len(t) < 20:
        return "low"
    if any(k in t.lower() for k in ["urgent", "asap", "immediately", "important"]):
        return "high"
    return "medium"
