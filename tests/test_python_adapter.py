from code_maintenance import PythonAdapter, SourceFile, SymbolKind


SOURCE = '''\
def top(value):
    return value


class First:
    def __init__(self, value):
        self.value = value

    class Nested:
        def method(self):
            return 1


class Second:
    def __init__(self):
        self.ready = True
'''


def parse(source=SOURCE):
    return PythonAdapter().parse_symbols(SourceFile("project-1", "src/example.py", "python", source))


def test_maps_legacy_python_parser_results_to_qualified_symbols():
    symbols = parse()

    assert [(symbol.kind, symbol.qualified_name) for symbol in symbols] == [
        (SymbolKind.FUNCTION, "top"),
        (SymbolKind.CLASS, "First"),
        (SymbolKind.METHOD, "First.__init__"),
        (SymbolKind.CLASS, "First.Nested"),
        (SymbolKind.METHOD, "First.Nested.method"),
        (SymbolKind.CLASS, "Second"),
        (SymbolKind.METHOD, "Second.__init__"),
    ]


def test_same_named_methods_have_distinct_stable_ids():
    first, second = [symbol for symbol in parse() if symbol.name == "__init__"]

    assert first.id != second.id
    assert str(first.id) == "python:src/example.py:First.__init__:method"
    assert str(second.id) == "python:src/example.py:Second.__init__:method"


def test_body_change_updates_content_hash_without_changing_identity():
    original = parse()[0]
    changed = parse(SOURCE.replace("return value", "return value + 1"))[0]

    assert original.id == changed.id
    assert original.content_hash != changed.content_hash


def test_nested_functions_are_not_available_from_the_legacy_parser():
    source = '''\
def outer():
    def inner():
        return 1
    return inner()
'''

    assert [symbol.qualified_name for symbol in parse(source)] == ["outer"]
