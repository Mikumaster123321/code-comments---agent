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


def test_single_line_java_class_overloads_keep_scope_and_distinct_ids():
    source = "class A { int foo(int x){ return x; } String foo(String s){ return s; } }"

    overloads = [symbol for symbol in parse(source) if symbol.name == "foo"]

    assert [symbol.kind for symbol in overloads] == [SymbolKind.METHOD, SymbolKind.METHOD]
    assert [symbol.qualified_name for symbol in overloads] == ["A.foo", "A.foo"]
    assert [symbol.signature for symbol in overloads] == ["foo(int)", "foo(String)"]
    assert overloads[0].id != overloads[1].id
    assert all(symbol.id.fallback_line is None for symbol in overloads)


def test_final_parameter_modifier_does_not_change_identity():
    plain = parse("class A { void foo(int x) {} }")[1]
    modified = parse("class A { void foo(final int x) {} }")[1]

    assert plain.signature == modified.signature == "foo(int)"
    assert plain.id == modified.id


def test_array_whitespace_does_not_change_identity():
    compact = parse("class A { void foo(int[] x) {} }")[1]
    spaced = parse("class A { void foo(int [] x) {} }")[1]

    assert compact.signature == spaced.signature == "foo(int[])"
    assert compact.id == spaced.id


def test_varargs_whitespace_does_not_change_identity():
    compact = parse("class A { void foo(String... args) {} }")[1]
    spaced = parse("class A { void foo(String ... args) {} }")[1]

    assert compact.signature == spaced.signature == "foo(String...)"
    assert compact.id == spaced.id


def test_generic_whitespace_does_not_change_identity():
    compact = parse("class A { void foo(List<String> values) {} }")[1]
    spaced = parse("class A { void foo(List <String> values) {} }")[1]

    assert compact.signature == spaced.signature == "foo(List<String>)"
    assert compact.id == spaced.id


def test_nested_generic_commas_do_not_split_parameters():
    method = parse(
        "class A { void foo(Map<String, List<Integer>> data, int count) {} }"
    )[1]

    assert method.signature == "foo(Map<String,List<Integer>>,int)"
    assert method.id.semantic_disambiguator == method.signature


def test_unique_symbol_does_not_use_fallback_line():
    method = parse("class A { void foo(int x) {} }")[1]

    assert method.id.fallback_line is None


def test_fallback_line_is_only_added_for_semantic_identity_collision():
    source = '''\
class A {
    void foo(int x) {}
    void foo(int y) {}
}
'''
    overloads = [symbol for symbol in parse(source) if symbol.name == "foo"]

    assert [symbol.signature for symbol in overloads] == ["foo(int)", "foo(int)"]
    assert [symbol.id.fallback_line for symbol in overloads] == [2, 3]
    assert overloads[0].id != overloads[1].id
