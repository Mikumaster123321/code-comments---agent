from pathlib import Path

import pytest

import processor


@pytest.mark.xfail(
    reason="processor stores concurrent results by item name, so same-named methods overwrite each other",
    strict=True,
)
def test_same_named_methods_keep_their_own_generated_docstrings(monkeypatch):
    source = '''\
class First:
    def __init__(self):
        pass

class Second:
    def __init__(self):
        pass
'''
    monkeypatch.setattr(
        processor,
        "generate_docstring",
        lambda item, *_args: f"Generated for line {item['lineno']}",
    )

    annotated_code, _, _, markdown_path, source_path = processor.process_code(source)
    for path in (markdown_path, source_path):
        Path(path).unlink(missing_ok=True)

    assert "Generated for line 2" in annotated_code
    assert "Generated for line 6" in annotated_code
