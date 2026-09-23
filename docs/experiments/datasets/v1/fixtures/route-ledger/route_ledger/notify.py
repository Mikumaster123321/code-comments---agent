class RouteNotifier:
    def notify_closed(self, entry):
        if entry.status == "closed":
            return self.format_message(entry)
        return None

    def format_message(self, entry):
        return "Route " + entry.route_id + " is closed"
