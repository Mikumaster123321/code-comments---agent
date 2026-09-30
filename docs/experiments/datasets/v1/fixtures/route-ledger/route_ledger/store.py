from dataclasses import dataclass, field


@dataclass
class MemoryRouteStore:
    entries: dict = field(default_factory=dict)

    def save(self, entry):
        self.entries[entry.route_id] = entry
        return entry

    def load_all(self):
        return tuple(self.entries.values())

    def delete(self, route_id):
        return self.entries.pop(route_id, None)
