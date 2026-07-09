from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    database_url = f"sqlite:///{tmp_path / 'supportops-test.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    from app.db import SessionLocal, configure_database, init_db
    from app.main import app
    from app.seed import seed_data

    configure_database(database_url)
    init_db(drop=True)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()

    with TestClient(app) as test_client:
        yield test_client
