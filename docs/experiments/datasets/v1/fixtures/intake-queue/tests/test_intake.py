from intake_queue.parser import IntakeParser


def test_last_line_without_newline_is_kept():
    assert IntakeParser().normalize_payload("first\nlast") == "first\nlast"
