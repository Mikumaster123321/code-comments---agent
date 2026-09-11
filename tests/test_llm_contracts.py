import llm_service


def test_clean_docstring_removes_triple_quote_wrapper():
    assert llm_service._clean_docstring('\"\"\"Summarize the value.\"\"\"') == "Summarize the value."


def test_clean_docstring_removes_markdown_fence_and_standalone_triple_quotes():
    raw = '```python\n\"\"\"\nSummarize the value.\n\"\"\"\n```'

    assert llm_service._clean_docstring(raw) == "Summarize the value."


def test_clean_javadoc_removes_wrapper_and_line_prefixes():
    raw = "/**\n * Summarize the value.\n * @param value input value\n */"

    assert llm_service._clean_javadoc(raw) == "Summarize the value.\n@param value input value"


def test_clean_javadoc_removes_markdown_fence():
    raw = "```java\nSummarize the value.\n```"

    assert llm_service._clean_javadoc(raw) == "Summarize the value."


def test_generate_docstring_uses_stubbed_llm_and_cleans_response(monkeypatch):
    monkeypatch.setattr(llm_service, "_call_llm_with_retry", lambda *args: '\"\"\"Generated text.\"\"\"')

    result = llm_service.generate_docstring({"type": "function", "name": "work", "code": "def work(): pass"})

    assert result == "Generated text."


def test_generate_javadoc_uses_stubbed_llm_and_cleans_response(monkeypatch):
    monkeypatch.setattr(llm_service, "_call_llm_with_retry", lambda *args: "/**\n * Generated text.\n */")

    result = llm_service.generate_javadoc({"type": "method", "name": "work", "code": "void work() {}"})

    assert result == "Generated text."
