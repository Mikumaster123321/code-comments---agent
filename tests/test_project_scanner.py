from hashlib import sha256

import pytest

from code_maintenance import ProjectScanner


def test_scans_project_structure_languages_metadata_and_hashes(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "assets").mkdir()
    (tmp_path / "empty").mkdir()
    python_content = b"print('hello')\n"
    java_content = b"class App {}\n"
    binary_content = b"\x00\x01\x02"
    (tmp_path / "src" / "main.py").write_bytes(python_content)
    (tmp_path / "src" / "App.java").write_bytes(java_content)
    (tmp_path / "assets" / "data.bin").write_bytes(binary_content)

    result = ProjectScanner().scan(tmp_path)

    assert result.project.name == tmp_path.name
    assert result.project.root_path == str(tmp_path.resolve())
    assert len(result.project.id) == 64
    assert [directory.relative_path for directory in result.directories] == [
        ".",
        "assets",
        "empty",
        "src",
    ]
    assert [file.relative_path for file in result.files] == [
        "assets/data.bin",
        "src/App.java",
        "src/main.py",
    ]
    assert [file.language for file in result.files] == ["unknown", "java", "python"]
    assert result.metadata.directory_count == 4
    assert result.metadata.file_count == 3
    assert result.metadata.total_bytes == sum(map(len, (python_content, java_content, binary_content)))
    assert result.metadata.language_counts == (
        ("java", 1),
        ("python", 1),
        ("unknown", 1),
    )
    python_file = next(file for file in result.files if file.language == "python")
    assert python_file.content_hash == sha256(python_content).hexdigest()
    assert python_file.modified_time_ns > 0
    assert len(result.content_hash) == 64


def test_applies_default_gitignore_custom_and_negated_rules(tmp_path):
    (tmp_path / ".gitignore").write_text(
        "build/\n*.log\n!keep.log\n",
        encoding="utf-8",
    )
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "ignored.py").write_text("ignored = True\n", encoding="utf-8")
    (tmp_path / "generated").mkdir()
    (tmp_path / "generated" / "ignored.java").write_text("class Ignored {}\n", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "ignored.pyc").write_bytes(b"ignored")
    (tmp_path / "debug.log").write_text("ignored\n", encoding="utf-8")
    (tmp_path / "keep.log").write_text("kept\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("ready = True\n", encoding="utf-8")

    result = ProjectScanner(ignore_rules=("generated/",)).scan(tmp_path)
    paths = [file.relative_path for file in result.files]

    assert paths == [".gitignore", "keep.log", "main.py"]
    assert "build/" in result.ignore_rules
    assert "*.log" in result.ignore_rules
    assert "!keep.log" in result.ignore_rules
    assert "generated/" in result.ignore_rules
    assert "__pycache__/" in result.ignore_rules


def test_project_hash_is_deterministic_and_tracks_visible_content(tmp_path):
    visible = tmp_path / "main.py"
    ignored = tmp_path / "ignored.txt"
    visible.write_text("value = 1\n", encoding="utf-8")
    ignored.write_text("first\n", encoding="utf-8")
    scanner = ProjectScanner(ignore_rules=("ignored.txt",))

    first = scanner.scan(tmp_path)
    second = scanner.scan(tmp_path)
    ignored.write_text("second\n", encoding="utf-8")
    ignored_change = scanner.scan(tmp_path)
    visible.write_text("value = 2\n", encoding="utf-8")
    visible_change = scanner.scan(tmp_path)

    assert first.content_hash == second.content_hash
    assert first.content_hash == ignored_change.content_hash
    assert first.content_hash != visible_change.content_hash


def test_project_hash_tracks_empty_directory_changes(tmp_path):
    first = ProjectScanner().scan(tmp_path)
    (tmp_path / "empty").mkdir()
    second = ProjectScanner().scan(tmp_path)

    assert first.content_hash != second.content_hash


def test_rejects_missing_root_and_file_root(tmp_path):
    file_path = tmp_path / "main.py"
    file_path.write_text("value = 1\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        ProjectScanner().scan(tmp_path / "missing")
    with pytest.raises(NotADirectoryError):
        ProjectScanner().scan(file_path)
