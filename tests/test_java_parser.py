from Java.java_parser import get_defined_functions


SOURCE = '''\
public class First {
    public void run() {
    }

    public int add(int value) {
        return value;
    }

    public int add(int left, int right) {
        return left + right;
    }
}

class Second {
    void run() {
    }
}
'''


def test_extracts_classes_and_same_named_methods():
    items = get_defined_functions(SOURCE)

    assert [(item["type"], item["name"]) for item in items] == [
        ("class", "First"),
        ("method", "run"),
        ("method", "add"),
        ("method", "add"),
        ("class", "Second"),
        ("method", "run"),
    ]
    assert [item["lineno"] for item in items if item["name"] == "run"] == [2, 15]


def test_extracts_overloaded_methods_as_separate_items():
    items = get_defined_functions(SOURCE)
    overloads = [item for item in items if item["name"] == "add"]

    assert len(overloads) == 2
    assert "add(int value)" in overloads[0]["code"]
    assert "add(int left, int right)" in overloads[1]["code"]


def test_ignores_control_flow_and_braces_inside_strings_or_comments():
    source = '''\
class Example {
    void work() {
        if (true) { System.out.println("{ not a declaration }"); }
        // void ignored() {}
    }
}
'''

    assert [(item["type"], item["name"]) for item in get_defined_functions(source)] == [
        ("class", "Example"),
        ("method", "work"),
    ]
