from dataclasses import dataclass, field
from route_ledger.models import RouteEntry, validate_entry
import route_ledger.store
import route_ledger.policy


@dataclass
class RouteService:
    store: object = field(default_factory=route_ledger.store.MemoryRouteStore)
    policy: object = field(default_factory=route_ledger.policy.StopPolicy)

    def open_route(self, route_id):
        return self.store.save(validate_entry(RouteEntry(route_id)))

    def add_stop(self, entry):
        entry.pending += 1
        return self.store.save(entry)

    def close_route(self, entry):
        if not self.policy.can_close(entry):
            raise ValueError("Remaining stops prevent closure")
        entry.mark_closed()
        return self.store.save(entry)

    def reopen(self, entry):
        entry.status = "open"
        return self.store.save(entry)
