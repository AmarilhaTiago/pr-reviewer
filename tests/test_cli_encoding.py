import io
import sys

from reviewer import cli


def test_output_streams_are_forced_to_utf8(monkeypatch):
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", stream)
    cli._force_utf8_output()
    sys.stdout.write("⛔ blocker")
    sys.stdout.flush()
    assert raw.getvalue().decode("utf-8") == "⛔ blocker"
