import json
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse

from .models import Item, Transaction, TransactionItem


def pos(request):
    """Point of sale view – grid of items, cart in session."""
    items = Item.objects.filter(is_available=True)
    cart = request.session.get('cart', {})

    cart_items = []
    total = Decimal('0.00')
    for item_id, qty in cart.items():
        try:
            item = Item.objects.get(pk=item_id)
            subtotal = item.price * qty
            total += subtotal
            cart_items.append({'item': item, 'qty': qty, 'subtotal': subtotal})
        except Item.DoesNotExist:
            pass

    return render(request, 'store/pos.html', {
        'items': items,
        'cart_items': cart_items,
        'total': total,
    })


@require_GET
def till(request):
    return render(request, 'store/till.html')


@require_POST
def add_to_cart(request, item_id):
    """Add an item to the session cart."""
    try:
        item = Item.objects.get(pk=item_id, is_available=True)
    except Item.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)

    cart = request.session.get('cart', {})
    key = str(item_id)
    cart[key] = cart.get(key, 0) + 1
    request.session['cart'] = cart
    request.session.modified = True

    total = Decimal('0.00')
    for iid, qty in cart.items():
        try:
            it = Item.objects.get(pk=iid)
            total += it.price * qty
        except Item.DoesNotExist:
            pass

    return JsonResponse({
        'cart_count': sum(cart.values()),
        'total': str(total),
        'item_qty': cart[key],
    })


@require_POST
def remove_from_cart(request, item_id):
    """Remove one unit of an item from the session cart."""
    cart = request.session.get('cart', {})
    key = str(item_id)
    if key in cart:
        cart[key] -= 1
        if cart[key] <= 0:
            del cart[key]
    request.session['cart'] = cart
    request.session.modified = True

    total = Decimal('0.00')
    for iid, qty in cart.items():
        try:
            it = Item.objects.get(pk=iid)
            total += it.price * qty
        except Item.DoesNotExist:
            pass

    return JsonResponse({
        'cart_count': sum(cart.values()),
        'total': str(total),
        'item_qty': cart.get(key, 0),
    })


@require_POST
def clear_cart(request):
    """Empty the cart."""
    request.session['cart'] = {}
    request.session.modified = True
    return redirect('pos')


def checkout(request):
    """Show the cart total and accept the payment amount."""
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('pos')

    cart_items = []
    total = Decimal('0.00')
    for item_id, qty in cart.items():
        try:
            item = Item.objects.get(pk=item_id)
            subtotal = item.price * qty
            total += subtotal
            cart_items.append({'item': item, 'qty': qty, 'subtotal': subtotal})
        except Item.DoesNotExist:
            pass

    error = None
    if request.method == 'POST':
        try:
            amount_given = Decimal(request.POST.get('amount_given', '0'))
            if amount_given < total:
                error = f'Not enough money! Need at least ${total:.2f}'
            else:
                change = amount_given - total

                # Save the transaction
                transaction = Transaction.objects.create(
                    total=total,
                    amount_given=amount_given,
                    change=change,
                )
                for item_id, qty in cart.items():
                    try:
                        item = Item.objects.get(pk=item_id)
                        TransactionItem.objects.create(
                            transaction=transaction,
                            item=item,
                            quantity=qty,
                            unit_price=item.price,
                        )
                    except Item.DoesNotExist:
                        pass

                # Clear the cart and record this transaction as accessible in this session
                request.session['cart'] = {}
                completed = request.session.get('completed_transactions', [])
                completed.append(transaction.pk)
                request.session['completed_transactions'] = completed
                request.session.modified = True

                return redirect('change', pk=transaction.pk)
        except (InvalidOperation, ValueError):
            error = 'Please enter a valid amount.'

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'error': error,
    })


def change(request, pk):
    """Show the change due to the customer."""
    if pk not in request.session.get('completed_transactions', []):
        return redirect('pos')
    try:
        transaction = Transaction.objects.prefetch_related('items__item').get(pk=pk)
    except Transaction.DoesNotExist:
        return redirect('pos')

    return render(request, 'store/change.html', {'transaction': transaction})
