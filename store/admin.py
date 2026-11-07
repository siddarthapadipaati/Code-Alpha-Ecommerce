from django.contrib import admin
from .models import Product, Order, OrderItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'category',
        'price',
        'stock'
    )

    list_filter = ('category',)

    search_fields = ('name',)


admin.site.register(Order)
admin.site.register(OrderItem)