from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.agents.policy import (
    ADDRESS_CHANGE_TERMS,
    CANCEL_ORDER_TERMS,
    COMPLAINT_TERMS,
    DOWNGRADE_TERMS,
    FRAUD_TERMS,
    INVOICE_TERMS,
    PASSWORD_TERMS,
    REFUND_TERMS,
    SECURITY_TERMS,
    SETUP_TERMS,
    SHIPPING_TERMS,
    SUBSCRIPTION_TERMS,
    contains_any,
    detect_locale,
)
from app.models import KnowledgeDocument
from app.rag.indexer import reindex_documents


TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]+")

QUERY_EXPANSIONS = (
    (PASSWORD_TERMS, "password reset login sign in email link account"),
    (REFUND_TERMS, "refund money back duplicate charge purchase order billing payment"),
    (
        SHIPPING_TERMS | ADDRESS_CHANGE_TERMS | CANCEL_ORDER_TERMS,
        "shipping shipment address delivery tracking late order package cancel",
    ),
    (SUBSCRIPTION_TERMS | DOWNGRADE_TERMS, "subscription cancellation downgrade plan renewal account settings"),
    (INVOICE_TERMS, "invoice receipt tax VAT billing history payment record"),
    (FRAUD_TERMS | SECURITY_TERMS, "fraud unauthorized charge hacked account takeover legal police emergency"),
    (SETUP_TERMS, "product setup configure install onboarding workspace team support steps"),
    (COMPLAINT_TERMS, "service complaint delayed support recovery apology response policy"),
)


@dataclass
class RetrievedDocument:
    title: str
    snippet: str
    score: float


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def expand_query(question: str) -> str:
    expansions = [keywords for terms, keywords in QUERY_EXPANSIONS if contains_any(question, terms)]
    return " ".join([question, *expansions])


def _best_snippet(content: str, query_terms: set[str], max_len: int = 220) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
    if not lines:
        return content[:max_len]
    ranked = sorted(
        lines,
        key=lambda line: sum(1 for token in tokenize(line) if token in query_terms),
        reverse=True,
    )
    snippet = ranked[0]
    if len(snippet) > max_len:
        return snippet[: max_len - 3] + "..."
    return snippet


def _score(query_tokens: list[str], doc_tokens: list[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    query_counts = Counter(query_tokens)
    doc_counts = Counter(doc_tokens)
    dot = sum(query_counts[t] * doc_counts.get(t, 0) for t in query_counts)
    query_norm = math.sqrt(sum(v * v for v in query_counts.values()))
    doc_norm = math.sqrt(sum(v * v for v in doc_counts.values()))
    cosine = dot / (query_norm * doc_norm) if query_norm and doc_norm else 0.0
    overlap = len(set(query_tokens) & set(doc_tokens)) / max(len(set(query_tokens)), 1)
    return round((0.7 * cosine) + (0.3 * overlap), 4)


def retrieve(db: Session, question: str, limit: int = 3) -> list[dict]:
    if db.query(KnowledgeDocument).count() == 0:
        reindex_documents(db)

    query_tokens = tokenize(expand_query(question))
    query_terms = set(query_tokens)
    scored: list[RetrievedDocument] = []
    for doc in db.query(KnowledgeDocument).all():
        content = f"{doc.title}\n{doc.content}"
        score = _score(query_tokens, tokenize(content))
        if score > 0:
            scored.append(
                RetrievedDocument(
                    title=doc.source,
                    snippet=_best_snippet(doc.content, query_terms),
                    score=score,
                )
            )
    scored.sort(key=lambda item: item.score, reverse=True)
    return [item.__dict__ for item in scored[:limit]]


def answer_question(db: Session, question: str) -> dict:
    citations = retrieve(db, question, limit=3)
    locale = detect_locale(question)
    if not citations:
        return {
            "answer": (
                "暂未找到匹配度足够高的政策，请补充更多信息或转交人工客服专员处理。"
                if locale == "zh"
                else "I could not find a strong policy match. Please add more context or route this to a human specialist."
            ),
            "citations": [],
        }
    titles = ", ".join(citation["title"] for citation in citations)
    answer = (
        f"根据知识库，请遵循匹配的客服政策，并确保所有高风险变更经过审批。参考来源：{titles}。"
        if locale == "zh"
        else "Based on the knowledge base, follow the matching support policy and keep risky "
        f"changes behind approval. Relevant sources: {titles}."
    )
    return {"answer": answer, "citations": citations}
