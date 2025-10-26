from django.contrib import admin
from django.utils.html import format_html

# Register your models here.
from .models import Jewelry, Cart, CartItem, Order, OrderItem

@admin.register(Jewelry)
class JewelryAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_at', 'image_preview')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    list_editable = ('price',)
    readonly_fields = ('created_at', 'image_preview')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image.url)
        return 'No Image'
    image_preview.short_description = 'Image'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'created_at', 'updated_at', 'total_price')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'session_key')
    readonly_fields = ('created_at', 'updated_at', 'total_price')
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('cartitem_set__jewelry')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'jewelry', 'quantity', 'total_price')
    list_filter = ('cart',)
    search_fields = ('jewelry__name',)
    list_editable = ('quantity',)
    readonly_fields = ('total_price',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('jewelry', 'quantity', 'price', 'total_price')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'email', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'full_name', 'email', 'square_payment_id')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'square_payment_id')
    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'total_amount', 'square_payment_id', 'created_at', 'updated_at')
        }),
        ('Buyer Information', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('shipping_street', 'shipping_city', 'shipping_state', 'shipping_zip', 'shipping_country')
        }),
        ('Billing Address', {
            'fields': ('billing_street', 'billing_city', 'billing_state', 'billing_zip', 'billing_country')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items__jewelry')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'jewelry', 'quantity', 'price', 'total_price')
    list_filter = ('order',)
    search_fields = ('jewelry__name', 'order__id')
    readonly_fields = ('total_price',)
