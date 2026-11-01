"""A public Gradio link (share=True) always asks for a login."""

import pytest

webapp = pytest.importorskip("matrag.webapp")


def test_shared_app_gets_a_login(monkeypatch, capsys):
    monkeypatch.delenv("MATRAG_APP_USER", raising=False)
    monkeypatch.delenv("MATRAG_APP_PASSWORD", raising=False)
    user, password = webapp.share_auth(True)
    assert user == "matrag" and len(password) >= 12
    assert password in capsys.readouterr().out  # printed once, for the person who started it
    assert webapp.share_auth(True)[1] != password  # a new one each launch


def test_login_from_the_environment_and_none_when_local(monkeypatch, capsys):
    monkeypatch.setenv("MATRAG_APP_USER", "amin")
    monkeypatch.setenv("MATRAG_APP_PASSWORD", "s3cret")
    assert webapp.share_auth(True) == ("amin", "s3cret")
    assert "s3cret" not in capsys.readouterr().out
    assert webapp.share_auth(False) is None
    assert webapp.share_auth(True, auth=("a", "b")) == ("a", "b")
