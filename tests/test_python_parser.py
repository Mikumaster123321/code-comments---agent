import pytest

from Py.parser import get_defined_functions


SOURCE = '''\
def top_level(value):
    return value + 1


class First:
    def __init__(self, value):
        self.value = value

    def describe(self):
        return str(self.value)


class Second:
    def __init__(self):
        self.ready = True
'''


def test_extracts_top_level_function_classes_and_methods():
    items = get_defined_functions(SOURCE)

    assert [(item["type"], item["name"]) for item in items] == [
        ("function", "top_level"),
        ("class", "First"),
        ("function", "__init__"),
        ("function", "describe"),
        ("class", "Second"),
        ("function", "__init__"),
    ]
    assert items[0]["code"].startswith("def top_level")
    assert items[2]["code"].startswith("    def __init__")


def test_preserves_same_named_methods_from_different_classes():
    items = get_defined_functions(SOURCE)
    initializers = [item for item in items if item["name"] == "__init__"]

    assert len(initializers) == 2
    assert [item["lineno"] for item in initializers] == [6, 14]


def test_nested_function_and_function_local_class_are_currently_not_collected():
    source = '''\
def outer():
    def nested():
        return 1

    class Local:
        def method(self):
            return 2

    return nested()
'''

    items = get_defined_functions(source)

    assert [(item["type"], item["name"]) for item in items] == [("function", "outer")]


def test_invalid_python_is_reported_by_the_ast_parser():
    with pytest.raises(SyntaxError):
        get_defined_functions("def incomplete(:\n    pass\n")
