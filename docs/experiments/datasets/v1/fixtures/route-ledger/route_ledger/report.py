class RouteReport:
    def count_open_stops(self, entries):
        return sum(entry.remaining_stops() for entry in entries
                   if entry.remaining_stops() > 0)

    def summarize(self, store):
        entries = store.load_all()
        return {"open_stops": self.count_open_stops(entries),
                "closed_routes": self.closed_count(entries)}

    def closed_count(self, entries):
        return sum(entry.status == "closed" for entry in entries)
