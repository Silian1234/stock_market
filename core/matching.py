from django.db import transaction
from django.db.models import F
from market.models import Order, Trade, Account, Holding, Stock
from decimal import Decimal


def get_counter_orders(order):
    filters = {
        'stock': order.stock,
        'order_type': 'sell' if order.order_type == 'buy' else 'buy',
        'order_mode': 'limit',
        'is_filled': False
    }

    qs = Order.objects.filter(**filters)

    if order.order_type == 'buy':
        qs = qs.order_by('price', 'created_at')  # покупатель хочет дешевле
    else:
        qs = qs.order_by('-price', 'created_at')  # продавец хочет дороже

    if order.order_mode == 'limit':
        if order.order_type == 'buy':
            qs = qs.filter(price__lte=order.price)
        else:
            qs = qs.filter(price__gte=order.price)

    return qs.select_for_update()


def get_or_create_holding(user, stock):
    holding, _ = Holding.objects.get_or_create(user=user, stock=stock)
    return holding


@transaction.atomic
def execute_order(order):
    if order.order_mode == 'market':
        # для MARKET цена будет определяться встречной заявкой
        order.price = order.stock.current_price

    counter_orders = get_counter_orders(order)

    for counter in counter_orders:
        if order.remaining_quantity == 0:
            break

        match_qty = min(order.remaining_quantity, counter.remaining_quantity)
        match_price = counter.price

        buyer = order.user if order.order_type == 'buy' else counter.user
        seller = counter.user if order.order_type == 'buy' else order.user

        # Обновляем деньги и активы
        total_price = match_price * match_qty

        buyer_account = Account.objects.select_for_update().get(user=buyer)
        seller_account = Account.objects.select_for_update().get(user=seller)

        buyer_holding = get_or_create_holding(buyer, order.stock)
        seller_holding = get_or_create_holding(seller, order.stock)

        if buyer_account.balance < total_price:
            continue  # недостаточно денег

        if seller_holding.quantity < match_qty:
            continue  # недостаточно акций

        # Перевод средств и акций
        buyer_account.balance -= total_price
        seller_account.balance += total_price

        buyer_holding.quantity += match_qty
        seller_holding.quantity -= match_qty

        buyer_account.save()
        seller_account.save()
        buyer_holding.save()
        seller_holding.save()

        # Обновляем заявки
        order.remaining_quantity -= match_qty
        counter.remaining_quantity -= match_qty

        if counter.remaining_quantity == 0:
            counter.is_filled = True
        counter.save()

        Trade.objects.create(
            stock=order.stock,
            buyer=buyer,
            seller=seller,
            price=match_price,
            quantity=match_qty
        )

    if order.remaining_quantity == 0:
        order.is_filled = True
    order.save()

    # Обновляем текущую цену акции
    last_trade = Trade.objects.filter(stock=order.stock).order_by('-created_at').first()
    if last_trade:
        Stock.objects.filter(id=order.stock.id).update(current_price=last_trade.price)