class OrderBook:
    def __init__(self):
        self.bids = []
        self.asks = []

    def add_order(self, order):
        if order.side == "BUY":
            self.bids.append(order)
            self.bids.sort(key=lambda x: x.price, reverse=True)
        elif order.side == "SELL":
            self.asks.append(order)
            self.asks.sort(key=lambda x: x.price)

    def remove_order(self, order):
        if order.side == "BUY":
            self.bids.remove(order)
        elif order.side == "SELL":
            self.asks.remove(order)

    def get_best_bid(self):
        return self.bids[0] if self.bids else None

    def get_best_ask(self):
        return self.asks[0] if self.asks else None

    def get_order_book(self):
        return {"bids": [(order.price, order.quantity) for order in self.bids],
                "asks": [(order.price, order.quantity) for order in self.asks]}
