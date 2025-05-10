from decimal import Decimal
from django.db import transaction
from market.models import Order, Trade, Holding, Account

def execute_order(order):
    if order.order_mode == 'market':
        match_market_order(order)
    elif order.order_mode == 'limit':
        match_limit_order(order)

def match_market_order(order):
    # Получаем противоположные лимитные заявки
    counter_orders = Order.objects.filter(
        stock=order.stock,
        order_type='buy' if order.order_type == 'sell' else 'sell',
        order_mode='limit',
        is_filled=False
    ).order_by('-price' if order.order_type == 'sell' else 'price', 'created_at')

    _execute_matches(order, counter_orders)

def match_limit_order(order):
    # Получаем подходящие противоположные лимитные заявки
    counter_orders = Order.objects.filter(
        stock=order.stock,
        order_type='buy' if order.order_type == 'sell' else 'sell',
        order_mode='limit',
        is_filled=False
    ).order_by('-price' if order.order_type == 'sell' else 'price', 'created_at')

    if order.order_type == 'sell':
        counter_orders = counter_orders.filter(price__gte=order.price)
    else:
        counter_orders = counter_orders.filter(price__lte=order.price)

    _execute_matches(order, counter_orders)

@transaction.atomic
def _execute_matches(order, counter_orders):
    for counter in counter_orders:
        if order.remaining_quantity == 0:
            break

        qty = min(order.remaining_quantity, counter.remaining_quantity)
        trade_price = counter.price

        # Обновление холдингов
        buyer, seller = (order.user, counter.user) if order.order_type == 'buy' else (counter.user, order.user)
        buyer_account = Account.objects.select_for_update().get(user=buyer, currency='USD')
        seller_account = Account.objects.select_for_update().get(user=seller, currency='USD')

        total_cost = Decimal(qty) * trade_price

        if buyer_account.balance < total_cost:
            continue  # пропускаем, если у покупателя нет средств

        # списание/зачисление денег
        buyer_account.balance -= total_cost
        seller_account.balance += total_cost
        buyer_account.save()
        seller_account.save()

        # обновление холдингов
        buyer_holding, _ = Holding.objects.get_or_create(user=buyer, stock=order.stock)
        seller_holding, _ = Holding.objects.get_or_create(user=seller, stock=order.stock)

        if seller_holding.quantity < qty:
            continue  # пропускаем, если у продавца нет акций

        buyer_holding.quantity += qty
        seller_holding.quantity -= qty
        buyer_holding.save()
        seller_holding.save()

        # создание сделки
        Trade.objects.create(
            stock=order.stock,
            buyer=buyer,
            seller=seller,
            quantity=qty,
            price=trade_price
        )

        order.remaining_quantity -= qty
        counter.remaining_quantity -= qty

        if counter.remaining_quantity == 0:
            counter.is_filled = True
        counter.save()

    if order.remaining_quantity == 0:
        order.is_filled = True
    order.save()
