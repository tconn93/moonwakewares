from django.contrib import admin
from django.utils.html import format_html

# Register your models here.
from .models import (
    Jewelry, Cart, CartItem, Order, OrderItem,
    Category, VariationType, VariationOption, ProductVariation, UserProfile, Event
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone', 'shipping_city', 'billing_city', 'created_at')
    list_filter = ('created_at', 'shipping_state', 'billing_state')
    search_fields = ('user__username', 'user__email', 'full_name', 'phone')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('shipping_street', 'shipping_city', 'shipping_state', 'shipping_zip', 'shipping_country'),
            'classes': ('collapse',)
        }),
        ('Billing Address', {
            'fields': ('same_billing_shipping', 'billing_street', 'billing_city', 'billing_state', 'billing_zip', 'billing_country'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(VariationType)
class VariationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name')
    search_fields = ('name', 'display_name')

@admin.register(VariationOption)
class VariationOptionAdmin(admin.ModelAdmin):
    list_display = ('variation_type', 'value', 'display_value', 'color_hex')
    list_filter = ('variation_type',)
    search_fields = ('value', 'display_value')

@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = ('jewelry', 'get_variation_options', 'total_price', 'stock_quantity', 'is_available')
    list_filter = ('jewelry', 'is_available')
    search_fields = ('jewelry__name', 'sku')
    list_editable = ('stock_quantity', 'is_available')
    readonly_fields = ('created_at', 'total_price')

    def get_variation_options(self, obj):
        return ", ".join([str(option) for option in obj.variation_options.all()])
    get_variation_options.short_description = 'Variation Options'

@admin.register(Jewelry)
class JewelryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity', 'is_active', 'has_variations', 'created_at', 'image_preview')
    list_filter = ('category', 'is_active', 'created_at', 'variation_types')
    search_fields = ('name', 'description', 'sku')
    list_editable = ('price', 'stock_quantity', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'image_preview', 'has_variations')
    filter_horizontal = ('variation_types',)
    
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
    list_display = ('cart', 'jewelry', 'product_variation', 'quantity', 'unit_price', 'total_price')
    list_filter = ('cart', 'jewelry')
    search_fields = ('jewelry__name', 'product_variation__sku')
    list_editable = ('quantity',)
    readonly_fields = ('unit_price', 'total_price')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('jewelry', 'product_variation', 'quantity', 'price', 'get_total_price', 'variation_data')
    can_delete = False

    def get_total_price(self, obj):
        """Safe total price display that handles None prices"""
        if obj and obj.pk:
            return f"${obj.total_price}"
        return "-"
    get_total_price.short_description = 'Total Price'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'email', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'full_name', 'email', 'square_payment_id')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'square_payment_id')
    inlines = [OrderItemInline]
    actions = ['mark_as_shipped']

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

    @admin.action(description='Mark selected orders as shipped')
    def mark_as_shipped(self, request, queryset):
        """Admin action to mark orders as shipped"""
        updated_count = queryset.update(status='shipped')
        self.message_user(
            request,
            f'{updated_count} order(s) successfully marked as shipped.',
            level='success'
        )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'jewelry', 'product_variation', 'quantity', 'price', 'get_total_price')
    list_filter = ('order', 'jewelry')
    search_fields = ('jewelry__name', 'product_variation__sku', 'order__id')
    readonly_fields = ('get_total_price', 'variation_data')

    def get_total_price(self, obj):
        """Safe total price display that handles None prices"""
        if obj and obj.price is not None:
            return f"${obj.total_price}"
        return "-"
    get_total_price.short_description = 'Total Price'

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'location', 'is_active', 'is_upcoming', 'max_attendees', 'image_preview')
    list_filter = ('is_active', 'date')
    search_fields = ('title', 'description', 'location')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at', 'image_preview')

    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'description', 'date', 'location', 'image', 'is_active')
        }),
        ('Capacity', {
            'fields': ('max_attendees',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image.url)
        return 'No Image'
    image_preview.short_description = 'Image'
