from types import SimpleNamespace
from typing import Any

import pytest

from wine_recommendation.parser import bootstrap


def test_loader_is_skipped_when_parser_is_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        bootstrap,
        "settings",
        SimpleNamespace(parser_enabled=True),
    )

    def unexpected_source(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("mock loader must be skipped")

    monkeypatch.setattr(bootstrap, "PerekrestokSource", unexpected_source)

    bootstrap.load_mock_catalog()


def test_loader_rejects_remote_source_when_parser_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        bootstrap,
        "settings",
        SimpleNamespace(
            parser_enabled=False,
            mock_json_data="https://example.com/catalogue.json",
        ),
    )

    with pytest.raises(SystemExit, match="requires a local path"):
        bootstrap.load_mock_catalog()
