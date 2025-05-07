from .models import Order, Trade
from django.db import transaction

def process_order(order):
    if order.order_mode == 'market':
        match_market_order(order)
    elif order.order_mode == 'limit':
        match_limit_order(order)

@transaction.atomic
def match_market_order(order):
    counter_orders = Order.objects.filter(
        stock=order.stock,
        order_type='buy' if order.order_type == 'sell' else 'sell',
        order_mode='limit',
        is_filled=False
    ).order_by('-price' if order.order_type == 'sell' else 'price', 'created_at')

    execute_matches(order, counter_orders)

@transaction.atomic
def match_limit_order(order):
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

    execute_matches(order, counter_orders)

def execute_matches(order, counter_orders):
    for counter in counter_orders:
        if order.remaining_quantity == 0:
            break

        matched_qty = min(order.remaining_quantity, counter.remaining_quantity)
        matched_price = counter.price

        Trade.objects.create(
            stock=order.stock,
            seller=order.user if order.order_type == 'sell' else counter.user,
            buyer=counter.user if order.order_type == 'sell' else order.user,
            price=matched_price,
            quantity=matched_qty
        )

        order.remaining_quantity -= matched_qty
        counter.remaining_quantity -= matched_qty

        if counter.remaining_quantity == 0:
            counter.is_filled = True
        counter.save()

    if order.remaining_quantity == 0:
        order.is_filled = True
    order.save()
