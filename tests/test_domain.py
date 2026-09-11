from code_maintenance import AnalysisFinding, Project, SourceFile, SymbolId, SymbolKind


def test_source_file_normalizes_relative_path_and_hashes_content():
    source_file = SourceFile("project-1", "src\\example.py", "python", "print('one')\n")

    assert source_file.relative_path == "src/example.py"
    assert source_file.content_hash == SourceFile("project-1", "src/example.py", "python", "print('one')\n").content_hash


def test_source_file_hash_changes_with_content():
    first = SourceFile("project-1", "example.py", "python", "print('one')\n")
    second = SourceFile("project-1", "example.py", "python", "print('two')\n")

    assert first.content_hash != second.content_hash


def test_symbol_id_is_deterministic_and_uses_semantic_identity_only():
    first = SymbolId("python", "example.py", "Service.run", SymbolKind.METHOD)
    second = SymbolId("python", "example.py", "Service.run", SymbolKind.METHOD)

    assert first == second
    assert str(first) == "python:example.py:Service.run:method"


def test_symbol_id_distinguishes_same_name_in_different_scopes():
    first = SymbolId("python", "example.py", "First.__init__", SymbolKind.METHOD)
    second = SymbolId("python", "example.py", "Second.__init__", SymbolKind.METHOD)

    assert first != second


def test_symbol_id_normalizes_windows_and_unix_path_separators():
    windows = SymbolId("python", "src\\a.py", "run", SymbolKind.FUNCTION)
    unix = SymbolId("python", "src/a.py", "run", SymbolKind.FUNCTION)

    assert windows == unix
    assert windows.relative_path == "src/a.py"
    assert hash(windows) == hash(unix)


def test_project_and_analysis_finding_remain_minimal_data_objects():
    project = Project("project-1", "Example", "/tmp/example")
    finding = AnalysisFinding("E501", "line too long", "warning", "example.py", 4)

    assert project.name == "Example"
    assert finding.symbol_id is None
