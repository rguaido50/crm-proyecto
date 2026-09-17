from pathlib import Path

import pytest

from crm.core.templates import _module_template_dirs, currency


def test_module_template_dirs_finds_each_modules_templates_dir(tmp_path: Path) -> None:
    (tmp_path / "contacts" / "templates").mkdir(parents=True)
    (tmp_path / "opportunities" / "templates").mkdir(parents=True)

    dirs = _module_template_dirs(tmp_path)

    assert dirs == [tmp_path / "contacts" / "templates", tmp_path / "opportunities" / "templates"]


def test_module_template_dirs_raises_on_a_duplicate_template_name(tmp_path: Path) -> None:
    (tmp_path / "contacts" / "templates").mkdir(parents=True)
    (tmp_path / "contacts" / "templates" / "list.html").write_text("contacts")
    (tmp_path / "tasks" / "templates").mkdir(parents=True)
    (tmp_path / "tasks" / "templates" / "list.html").write_text("tasks")

    with pytest.raises(
        RuntimeError, match=r"pick whichever comes first\. Rename one of them\.$"
    ) as exc_info:
        _module_template_dirs(tmp_path)

    assert str(tmp_path / "contacts" / "templates") in str(exc_info.value)


def test_module_template_dirs_allows_differently_named_templates(tmp_path: Path) -> None:
    (tmp_path / "contacts" / "templates").mkdir(parents=True)
    (tmp_path / "contacts" / "templates" / "list.html").write_text("contacts")
    (tmp_path / "tasks" / "templates").mkdir(parents=True)
    (tmp_path / "tasks" / "templates" / "detail.html").write_text("tasks")

    dirs = _module_template_dirs(tmp_path)

    assert dirs == [tmp_path / "contacts" / "templates", tmp_path / "tasks" / "templates"]


def test_currency_renders_an_em_dash_for_none() -> None:
    assert currency(None) == "—"
