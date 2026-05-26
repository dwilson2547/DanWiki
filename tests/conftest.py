import pytest
from app import create_app
from app.models import db as _db


@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    return app


@pytest.fixture(scope='session')
def app_context(app):
    with app.app_context():
        yield app
