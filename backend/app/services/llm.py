from __future__ import annotations
import logging
import time
from typing import List

from openai import OpenAI
from openai._exceptions import (
    APIStatusError,
    APIConnectionError,
    RateLimitError,
    OpenAIError,
)

from ..config import settings

log = logging.getLogger("llm")

# OpenRouter

_client: OpenAI | None = None


def _get_or_client() -> OpenAI:
    """OpenAI client configured to hit OpenRouter."""
    global _client
    if _client is None:
        headers = {}
        if getattr(settings, "OPENROUTER_SITE_URL", None):
            headers["HTTP-Referer"] = settings.OPENROUTER_SITE_URL
        if getattr(settings, "OPENROUTER_APP_NAME", None):
            headers["X-Title"] = settings.OPENROUTER_APP_NAME

        _client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            default_headers=headers or None,
        )
        log.info("[llm] OpenRouter chat client ready (model=%s)", settings.LLM_MODEL)
    return _client


def _retry(func, attempts=2, backoff=0.6):
    last = None
    for i in range(attempts):
        try:
            return func()
        except (RateLimitError, APIConnectionError) as e:
            last = e
            time.sleep(backoff * (2**i))
        except APIStatusError as e:
            last = e
            # retry on 429/5xx
            if 500 <= e.status_code < 600 or e.status_code == 429:
                time.sleep(backoff * (2**i))
            else:
                break
        except OpenAIError as e:
            last = e
            break
        except Exception as e:
            last = e
            break
    if last:
        raise last
    raise RuntimeError("unreachable")


def answer_with_llm(question: str, contexts: List[str]) -> str:
    """
    Calls OpenRouter /chat/completions via OpenAI SDK.
    If it errors, fall back to a short extract from the first context.
    """
    system = (
        "You are a helpful support agent. Answer using ONLY the provided context. "
        "If the answer isn't in the context, say you'll escalate to a specialist."
    )
    ctx_block = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts[:3]))
    user = f"Context:\n{ctx_block}\n\nQuestion: {question}\n\nAnswer succinctly."

    def _call():
        cli = _get_or_client()
        resp = cli.chat.completions.create(
            model=settings.LLM_MODEL,  #"meta-llama/llama-3.1-8b-instruct:free"
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()

    try:
        return _retry(_call, attempts=2, backoff=0.6)
    except Exception as e:
        log.warning("[answer_with_llm] OpenRouter error: %s: %s", type(e).__name__, e)
        return "Here’s what I found:\n\n" + (
            (contexts[0][:800] if contexts else "No context available.")
        )


# Local embeddings

_ST_MODEL = None


def _get_local_embedder():
    global _ST_MODEL
    if _ST_MODEL is None:
        log.info("[embeddings] loading sentence-transformers/all-MiniLM-L6-v2")
        from sentence_transformers import SentenceTransformer

        _ST_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _ST_MODEL


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Return 384-dim normalized embeddings using MiniLM.
    Make sure your DB uses vector(384).
    """
    try:
        model = _get_local_embedder()
        vecs = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return [v.tolist() for v in vecs]
    except Exception as e:
        log.exception("[embed_texts] local embeddings failed: %r", e)
        raise
