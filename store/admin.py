from django.contrib import admin
from .models import Item, Transaction, TransactionItem


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'thumbnail_type', 'emoji', 'is_available')
    list_filter = ('thumbnail_type', 'is_available')
    search_fields = ('name',)
    list_editable = ('price', 'is_available')


class TransactionItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 0
    readonly_fields = ('unit_price', 'subtotal')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'total', 'amount_given', 'change', 'created_at')
    readonly_fields = ('total', 'amount_given', 'change', 'created_at')
    inlines = [TransactionItemInline]
