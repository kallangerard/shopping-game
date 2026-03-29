from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from .models import Item, Transaction, TransactionItem


class ItemModelTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(
            name='Apple',
            price=Decimal('0.50'),
            thumbnail_type=Item.THUMBNAIL_EMOJI,
            emoji='🍎',
        )

    def test_str(self):
        self.assertIn('Apple', str(self.item))

    def test_thumbnail_display_emoji(self):
        kind, val = self.item.thumbnail_display
        self.assertEqual(kind, 'emoji')
        self.assertEqual(val, '🍎')

    def test_thumbnail_display_fallback(self):
        self.item.emoji = ''
        kind, val = self.item.thumbnail_display
        self.assertEqual(kind, 'emoji')
        self.assertEqual(val, '🛒')


class TransactionModelTest(TestCase):
    def test_calculate_change(self):
        tx = Transaction(
            total=Decimal('15.00'),
            amount_given=Decimal('20.00'),
        )
        change = tx.calculate_change()
        self.assertEqual(change, Decimal('5.00'))

    def test_calculate_change_exact(self):
        tx = Transaction(
            total=Decimal('10.00'),
            amount_given=Decimal('10.00'),
        )
        self.assertEqual(tx.calculate_change(), Decimal('0.00'))


class POSViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.apple = Item.objects.create(
            name='Apple', price=Decimal('1.00'), emoji='🍎',
        )
        self.milk = Item.objects.create(
            name='Milk', price=Decimal('2.50'), emoji='🥛',
        )

    def test_pos_page_loads(self):
        response = self.client.get(reverse('pos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apple')
        self.assertContains(response, 'Milk')

    def test_add_to_cart(self):
        response = self.client.post(
            reverse('add_to_cart', args=[self.apple.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['item_qty'], 1)
        self.assertEqual(data['cart_count'], 1)

    def test_add_to_cart_twice(self):
        self.client.post(reverse('add_to_cart', args=[self.apple.pk]))
        response = self.client.post(reverse('add_to_cart', args=[self.apple.pk]))
        data = response.json()
        self.assertEqual(data['item_qty'], 2)
        self.assertEqual(data['cart_count'], 2)

    def test_remove_from_cart(self):
        self.client.post(reverse('add_to_cart', args=[self.apple.pk]))
        self.client.post(reverse('add_to_cart', args=[self.apple.pk]))
        response = self.client.post(reverse('remove_from_cart', args=[self.apple.pk]))
        data = response.json()
        self.assertEqual(data['item_qty'], 1)

    def test_remove_from_cart_to_zero(self):
        self.client.post(reverse('add_to_cart', args=[self.apple.pk]))
        response = self.client.post(reverse('remove_from_cart', args=[self.apple.pk]))
        data = response.json()
        self.assertEqual(data['item_qty'], 0)
        self.assertEqual(data['cart_count'], 0)

    def test_clear_cart_redirects(self):
        self.client.post(reverse('add_to_cart', args=[self.apple.pk]))
        response = self.client.post(reverse('clear_cart'))
        self.assertRedirects(response, reverse('pos'))

    def test_add_unavailable_item(self):
        self.apple.is_available = False
        self.apple.save()
        response = self.client.post(reverse('add_to_cart', args=[self.apple.pk]))
        self.assertEqual(response.status_code, 404)

    def test_checkout_empty_cart_redirects(self):
        response = self.client.get(reverse('checkout'))
        self.assertRedirects(response, reverse('pos'))


class CheckoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.item = Item.objects.create(
            name='Bread', price=Decimal('3.00'), emoji='🍞',
        )
        # Add item to cart via session
        self.client.post(reverse('add_to_cart', args=[self.item.pk]))
        self.client.post(reverse('add_to_cart', args=[self.item.pk]))  # qty=2 -> total=$6

    def test_checkout_page_shows_total(self):
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '6.00')

    def test_checkout_exact_payment(self):
        response = self.client.post(
            reverse('checkout'), {'amount_given': '6.00'}
        )
        tx = Transaction.objects.last()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.total, Decimal('6.00'))
        self.assertEqual(tx.change, Decimal('0.00'))
        self.assertRedirects(response, reverse('change', args=[tx.pk]))

    def test_checkout_overpayment(self):
        response = self.client.post(
            reverse('checkout'), {'amount_given': '10.00'}
        )
        tx = Transaction.objects.last()
        self.assertEqual(tx.change, Decimal('4.00'))
        self.assertRedirects(response, reverse('change', args=[tx.pk]))

    def test_checkout_underpayment_shows_error(self):
        response = self.client.post(
            reverse('checkout'), {'amount_given': '5.00'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Not enough money')

    def test_checkout_invalid_amount_shows_error(self):
        response = self.client.post(
            reverse('checkout'), {'amount_given': 'abc'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'valid amount')

    def test_cart_cleared_after_payment(self):
        self.client.post(reverse('checkout'), {'amount_given': '10.00'})
        session = self.client.session
        self.assertEqual(session.get('cart', {}), {})

    def test_session_records_last_transaction_after_payment(self):
        self.client.post(reverse('checkout'), {'amount_given': '10.00'})
        tx = Transaction.objects.last()
        session = self.client.session
        self.assertIn(tx.pk, session.get('completed_transactions', []))


class ChangeViewTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(
            name='Eggs', price=Decimal('4.50'), emoji='🥚',
        )
        self.tx = Transaction.objects.create(
            total=Decimal('4.50'),
            amount_given=Decimal('5.00'),
            change=Decimal('0.50'),
        )
        TransactionItem.objects.create(
            transaction=self.tx,
            item=self.item,
            quantity=1,
            unit_price=Decimal('4.50'),
        )

    def _set_last_transaction(self, pk):
        """Helper to seed the session as if a checkout completed for the given PK."""
        session = self.client.session
        session['completed_transactions'] = [pk]
        session.save()

    def test_change_page_loads(self):
        self._set_last_transaction(self.tx.pk)
        response = self.client.get(reverse('change', args=[self.tx.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '0.50')

    def test_change_page_shows_items(self):
        self._set_last_transaction(self.tx.pk)
        response = self.client.get(reverse('change', args=[self.tx.pk]))
        self.assertContains(response, 'Eggs')

    def test_change_authorized_missing_pk_redirects(self):
        """Session has authorization for PK 9999 but the transaction doesn't exist in DB."""
        self._set_last_transaction(9999)
        response = self.client.get(reverse('change', args=[9999]))
        self.assertRedirects(response, reverse('pos'))

    def test_change_page_unauthorized_redirects(self):
        """Accessing another session's transaction (IDOR) is blocked."""
        # No completed_transactions in session — should redirect to pos
        response = self.client.get(reverse('change', args=[self.tx.pk]))
        self.assertRedirects(response, reverse('pos'))
