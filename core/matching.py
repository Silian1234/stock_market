from .orderbook import OrderBook

class MatchingEngine:
    def __init__(self):
        self.order_books = {}

    def get_order_book(self, stock_symbol):
        if stock_symbol not in self.order_books:
            self.order_books[stock_symbol] = OrderBook()
        return self.order_books[stock_symbol]

    def match_orders(self, order):
        stock_symbol = order.stock.symbol
        order_book = self.get_order_book(stock_symbol)
        order_book.add_order(order)
        if order.side == "BUY":
            best_ask = order_book.get_best_ask()
            if best_ask and order.price >= best_ask.price:
                trade_price = best_ask.price
                trade_quantity = min(order.quantity, best_ask.quantity)
                print(f"Trade executed: BUY {trade_quantity} of {stock_symbol} at {trade_price}")
                order.quantity -= trade_quantity
                best_ask.quantity -= trade_quantity
                if order.quantity == 0:
                    print("Buy order fully filled")
                if best_ask.quantity == 0:
                    order_book.remove_order(best_ask)
                    print("Sell order fully filled")
        elif order.side == "SELL":
            best_bid = order_book.get_best_bid()
            if best_bid and order.price <= best_bid.price:
                trade_price = best_bid.price
                trade_quantity = min(order.quantity, best_bid.quantity)
                print(f"Trade executed: SELL {trade_quantity} of {stock_symbol} at {trade_price}")
                order.quantity -= trade_quantity
                best_bid.quantity -= trade_quantity
                if order.quantity == 0:
                    print("Sell order fully filled")
                if best_bid.quantity == 0:
                    order_book.remove_order(best_bid)
                    print("Buy order fully filled")
