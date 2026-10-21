import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.store import FileConfigStore  # noqa: E402


@pytest.fixture()
def app(tmp_path):
    return create_app({"TESTING": True, "CONFIG_STORE": FileConfigStore(str(tmp_path / "configs"))})


@pytest.fixture()
def client(app):
    return app.test_client()
