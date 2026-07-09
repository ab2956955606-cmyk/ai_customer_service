from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.models import KnowledgeDocument


SAMPLE_DOCS_DIR = Path(__file__).parent / "sample_docs"


def load_markdown_documents() -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    for path in sorted(SAMPLE_DOCS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        title = path.name
        first_line = content.splitlines()[0].strip() if content.splitlines() else ""
        if first_line.startswith("# "):
            title = first_line[2:].strip()
        documents.append({"title": title, "content": content, "source": path.name})
    return documents


def reindex_documents(db: Session) -> list[KnowledgeDocument]:
    existing = {doc.source: doc for doc in db.query(KnowledgeDocument).all()}
    indexed: list[KnowledgeDocument] = []
    for doc in load_markdown_documents():
        item = existing.get(doc["source"])
        if item is None:
            item = KnowledgeDocument(**doc)
            db.add(item)
        else:
            item.title = doc["title"]
            item.content = doc["content"]
        indexed.append(item)
    db.commit()
    for item in indexed:
        db.refresh(item)
    return indexed
