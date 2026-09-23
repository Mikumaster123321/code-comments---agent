from route_ledger.models import RouteEntry
from route_ledger.report import RouteReport


def test_closed_route_is_not_open():
    entry = RouteEntry("harbor", pending=2)
    entry.mark_closed()
    assert RouteReport().count_open_stops([entry]) == 0


def test_skipped_stop_is_not_open():
    entry = RouteEntry("garden", pending=1, status="skipped")
    assert RouteReport().count_open_stops([entry]) == 0
