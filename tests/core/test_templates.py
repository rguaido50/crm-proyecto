from pathlib import Path

import pytest

from crm.core.templates import _module_template_dirs


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

    with pytest.raises(RuntimeError, match="list.html"):
        _module_template_dirs(tmp_path)
