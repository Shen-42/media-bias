from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parent.parent / "app" / "streamlit_app.py"


def test_dashboard_renders_without_errors():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    assert any("Bike lanes and transit" in t.label for t in at.tabs)
