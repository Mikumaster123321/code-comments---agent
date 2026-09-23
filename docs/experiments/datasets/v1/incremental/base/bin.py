class Bin:
    def put(self, item):
        return [item]

    def remove(self, items, item):
        items.remove(item)
