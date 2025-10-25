from django.contrib import admin
from django.utils.html import format_html

# Register your models here.
from .models import Jewelry, Cart, CartItem

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
