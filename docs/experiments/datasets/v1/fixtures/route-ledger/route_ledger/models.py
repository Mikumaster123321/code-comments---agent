from dataclasses import dataclass


@dataclass
class RouteStatus:
    value: str = "open"

    def label(self):
        return self.value


@dataclass
class RouteEntry:
    route_id: str
    pending: int = 0
    status: str = "open"

    def remaining_stops(self):
        return self.pending

    def mark_closed(self):
        self.status = "closed"


def validate_entry(entry):
    if not entry.route_id:
        raise ValueError("A route needs an identifier")
    return entry
