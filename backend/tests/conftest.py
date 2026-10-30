import pytest

from app import crear_app
from infraestructura.persistencia.sql.modelos import db
from seed import poblar_datos


@pytest.fixture
def app(tmp_path, monkeypatch):
    """App real con una base SQLite temporal propia de cada test, ya sembrada."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    app = crear_app()
    app.config["TESTING"] = True
    with app.app_context():
        poblar_datos(db)
    return app


@pytest.fixture
def client(app):
    return app.test_client()
