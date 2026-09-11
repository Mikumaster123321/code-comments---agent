from code_maintenance import JavaAdapter, SourceFile, SymbolKind


SOURCE = '''\
class First {
    void run() {}
    int foo(int value) { return value; }
    String foo(String value) { return value; }
}

class Second {
    void run() {}
}
'''


def parse(source=SOURCE):
    return JavaAdapter().parse_symbols(SourceFile("project-1", "src/Example.java", "java", source))


def test_maps_legacy_java_parser_results_to_qualified_symbols():
    symbols = parse()

    assert [(symbol.kind, symbol.qualified_name) for symbol in symbols] == [
        (SymbolKind.CLASS, "First"),
        (SymbolKind.METHOD, "First.run"),
        (SymbolKind.METHOD, "First.foo"),
        (SymbolKind.METHOD, "First.foo"),
        (SymbolKind.CLASS, "Second"),
        (SymbolKind.METHOD, "Second.run"),
    ]


def test_java_overloads_use_normalized_parameter_signatures_in_ids():
    overloads = [symbol for symbol in parse() if symbol.qualified_name == "First.foo"]

    assert [symbol.signature for symbol in overloads] == ["foo(int)", "foo(String)"]
    assert overloads[0].id != overloads[1].id
    assert str(overloads[0].id).endswith(":foo(int)")
    assert str(overloads[1].id).endswith(":foo(String)")


def test_java_body_change_updates_content_hash_without_changing_identity():
    original = [symbol for symbol in parse() if symbol.qualified_name == "First.foo"][0]
    changed = [symbol for symbol in parse(SOURCE.replace("return value;", "return value + 1;", 1)) if symbol.qualified_name == "First.foo"][0]

    assert original.id == changed.id
    assert original.content_hash != changed.content_hash
