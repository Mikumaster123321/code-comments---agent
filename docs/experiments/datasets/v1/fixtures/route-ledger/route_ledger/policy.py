class StopPolicy:
    def can_close(self, entry):
        return entry.remaining_stops() == 0

    def counts_as_open(self, entry):
        return entry.status not in {"closed", "skipped"}

    def allows_skip(self, entry):
        return entry.status == "open"
